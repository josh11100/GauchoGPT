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

    # numeric helpers for UI/filtering
    price_value: Optional[float] = None
    beds_value: Optional[float] = None
    baths_value: Optional[float] = None


def _first_text_matching(chunks, *needles) -> Optional[str]:
    for txt in chunks:
        lower = txt.lower()
        if any(n in lower for n in needles):
            return txt
    return None


def _extract_max_residents(chunks) -> Optional[int]:
    for txt in chunks:
        if "resident" in txt.lower():
            m = re.search(r"(\d+)", txt)
            if m:
                return int(m.group(1))
    return None


def _extract_status(chunks) -> str:
    for txt in chunks:
        lower = txt.lower()
        if ("available" in lower) or ("leased" in lower) or ("processing" in lower):
            return txt
    return ""


def _num_from_text(s: str) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"(\d+(\.\d+)?)", s.replace(",", ""))
    return float(m.group(1)) if m else None


def _price_from_text(s: str) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"\$?\s*([\d,]+)", s)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def parse_isla_vista_properties(html: str) -> List[Listing]:
    """
    Parse the Isla Vista properties page into Listing objects.

    This is heuristic-based; you may tune selectors once you know ivproperties HTML structure.
    """
    soup = BeautifulSoup(html, "html.parser")

    def is_property_card(tag):
        if tag.name not in ("div", "article", "li", "section"):
            return False
        classes = tag.get("class") or []
        return any("property" in c.lower() for c in classes)

    cards = soup.find_all(is_property_card)

    # Fallback selectors
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
        chunks = [t.strip() for t in node.stripped_strings if t.strip()]
        if not chunks:
            continue

        title_tag = node.find(["h1", "h2", "h3", "h4"])
        title = title_tag.get_text(strip=True) if title_tag else chunks[0]
        address = title

        price_txt = _first_text_matching(chunks, "$") or ""
        beds_txt = _first_text_matching(chunks, "bed", "bedroom") or ""
        baths_txt = _first_text_matching(chunks, "bath", "bathroom") or ""

        max_residents = _extract_max_residents(chunks)
        status = _extract_status(chunks)

        link_tag = node.find("a", href=True)
        link = link_tag["href"] if link_tag else ""

        price_val = _price_from_text(price_txt)
        beds_val = _num_from_text(beds_txt)
        baths_val = _num_from_text(baths_txt)

        listings.append(
            Listing(
                title=title,
                address=address,
                price=price_txt,
                beds=beds_txt,
                baths=baths_txt,
                link=link,
                max_residents=max_residents,
                status=status,
                price_value=price_val,
                beds_value=beds_val,
                baths_value=baths_val,
            )
        )

    return listings
