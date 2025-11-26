# housingproperties.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import re

from bs4 import BeautifulSoup


@dataclass
class Listing:
    """Structured representation of one housing listing."""
    title: str
    address: str
    price: str
    beds: str
    baths: str
    link: str
    max_residents: Optional[int] = None
    status: str = ""


def _first_text_matching(chunks, *needles) -> Optional[str]:
    """Return first text chunk that contains any of the needles."""
    for txt in chunks:
        lower = txt.lower()
        if any(n in lower for n in needles):
            return txt
    return None


def _extract_max_residents(chunks) -> Optional[int]:
    # Look for "Maximum 6 residents" style text
    for txt in chunks:
        if "resident" in txt.lower():
            m = re.search(r"(\d+)", txt)
            if m:
                return int(m.group(1))
    return None


def _extract_status(chunks) -> str:
    # Look for availability-style lines
    for txt in chunks:
        lower = txt.lower()
        if ("available" in lower
                or "leased through" in lower
                or "processing applications" in lower):
            return txt
    return ""


def parse_isla_vista_properties(html: str) -> List[Listing]:
    """
    Parse the Isla Vista properties page into a list of Listing objects.

    This is written to be fairly robust: it looks for any elements whose
    CSS class contains 'property' and then uses regex + text heuristics
    to pull out price, beds, baths, etc.
    """
    soup = BeautifulSoup(html, "html.parser")

    def is_property_card(tag):
        if tag.name not in ("div", "article", "li", "section"):
            return False
        classes = tag.get("class") or []
        return any("property" in c.lower() for c in classes)

    cards = soup.find_all(is_property_card)

    # Fallback: if nothing matched, try some generic selectors
    if not cards:
        selectors = [
            "div.listing",
            "article.property-card",
            "div.property-card",
            "li.property",
        ]
        for sel in selectors:
            nodes = soup.select(sel)
            if nodes:
                cards = nodes
                break

    listings: List[Listing] = []

    for node in cards:
        # text chunks inside the card
        chunks = [t.strip() for t in node.stripped_strings if t.strip()]

        if not chunks:
            continue

        # Title / address: usually in an h2/h3, else first chunk
        title_tag = node.find(["h2", "h3", "h4"])
        title = title_tag.get_text(strip=True) if title_tag else chunks[0]

        # Try to separate address from title if possible
        address = title
        if "," in title:
            # e.g. "6522 Del Playa Drive, Unit A"
            address = title

        # Price: first chunk with a $
        price = _first_text_matching(chunks, "$") or ""

        # Beds / baths
        beds = _first_text_matching(chunks, "bed", "bedroom") or ""
        baths = _first_text_matching(chunks, "bath", "bathroom") or ""

        # Max residents & status
        max_residents = _extract_max_residents(chunks)
        status = _extract_status(chunks)

        # Link (if there's an <a> inside)
        link_tag = node.find("a", href=True)
        link = link_tag["href"] if link_tag else ""

        listings.append(
            Listing(
                title=title,
                address=address,
                price=price,
                beds=beds,
                baths=baths,
                link=link,
                max_residents=max_residents,
                status=status,
            )
        )

    return listings
