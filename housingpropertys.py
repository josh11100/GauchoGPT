# housingproperties.py
# Parser + feature extractor for:
# https://www.ivproperties.com/properties/isla-vista-properties/

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import re

from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.ivproperties.com"


@dataclass
class Listing:
    street: str
    unit: Optional[str]
    status: str
    price: Optional[str]
    bedrooms: Optional[str]
    bathrooms: Optional[str]
    max_residents: Optional[int]
    utilities: Optional[str]
    pet_friendly: Optional[bool]
    link: str


def _looks_like_iv_address(text: str) -> bool:
    """Heuristic to skip random <h2> headings and only keep property blocks."""
    text = text.lower()
    if "isla vista" in text:
        return True
    # Some addresses on the page omit "Isla Vista" in the <h2> text
    for street in [
        "del playa", "el nido", "fortuna", "pasado", "picasso",
        "sabado tarde", "sueno", "trigo"
    ]:
        if street in text:
            return True
    return False


def parse_isla_vista_properties(html: str) -> List[Listing]:
    """
    Parse the Isla Vista properties page into a list of Listing objects.

    We assume each property block looks roughly like:
        <h2>6512 Del Playa Drive, Isla Vista, CA</h2>
        <img ...>
        <h3>6512 Del Playa Drive - Unit 1</h3>
        <p>Status line...</p>
        <p>$8,700/installment</p>
        <p>3 bedrooms</p>
        <p>2 bathrooms</p>
        <p>Maximum 6 residents</p>
        <p>Included Utilities: ...</p>
        <p>Pet friendly / No pets</p>
        <a>More details</a>
        ...
    """
    soup = BeautifulSoup(html, "html.parser")
    listings: List[Listing] = []

    # Iterate over all h2 headings that look like property addresses
    for h2 in soup.find_all("h2"):
        addr = h2.get_text(strip=True)
        if not _looks_like_iv_address(addr):
            continue

        # We walk siblings until the next h2 (next property)
        sib = h2.next_sibling

        current_unit_name: Optional[str] = None
        current_fields: dict = {}

        def flush_current():
            """Push the current unit into the listings list."""
            nonlocal current_unit_name, current_fields
            if not current_unit_name and not current_fields:
                return
            listings.append(
                Listing(
                    street=addr,
                    unit=current_unit_name,
                    status=current_fields.get("status", ""),
                    price=current_fields.get("price"),
                    bedrooms=current_fields.get("bedrooms"),
                    bathrooms=current_fields.get("bathrooms"),
                    max_residents=current_fields.get("max_residents"),
                    utilities=current_fields.get("utilities"),
                    pet_friendly=current_fields.get("pet_friendly"),
                    link=current_fields.get("link", ""),
                )
            )
            current_unit_name = None
            current_fields = {}

        while sib and not (isinstance(sib, Tag) and sib.name == "h2"):
            if isinstance(sib, Tag):
                # New unit header
                if sib.name == "h3":
                    flush_current()
                    current_unit_name = sib.get_text(strip=True)

                # Details lines (usually <p>, sometimes <div>/etc)
                elif sib.name in {"p", "div", "span", "li"}:
                    text = sib.get_text(strip=True)
                    lower = text.lower()
                    if not text:
                        pass
                    elif text.startswith("$"):
                        current_fields["price"] = text
                    elif ("available for" in lower
                          or "currently leased" in lower
                          or "processing applications" in lower):
                        current_fields["status"] = text
                    elif "bedroom" in lower or "studio" in lower:
                        current_fields["bedrooms"] = text
                    elif "bathroom" in lower:
                        current_fields["bathrooms"] = text
                    elif "maximum" in lower and "resident" in lower:
                        m = re.search(r"(\d+)", text)
                        if m:
                            current_fields["max_residents"] = int(m.group(1))
                    elif lower.startswith("included utilities"):
                        current_fields["utilities"] = text
                    elif "pet friendly" in lower:
                        current_fields["pet_friendly"] = True
                    elif "no pets" in lower:
                        current_fields["pet_friendly"] = False

                # "More details" / "Apply" links
                if sib.name == "a":
                    href = sib.get("href") or ""
                    if href and not href.startswith("http"):
                        href = BASE_URL + href
                    if href:
                        current_fields.setdefault("link", href)

            sib = sib.next_sibling

        # Flush the last unit (or single-unit property without <h3>)
        flush_current()

    return listings
