# housingpropertys.py
# ------------------------------------------------------------
# Scraper + data cleaning for IV Properties (Isla Vista).
# Returns a cleaned pandas DataFrame you can use for analysis
# or plug into the gauchoGPT Streamlit app.
# ------------------------------------------------------------

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0 Safari/537.36"
)

DEFAULT_IV_ISLA_VISTA_URL = (
    "https://www.ivproperties.com/properties/isla-vista-properties/"
)


def _fetch_html(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch raw HTML from a URL, returning None on error."""
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None


def _text(node) -> str:
    if not node:
        return ""
    return node.get_text(" ", strip=True)


def _parse_iv_cards(html: str) -> List[Dict[str, Any]]:
    """
    Parse IVProperties listing cards into raw fields:
    Title, Address, Price, Beds, Baths, Meta, Status, Link.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards: List[Dict[str, Any]] = []

    # Try several possible card selectors (site might change)
    selectors = [
        "div.listing",
        "article.property-card",
        "div.property-card",
        "li.property",
        "div.property",
    ]

    for sel in selectors:
        nodes = soup.select(sel)
        if not nodes:
            continue

        for node in nodes:
            title = _text(
                node.select_one(".title")
                or node.select_one("h2")
                or node.select_one("h3")
            )
            address = _text(node.select_one(".address"))
            price = _text(node.select_one(".price, .rent, .amount"))
            beds = _text(node.select_one(".beds, .bedrooms"))
            baths = _text(node.select_one(".baths, .bathrooms"))
            status = _text(node.select_one(".status, .availability"))
            meta = _text(
                node.select_one(".details, .meta, .description, .body")
            )

            link_el = node.select_one("a")
            link = ""
            if link_el and link_el.has_attr("href"):
                link = link_el["href"]

            cards.append(
                {
                    "Title": title,
                    "Address": address,
                    "Price": price,
                    "Beds": beds,
                    "Baths": baths,
                    "Status": status,
                    "Meta": meta,
                    "Link": link,
                }
            )

        # If we found cards with this selector, don't keep trying others
        if cards:
            break

    return cards


def _first_float(text: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)", text or "")
    return float(m.group(1)) if m else None


def _first_int(text: str) -> Optional[int]:
    m = re.search(r"(\d+)", text or "")
    return int(m.group(1)) if m else None


def _clean_listing(row: Dict[str, Any]) -> Dict[str, Any]:
    """Add cleaned numeric / categorical features to a raw listing row."""
    price_text = row.get("Price", "") or ""
    beds_text = row.get("Beds", "") or ""
    baths_text = row.get("Baths", "") or ""
    meta_text = (row.get("Meta", "") or "") + " " + (row.get("Status", "") or "")
    title_text = row.get("Title", "") or ""

    # Price as integer + price type (e.g. 'installment')
    price_int = None
    m = re.search(r"([\d,]+)", price_text)
    if m:
        try:
            price_int = int(m.group(1).replace(",", ""))
        except Exception:
            price_int = None

    price_type = None
    if "installment" in price_text.lower():
        price_type = "installment"
    elif "per month" in price_text.lower() or "/month" in price_text.lower():
        price_type = "month"

    # Bedrooms: try numeric, but treat 'studio' specially
    bedrooms = _first_float(beds_text)
    if bedrooms is None and "studio" in (beds_text + " " + title_text).lower():
        bedrooms = 0.0

    # Bathrooms numeric
    bathrooms = _first_float(baths_text)

    # Max residents (if mentioned)
    max_residents = None
    if "resident" in meta_text.lower():
        max_residents = _first_int(meta_text)

    # Pet friendliness
    low_meta = meta_text.lower()
    pet_friendly: Optional[bool] = None
    if "no pets" in low_meta or "no animals" in low_meta:
        pet_friendly = False
    elif "pet friendly" in low_meta or "pets ok" in low_meta:
        pet_friendly = True

    # Utilities included
    utilities_included: Optional[bool] = None
    if "utilities included" in low_meta or "all utilities paid" in low_meta:
        utilities_included = True
    elif "tenant pays utilities" in low_meta:
        utilities_included = False

    row["price_int"] = price_int
    row["price_type"] = price_type
    row["bedrooms"] = bedrooms
    row["bathrooms"] = bathrooms
    row["max_residents"] = max_residents
    row["pet_friendly"] = pet_friendly
    row["utilities_included"] = utilities_included

    # Normalize status field: if empty, fall back to Meta snippet
    if not row.get("Status"):
        row["Status"] = row.get("Meta", "")

    return row


def _normalize_link(link: str) -> str:
    if not link:
        return ""
    if link.startswith("http://") or link.startswith("https://"):
        return link
    return "https://www.ivproperties.com" + link


def scrape_iv_dataframe(url: str | None = None) -> pd.DataFrame:
    """
    Scrape IV Properties for a given URL and return a cleaned DataFrame.

    Columns include:
    - Title, Address, Price, Beds, Baths, Status, Meta, Link
    - price_int, price_type, bedrooms, bathrooms, max_residents,
      pet_friendly, utilities_included
    """
    if url is None:
        url = DEFAULT_IV_ISLA_VISTA_URL

    html = _fetch_html(url)
    if not html:
        return pd.DataFrame()

    raw_cards = _parse_iv_cards(html)
    cleaned_rows = [_clean_listing(dict(row)) for row in raw_cards]

    df = pd.DataFrame(cleaned_rows)
    if not df.empty:
        if "Link" in df.columns:
            df["Link"] = df["Link"].fillna("").map(_normalize_link)
    return df
