# scrape_pstat_offerings.py
# ---------------------------------------------------------
# Scrape UCSBPlat PSTAT Winter 2026 offerings into SQLite
# ---------------------------------------------------------
import re
import sqlite3
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup

DB_PATH = "db.sq"  # your SQLite file


BASE_URL = "https://ucsbplat.com/curriculum/major/PSTAT"


def fetch_page(page: int) -> str:
    """Fetch HTML for a given UCSBPlat PSTAT page."""
    if page == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}?page={page}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text


def parse_offerings_from_html(html: str) -> List[Dict[str, Any]]:
    """
    Very heuristic parser that walks the text line-by-line and extracts
    blocks that look like:

        PSTAT 170
        75 / 75  Full
        ######  Introduction to Mathematical Finance
        [Image] Tomoyuki Ichiba  3.8
        M  W
        14:00 PM - 15:15 PM
        34.1% A

    Handles cases where some lines are missing (e.g., T B A, no time, etc.).
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")
    lines = [ln.strip() for ln in text.splitlines()]

    offerings: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)

    def is_course_line(line: str) -> bool:
        return line.startswith("PSTAT ") and len(line.split()) >= 2

    while i < n:
        line = lines[i]

        if not is_course_line(line):
            i += 1
            continue

        course_code = line  # e.g. "PSTAT 170"
        # normalize to "PSTAT 170"
        course_code = " ".join(course_code.split()[:2])

        # --- capacity / status ---
        j = i + 1
        while j < n and lines[j] == "":
            j += 1
        capacity_line = lines[j] if j < n else ""

        seats_taken = None
        seats_total = None
        status_text = None

        # e.g. "75 / 75  Full" or "0 / 5  Enrolled" or "0 / 0  Full"
        cap_match = re.search(r"(\d+)\s*/\s*(\d+)\s*(.*)", capacity_line)
        if cap_match:
            seats_taken = int(cap_match.group(1))
            seats_total = int(cap_match.group(2))
            status_text = cap_match.group(3).strip() or None

        # --- title line (###### …) ---
        j += 1
        while j < n and lines[j] == "":
            j += 1
        title = ""
        if j < n and lines[j].startswith("######"):
            # strip leading hashes
            title = lines[j].lstrip("#").strip()
            j += 1
        else:
            # no explicit title? leave blank
            title = ""

        # --- instructor / rating, days, time, %A ---
        instructor = None
        rating = None
        days = None
        time_str = None
        pct_a = None

        # First non-empty after title is usually instructor / rating / or T B A
        while j < n and lines[j] == "":
            j += 1
        if j < n:
            instr_line = lines[j]
            j += 1

            # Remove any leading "Image" noise
            instr_line_clean = re.sub(r"^Image", "", instr_line).strip()

            # Pattern: "Name  3.8" (rating at the end)
            m = re.search(r"(.+?)\s+([0-9.]+)$", instr_line_clean)
            if m:
                instructor = m.group(1).strip()
                try:
                    rating = float(m.group(2))
                except ValueError:
                    rating = None
            else:
                # Could be "Natido A" or "T B A" or nothing useful
                instructor = instr_line_clean or None

        # After that, we may see days, time, and/or %A in *any* combination
        while j < n:
            ln = lines[j]
            # stop if next course starts
            if is_course_line(ln):
                break
            if ln == "":
                j += 1
                continue

            # percent A
            if "% A" in ln or "%A" in ln:
                m_pct = re.search(r"([\d.]+)\s*%A?", ln.replace(" ", ""))
                # fallback: just extract first number
                if not m_pct:
                    m_pct = re.search(r"([\d.]+)", ln)
                if m_pct:
                    try:
                        pct_a = float(m_pct.group(1))
                    except ValueError:
                        pct_a = None

            # time line: contains AM/PM or "-"
            elif ("AM" in ln or "PM" in ln or "-" in ln) and not time_str:
                time_str = ln

            # days line: letters like M/T/W/R/F, very short
            elif all(ch in "MTWRF " for ch in ln) and len(ln) <= 12 and not days:
                days = " ".join(ln.split())

            j += 1

        offerings.append(
            {
                "course_code": course_code,
                "title": title,
                "seats_taken": seats_taken,
                "seats_total": seats_total,
                "status": status_text,
                "instructor": instructor,
                "rating": rating,
                "days": days,
                "time": time_str,
                "pct_a": pct_a,
                "quarter": "Winter",
                "year": "2026",
            }
        )

        i = j  # move to next block

    return offerings


def init_db(conn: sqlite3.Connection) -> None:
    """
    Create a separate table for PSTAT offerings scraped from UCSBPlat.
    This does NOT touch your existing tables.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pstat_offerings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            title TEXT NOT NULL,
            quarter TEXT,
            year TEXT,
            instructor TEXT,
            rating REAL,
            seats_taken INTEGER,
            seats_total INTEGER,
            status TEXT,
            days TEXT,
            time TEXT,
            pct_a REAL
        );
        """
    )
    conn.commit()


def upsert_offerings(conn: sqlite3.Connection, offerings: List[Dict[str, Any]]) -> None:
    """
    Wipe existing Winter 2026 PSTAT offerings and insert fresh data.
    """
    conn.execute(
        "DELETE FROM pstat_offerings WHERE quarter = ? AND year = ?",
        ("Winter", "2026"),
    )

    conn.executemany(
        """
        INSERT INTO pstat_offerings (
            course_code, title, quarter, year,
            instructor, rating,
            seats_taken, seats_total,
            status, days, time, pct_a
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                o["course_code"],
                o["title"],
                o["quarter"],
                o["year"],
                o["instructor"],
                o["rating"],
                o["seats_taken"],
                o["seats_total"],
                o["status"],
                o["days"],
                o["time"],
                o["pct_a"],
            )
            for o in offerings
        ],
    )
    conn.commit()


def main():
    # 1) scrape all pages for Winter 2026 PSTAT
    all_offerings: List[Dict[str, Any]] = []
    for page in (1, 2, 3):
        html = fetch_page(page)
        page_offerings = parse_offerings_from_html(html)
        all_offerings.extend(page_offerings)

    print(f"Parsed {len(all_offerings)} PSTAT offerings.")

    # 2) write to SQLite
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        upsert_offerings(conn, all_offerings)
    finally:
        conn.close()

    print(f"Saved data into {DB_PATH} in table pstat_offerings.")


if __name__ == "__main__":
    main()
