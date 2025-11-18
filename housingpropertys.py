# housingproperties.py
# Helpers for scraping & cleaning Isla Vista listings from ivproperties.com

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import re

from bs4 import BeautifulSoup


@dataclass
class Listing:
    title: str
    address: str
    price: str
    beds: str
    baths: str
    link: str
    status: str = ""
    max_residents: Optional[int] = None
    pets: str = ""
    utilities: str = ""


def _to_int(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d+)", text.replace(",", ""))
    return int(m.group(1)) if m else None


def parse_isla_vista_properties(
    html: str,
    base_url: str = "https://www.ivproperties.com",
) -> List[Listing]:
    """
    Parse the Isla Vista properties page into a list of Listing objects.

    This is tailored to:
    https://www.ivproperties.com/properties/isla-vista-properties/
    """

    soup = BeautifulSoup(html, "html.parser")
    listings: List[Listing] = []

    # The structure of the page is:
    #   <h2> Street, Isla Vista, CA </h2>
    #   [image]
    #   <h3> Street - Unit X </h3>   (optional, some properties only have an <h2>)
    #   status
    #   $price/installment (optional)
    #   X bedrooms / Studio
    #   Y bathrooms
    #   Maximum N residents
    #   Included Utilities: ...
    #   Pet friendly / No pets
    #   "More details" link
    #
    # We'll treat each <h3> or <h2> with following details as one Listing.

    # Consider both h2 and h3 as "start of listing blocks"
    for header in soup.select("h2, h3"):
        header_text = header.get_text(" ", strip=True)
        if not header_text:
            continue

        # Skip global heading like "Pricing and availability..."
        if "Pricing and availability" in header_text:
            continue

        # Determine street/address: use the closest previous h2 as the street,
        # otherwise header itself if it's an h2-only property.
        if header.name == "h2":
            street_text = header_text
        else:
            prev_h2 = header.find_previous("h2")
            street_text = prev_h2.get_text(" ", strip=True) if prev_h2 else header_text

        address = street_text  # keep full string, e.g. "6522 Del Playa Drive, Isla Vista, CA"

        title = header_text

        # Try to grab link from the header or from a "More details" link
        link = ""
        a = header.find("a")
        if a and a.get("href"):
            link = a["href"]

        status = ""
        price_raw = ""
        beds_raw = ""
        baths_raw = ""
        max_res_raw = ""
        utilities_raw = ""
        pets_raw = ""

        # Walk through siblings until the next header (h2 or h3)
        for sib in header.find_next_siblings():
            if sib.name in ("h2", "h3"):
                break

            text = sib.get_text(" ", strip=True)
            if not text:
                continue

            lower = text.lower()

            if "bedroom" in lower or "studio" in lower:
                beds_raw = text
            elif "bathroom" in lower:
                baths_raw = text
            elif "maximum" in lower and "resident" in lower:
                max_res_raw = text
            elif "$" in text or "installment" in lower:
                price_raw = text
            elif text.startswith("Included Utilities"):
                utilities_raw = text
            elif "pet friendly" in lower or "no pets" in lower:
                pets_raw = text
            elif "more details" in lower:
                a2 = sib.find("a")
                if a2 and a2.get("href"):
                    link = a2["href"]
            else:
                # First unclassified line is usually the status (available / leased / processing)
                if not status:
                    status = text

        # If we didn't pick up any beds/baths, this probably isn't a real listing
        if not beds_raw and not baths_raw and not status:
            continue

        # Normalize link to absolute
        if link and not link.startswith("http"):
            link = base_url.rstrip("/") + "/" + link.lstrip("/")

        listing = Listing(
            title=title,
            address=address,
            price=price_raw,
            beds=beds_raw,
            baths=baths_raw,
            link=link,
            status=status,
            max_residents=_to_int(max_res_raw),
            pets=pets_raw,
            utilities=utilities_raw,
        )
        listings.append(listing)

    return listings
