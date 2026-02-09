"""
scrapers.py

Scraping utilities for gauchoGPT housing data.

- One unified Listing dataclass
- One scraper function per website
- scrape_all_sources() to merge + write iv_housing_listings.csv

IMPORTANT:
    All CSS selectors inside individual scraper functions are PLACEHOLDERS.
    You MUST inspect each website in your browser dev tools and update them
    to match the real HTML structure.
"""

from __future__ import annotations

import time
import re
from dataclasses import dataclass, asdict
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd


# ---------------------------
# Config / constants
# ---------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; gauchoGPT/1.0; "
        "+https://github.com/your-username/gauchoGPT)"
    )
}

REQUEST_TIMEOUT = 15  # seconds
POLITE_DELAY = 1.0    # seconds between pages


# ---------------------------
# Listing dataclass
# ---------------------------

@dataclass
class Listing:
    source: str
    street: Optional[str] = None
    unit: Optional[str] = None
    city: Optional[str] = None

    price: Optional[int] = None          # total monthly rent (int dollars)
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    max_residents: Optional[int] = None

    status: str = "available"            # "available" | "processing" | "leased" | "unknown"
    avail_start: Optional[str] = None
    avail_end: Optional[str] = None

    utilities: Optional[str] = None
    pet_policy: Optional[str] = None
    pet_friendly: bool = False

    listing_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Return a plain dict compatible with your CSV / Streamlit app."""
        d = asdict(self)
        # price_per_person is computed later in gauchoGPT.py
        d["price_per_person"] = None
        return d


# ---------------------------
# Helper: general cleaners
# ---------------------------

def clean_price(text: str) -> Optional[int]:
    """Extract integer monthly price from messy text like '$4,800/mo', '$800', 'From $1,200'."""
    if not text:
        return None
    nums = re.findall(r"\d+", text.replace(",", ""))
    if not nums:
        return None
    try:
        return int(nums[0])
    except ValueError:
        return None


def clean_bed_bath(text: str) -> (Optional[float], Optional[float]):
    """
    Parse something like '2 Bed / 1.5 Bath', 'Studio', '3BR 2BA'.

    Returns (bedrooms, bathrooms) as floats or None.
    """
    if not text:
        return None, None

    t = text.lower()

    # Studio handling
    if "studio" in t and "bed" not in t:
        beds = 0.0
    else:
        beds_match = re.search(r"(\d+(\.\d+)?)\s*(bed|br)", t)
        beds = float(beds_match.group(1)) if beds_match else None

    baths_match = re.search(r"(\d+(\.\d+)?)\s*(bath|ba)", t)
    baths = float(baths_match.group(1)) if baths_match else None

    return beds, baths


def normalize_status(raw: Optional[str]) -> str:
    """
    Map site-specific status to one of:
        'available', 'processing', 'leased', 'unknown'
    """
    if not raw:
        return "unknown"

    t = raw.strip().lower()
    if any(k in t for k in ["available", "now", "vacant"]):
        return "available"
    if any(k in t for k in ["pending", "waitlist", "processing", "applying"]):
        return "processing"
    if any(k in t for k in ["leased", "occupied", "not available", "unavailable"]):
        return "leased"
    return "unknown"


def looks_like_isla_vista(text: str) -> bool:
    """
    Heuristic: decide if an address / city string is Isla Vista.

    Prefer exact city if present. As a fallback, look for common IV street names.
    """
    if not text:
        return False

    t = text.lower()

    # Direct city hits
    if "isla vista" in t or "iv," in t:
        return True

    # Very rough heuristic by street names
    iv_streets = [
        "del playa", "dp", "sabado tarde", "trigo", "pasado", "picasso",
        "emeterio", "el greco", "cordova", "camino del sur", "camino pescadero",
        "el colegio", "sueno", "segovia", "abrego", "oceano"
    ]
    return any(s in t for s in iv_streets)


# ---------------------------
# Scraper: ivproperties.com
# ---------------------------

def scrape_ivproperties() -> List[Listing]:
    """
    Scrape listings from https://www.ivproperties.com/

    NOTE: All CSS selectors here are placeholders and must be updated
    after inspecting the real HTML with your browser devtools.
    """
    base_url = "https://www.ivproperties.com"
    listings: List[Listing] = []

    # Example: assume there is a main 'apartments' page possibly paginated:
    page = 1
    while True:
        url = f"{base_url}/apartments?page={page}"
        print(f"[ivproperties] Fetching {url}")
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            print(f"[ivproperties] Stopping on status {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # TODO: update selector for one listing "card"
        cards = soup.select(".property-card, .listing-card")
        if not cards:
            # If there are no cards, assume we ran out of pages
            if page > 1:
                break
            else:
                print("[ivproperties] No listing cards found on first page; update selectors.")
                break

        for card in cards:
            # TODO: Update selectors below
            address_el = card.select_one(".property-address, .address")
            price_el = card.select_one(".rent, .price")
            details_el = card.select_one(".beds-baths, .details")
            status_el = card.select_one(".status, .availability")

            link_el = card.select_one("a")
            href = link_el["href"] if link_el and link_el.has_attr("href") else None
            if href and not href.startswith("http"):
                href = base_url.rstrip("/") + "/" + href.lstrip("/")

            address_text = address_el.get_text(" ", strip=True) if address_el else ""
            price_text = price_el.get_text(" ", strip=True) if price_el else ""
            details_text = details_el.get_text(" ", strip=True) if details_el else ""
            status_text = status_el.get_text(" ", strip=True) if status_el else ""

            if address_text and not looks_like_isla_vista(address_text):
                # Skip Goleta / SB for now
                continue

            beds, baths = clean_bed_bath(details_text)
            price = clean_price(price_text)
            status = normalize_status(status_text)

            listing = Listing(
                source="ivproperties",
                street=address_text or None,
                unit=None,  # could be parsed from address if needed
                city="Isla Vista" if looks_like_isla_vista(address_text) else None,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                max_residents=None,
                status=status,
                avail_start=None,  # could be added if present
                avail_end=None,
                utilities=None,
                pet_policy=None,
                pet_friendly=False,
                listing_url=href,
            )
            listings.append(listing)

        page += 1
        time.sleep(POLITE_DELAY)

    return listings


# ---------------------------
# Scraper: kamap.net
# ---------------------------

def scrape_kamap() -> List[Listing]:
    """
    Scrape listings from https://www.kamap.net/

    CURRENTLY A SKELETON:
        - You must inspect the actual HTML and fill in selectors.
        - Filter to Isla Vista only using looks_like_isla_vista().
    """
    base_url = "https://www.kamap.net"
    listings: List[Listing] = []

    url = f"{base_url}/availability"  # TODO: update to the real listings page
    print(f"[kamap] Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        print(f"[kamap] failed with status {resp.status_code}")
        return listings

    soup = BeautifulSoup(resp.text, "html.parser")

    # TODO: update selector
    rows = soup.select(".property-row, .listing-row, tr")
    for row in rows:
        # TODO: update these to real selectors / <td> positions
        address_el = row.select_one(".address")
        price_el = row.select_one(".rent")
        beds_el = row.select_one(".beds")
        baths_el = row.select_one(".baths")
        status_el = row.select_one(".status")
        avail_el = row.select_one(".available-date")

        link_el = row.select_one("a")
        href = link_el["href"] if link_el and link_el.has_attr("href") else None
        if href and not href.startswith("http"):
            href = base_url.rstrip("/") + "/" + href.lstrip("/")

        address_text = address_el.get_text(" ", strip=True) if address_el else ""
        if not looks_like_isla_vista(address_text):
            continue

        price = clean_price(price_el.get_text(" ", strip=True) if price_el else "")
        beds = None
        baths = None
        if beds_el:
            try:
                beds = float(re.findall(r"\d+(\.\d+)?", beds_el.get_text())[0])
            except Exception:
                beds = None
        if baths_el:
            try:
                baths = float(re.findall(r"\d+(\.\d+)?", baths_el.get_text())[0])
            except Exception:
                baths = None

        status = normalize_status(status_el.get_text(" ", strip=True) if status_el else "")
        avail_start = avail_el.get_text(" ", strip=True) if avail_el else None

        listing = Listing(
            source="kamap",
            street=address_text or None,
            unit=None,
            city="Isla Vista",
            price=price,
            bedrooms=beds,
            bathrooms=baths,
            max_residents=None,
            status=status,
            avail_start=avail_start,
            avail_end=None,
            utilities=None,
            pet_policy=None,
            pet_friendly=False,
            listing_url=href,
        )
        listings.append(listing)

    return listings


# ---------------------------
# Scraper: solisislavista.com
# ---------------------------

def scrape_solis() -> List[Listing]:
    """
    Scrape floorplans / availability from https://solisislavista.com/

    This will likely treat each floorplan or unit as a listing for the
    single Solis building in Isla Vista.
    """
    base_url = "https://solisislavista.com"
    listings: List[Listing] = []

    url = f"{base_url}/floorplans"  # TODO: confirm URL
    print(f"[solis] Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        print(f"[solis] failed with status {resp.status_code}")
        return listings

    soup = BeautifulSoup(resp.text, "html.parser")

    # TODO: update selector to floorplan cards
    cards = soup.select(".fp-card, .floorplan, .availability-card")
    for card in cards:
        name_el = card.select_one(".name, .title")
        beds_el = card.select_one(".beds")
        baths_el = card.select_one(".baths")
        price_el = card.select_one(".price, .rent")
        status_el = card.select_one(".status, .availability")

        name = name_el.get_text(" ", strip=True) if name_el else "Solis Isla Vista"
        beds, baths = clean_bed_bath(
            " ".join([
                beds_el.get_text(" ", strip=True) if beds_el else "",
                baths_el.get_text(" ", strip=True) if baths_el else "",
            ])
        )
        price = clean_price(price_el.get_text(" ", strip=True) if price_el else "")
        status = normalize_status(status_el.get_text(" ", strip=True) if status_el else "")

        listing = Listing(
            source="solis",
            street="Solis Isla Vista",
            unit=name,
            city="Isla Vista",
            price=price,
            bedrooms=beds,
            bathrooms=baths,
            max_residents=None,
            status=status,
            avail_start=None,
            avail_end=None,
            utilities=None,
            pet_policy=None,
            pet_friendly=False,
            listing_url=base_url,
        )
        listings.append(listing)

    return listings


# ---------------------------
# Scraper: sierrapropsb.com
# ---------------------------

def scrape_sierra() -> List[Listing]:
    """
    Scrape rentals from https://sierrapropsb.com/

    Filter to Isla Vista properties only.
    """
    base_url = "https://sierrapropsb.com"
    listings: List[Listing] = []

    url = f"{base_url}/rentals"  # TODO: confirm URL
    print(f"[sierra] Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        print(f"[sierra] failed with status {resp.status_code}")
        return listings

    soup = BeautifulSoup(resp.text, "html.parser")

    # TODO: update selector for each rental card / row
    cards = soup.select(".rental, .property-card, .listing")
    for card in cards:
        address_el = card.select_one(".address, .title")
        city_el = card.select_one(".city")
        price_el = card.select_one(".price, .rent")
        beds_el = card.select_one(".beds")
        baths_el = card.select_one(".baths")
        status_el = card.select_one(".status")

        address_text = address_el.get_text(" ", strip=True) if address_el else ""
        city_text = city_el.get_text(" ", strip=True) if city_el else ""
        combined = f"{address_text} {city_text}"

        if not looks_like_isla_vista(combined):
            continue

        price = clean_price(price_el.get_text(" ", strip=True) if price_el else "")
        beds, baths = clean_bed_bath(
            " ".join([
                beds_el.get_text(" ", strip=True) if beds_el else "",
                baths_el.get_text(" ", strip=True) if baths_el else "",
            ])
        )
        status = normalize_status(status_el.get_text(" ", strip=True) if status_el else "")

        listing = Listing(
            source="sierra",
            street=address_text or None,
            unit=None,
            city="Isla Vista",
            price=price,
            bedrooms=beds,
            bathrooms=baths,
            max_residents=None,
            status=status,
            avail_start=None,
            avail_end=None,
            utilities=None,
            pet_policy=None,
            pet_friendly=False,
            listing_url=None,
        )
        listings.append(listing)

    return listings


# ---------------------------
# Scraper: rlwa.com
# ---------------------------

def scrape_rlwa() -> List[Listing]:
    """
    Scrape rentals from https://www.rlwa.com/

    Filter to Isla Vista properties only.
    """
    base_url = "https://www.rlwa.com"
    listings: List[Listing] = []

    url = f"{base_url}/rentals"  # TODO: confirm URL
    print(f"[rlwa] Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        print(f"[rlwa] failed with status {resp.status_code}")
        return listings

    soup = BeautifulSoup(resp.text, "html.parser")

    # TODO: update selector
    cards = soup.select(".rental, .property-card, .listing")
    for card in cards:
        address_el = card.select_one(".address, .title")
        price_el = card.select_one(".price, .rent")
        beds_el = card.select_one(".beds")
        baths_el = card.select_one(".baths")
        status_el = card.select_one(".status, .availability")

        address_text = address_el.get_text(" ", strip=True) if address_el else ""
        if not looks_like_isla_vista(address_text):
            continue

        price = clean_price(price_el.get_text(" ", strip=True) if price_el else "")
        beds, baths = clean_bed_bath(
            " ".join([
                beds_el.get_text(" ", strip=True) if beds_el else "",
                baths_el.get_text(" ", strip=True) if baths_el else "",
            ])
        )
        status = normalize_status(status_el.get_text(" ", strip=True) if status_el else "")

        listing = Listing(
            source="rlwa",
            street=address_text or None,
            unit=None,
            city="Isla Vista",
            price=price,
            bedrooms=beds,
            bathrooms=baths,
            max_residents=None,
            status=status,
            avail_start=None,
            avail_end=None,
            utilities=None,
            pet_policy=None,
            pet_friendly=False,
            listing_url=None,
        )
        listings.append(listing)

    return listings


# ---------------------------
# Scraper: iconapts.com
# ---------------------------

def scrape_icon() -> List[Listing]:
    """
    Scrape ICON Apartments from https://www.iconapts.com/

    Likely a single-building complex with multiple floorplans / units.
    """
    base_url = "https://www.iconapts.com"
    listings: List[Listing] = []

    url = f"{base_url}/floorplans"  # TODO: confirm URL
    print(f"[icon] Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        print(f"[icon] failed with status {resp.status_code}")
        return listings

    soup = BeautifulSoup(resp.text, "html.parser")

    # TODO: update selector
    cards = soup.select(".fp-card, .floorplan, .availability-card")
    for card in cards:
        name_el = card.select_one(".name, .title")
        beds_el = card.select_one(".beds")
        baths_el = card.select_one(".baths")
        price_el = card.select_one(".price, .rent")
        status_el = card.select_one(".status, .availability")

        name = name_el.get_text(" ", strip=True) if name_el else "ICON Apartments"
        beds, baths = clean_bed_bath(
            " ".join([
                beds_el.get_text(" ", strip=True) if beds_el else "",
                baths_el.get_text(" ", strip=True) if baths_el else "",
            ])
        )
        price = clean_price(price_el.get_text(" ", strip=True) if price_el else "")
        status = normalize_status(status_el.get_text(" ", strip=True) if status_el else "")

        listing = Listing(
            source="icon",
            street="ICON Apartments",
            unit=name,
            city="Isla Vista",
            price=price,
            bedrooms=beds,
            bathrooms=baths,
            max_residents=None,
            status=status,
            avail_start=None,
            avail_end=None,
            utilities=None,
            pet_policy=None,
            pet_friendly=False,
            listing_url=base_url,
        )
        listings.append(listing)

    return listings


# ---------------------------
# Orchestrator: scrape all and write CSV
# ---------------------------

def scrape_all_sources(save_csv: bool = True,
                       csv_path: str = "iv_housing_listings.csv") -> pd.DataFrame:
    """
    Run all scrapers, merge results, drop obvious duplicates, and
    optionally save to a CSV that your Streamlit app reads.
    """
    all_listings: List[Listing] = []

    for name, func in [
        ("ivproperties", scrape_ivproperties),
        ("kamap", scrape_kamap),
        ("solis", scrape_solis),
        ("sierra", scrape_sierra),
        ("rlwa", scrape_rlwa),
        ("icon", scrape_icon),
    ]:
        try:
            print(f"[scrapers] Running {name}...")
            sites = func()
            print(f"[scrapers]  → {len(sites)} listings from {name}")
            all_listings.extend(sites)
        except Exception as e:
            # Don't let one failing scraper kill the whole pipeline
            print(f"[scrapers] ERROR in {name}: {e}")

    if not all_listings:
        print("[scrapers] No listings scraped from any source.")
        return pd.DataFrame()

    df = pd.DataFrame([l.to_dict() for l in all_listings])

    # Very rough duplicate drop: same street + unit + source
    df = df.drop_duplicates(subset=["source", "street", "unit"], keep="first")

    if save_csv:
        df.to_csv(csv_path, index=False)
        print(f"[scrapers] Saved {len(df)} listings to {csv_path}")

    return df


# ---------------------------
# CLI entrypoint
# ---------------------------

if __name__ == "__main__":
    scrape_all_sources()
