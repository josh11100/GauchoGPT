# housing_page.py
from __future__ import annotations

from typing import Optional, Callable
import os
import re

import pandas as pd
import streamlit as st

from housingproperties import Listing
from ui_components import housing_header_html, housing_summary_html, housing_listing_card_html


def _status_class_and_text(status: str) -> tuple[str, str]:
    s = (status or "").lower().strip()
    if "available" in s:
        return "status-ok", status or "Available"
    if "processing" in s:
        return "status-warn", status or "Processing applications"
    if "leased" in s:
        return "status-muted", status or "Leased"
    return "status-muted", status or "Status unknown"


def listings_to_df(listings: list[Listing]) -> pd.DataFrame:
    rows = []
    for L in listings:
        rows.append(
            {
                "street": (L.address or L.title or "").strip(),
                "unit": "",  # optional: parse later if you want
                "status_raw": L.status or "",
                "status": (L.status or "").lower().strip(),
                "price": L.price_value,
                "bedrooms": L.beds_value,
                "bathrooms": L.baths_value,
                "max_residents": L.max_residents,
                "pet_policy": "Pet friendly",  # placeholder unless you scrape it
                "pet_friendly": None,          # placeholder
                "utilities": "",               # placeholder unless you scrape it
                "image_url": "",               # placeholder unless you scrape it
                "listing_url": L.link or "",
                "is_studio": bool(L.beds_value == 0) if L.beds_value is not None else False,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------
# CSV support (iv_housing_listings.csv)
# ---------------------------

@st.cache_data
def load_listings_csv(path: str = "iv_housing_listings.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def _to_num(x):
    """
    Convert '$2,400', '2400', 'starting_1800', '2,400/mo', etc -> float or NaN.
    """
    if pd.isna(x):
        return float("nan")
    s = str(x).strip().lower()
    m = re.search(r"(\d[\d,]*)", s)
    if not m:
        return float("nan")
    return float(m.group(1).replace(",", ""))


def normalize_csv_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps a listings CSV into the column schema your UI expects.
    If your CSV headers differ, adjust mappings here.
    """
    out = pd.DataFrame()

    # street/address/title
    if "street" in df.columns:
        out["street"] = df["street"]
    elif "address" in df.columns:
        out["street"] = df["address"]
    elif "title" in df.columns:
        out["street"] = df["title"]
    else:
        out["street"] = ""

    # unit
    out["unit"] = df["unit"] if "unit" in df.columns else ""

    # status
    if "status_raw" in df.columns:
        out["status_raw"] = df["status_raw"]
        out["status"] = df["status_raw"].astype(str).str.lower().str.strip()
    elif "status" in df.columns:
        out["status_raw"] = df["status"]
        out["status"] = df["status"].astype(str).str.lower().str.strip()
    else:
        out["status_raw"] = ""
        out["status"] = ""

    # price
    if "price" in df.columns:
        out["price"] = df["price"].apply(_to_num)
    elif "rent" in df.columns:
        out["price"] = df["rent"].apply(_to_num)
    else:
        out["price"] = float("nan")

    # bedrooms/bathrooms
    if "bedrooms" in df.columns:
        out["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    elif "beds" in df.columns:
        out["bedrooms"] = pd.to_numeric(df["beds"], errors="coerce")
    else:
        out["bedrooms"] = float("nan")

    if "bathrooms" in df.columns:
        out["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    elif "baths" in df.columns:
        out["bathrooms"] = pd.to_numeric(df["baths"], errors="coerce")
    else:
        out["bathrooms"] = float("nan")

    # max residents
    if "max_residents" in df.columns:
        out["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")
    elif "max_occupancy" in df.columns:
        out["max_residents"] = pd.to_numeric(df["max_occupancy"], errors="coerce")
    else:
        out["max_residents"] = float("nan")

    # pet fields
    out["pet_policy"] = df["pet_policy"] if "pet_policy" in df.columns else "Pet friendly"
    if "pet_friendly" in df.columns:
        out["pet_friendly"] = df["pet_friendly"]
    else:
        out["pet_friendly"] = None

    # utilities / image / url
    out["utilities"] = df["utilities"] if "utilities" in df.columns else ""
    out["image_url"] = df["image_url"] if "image_url" in df.columns else ""
    if "listing_url" in df.columns:
        out["listing_url"] = df["listing_url"]
    elif "details_url" in df.columns:
        out["listing_url"] = df["details_url"]
    elif "url" in df.columns:
        out["listing_url"] = df["url"]
    else:
        out["listing_url"] = ""

    # derived
    out["is_studio"] = out["bedrooms"].fillna(-1).astype(float) == 0

    # normalize strings
    for col in ["street", "unit", "status_raw", "pet_policy", "utilities", "image_url", "listing_url"]:
        if col in out.columns:
            out[col] = out[col].fillna("").astype(str)

    return out


def _render_housing_from_df(
    *,
    df: pd.DataFrame,
    render_html: Callable[[str], None],
    fallback_listing_uri: Optional[str] = None,
    remote_fallback_url: Optional[str] = None,
):
    if df.empty:
        st.warning("No listings found.")
        return

    # Filters
    render_html('<div class="card">')
    c1, c2, c3, c4 = st.columns([2, 1.3, 1.3, 1.3])

    with c1:
        max_price_val = int(df["price"].max()) if df["price"].notna().any() else 10000
        min_price_val = int(df["price"].min()) if df["price"].notna().any() else 0
        price_limit = st.slider(
            "Max monthly installment",
            min_value=min_price_val,
            max_value=max_price_val,
            value=max_price_val,
            step=100,
        )

    with c2:
        bedroom_choice = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4", "5+"], index=0)

    with c3:
        status_choice = st.selectbox(
            "Status filter", ["Available only", "All statuses", "Processing only", "Leased only"], index=0
        )

    with c4:
        pet_choice = st.selectbox("Pet policy", ["Any", "Only pet-friendly", "No pets allowed"], index=0)

    render_html("</div>")

    filtered = df.copy()
    filtered = filtered[(filtered["price"].isna()) | (filtered["price"] <= price_limit)]

    if bedroom_choice == "Studio":
        filtered = filtered[filtered["is_studio"] == True]
    elif bedroom_choice == "5+":
        filtered = filtered[filtered["bedrooms"] >= 5]
    elif bedroom_choice not in ("Any", "Studio", "5+"):
        b = int(bedroom_choice)
        filtered = filtered[filtered["bedrooms"] == b]

    s = status_choice.lower()
    status_lower = filtered["status"].fillna("").astype(str)
    if s.startswith("available"):
        filtered = filtered[status_lower.str.contains("available", na=False)]
    elif s.startswith("processing"):
        filtered = filtered[status_lower.str.contains("processing", na=False)]
    elif s.startswith("leased"):
        filtered = filtered[status_lower.str.contains("leased", na=False)]

    if pet_choice == "Only pet-friendly":
        filtered = filtered[filtered["pet_friendly"] == True]
    elif pet_choice == "No pets allowed":
        filtered = filtered[filtered["pet_friendly"] == False]

    render_html(housing_summary_html(len(filtered), len(df), int(price_limit)))

    with st.expander("📊 View table of filtered units"):
        st.dataframe(filtered, use_container_width=True)

    # Cards
    for _, row in filtered.iterrows():
        street = (row.get("street") or "").strip()
        unit = (row.get("unit") or "").strip()

        price = row.get("price")
        bedrooms = row.get("bedrooms")
        bathrooms = row.get("bathrooms")
        max_res = row.get("max_residents")

        is_studio = bool(row.get("is_studio"))
        bed_label = "Studio" if is_studio else (f"{int(bedrooms)} bed" if pd.notna(bedrooms) else "? bed")

        if pd.notna(bathrooms):
            ba_label = f"{int(bathrooms)} bath" if float(bathrooms).is_integer() else f"{bathrooms} bath"
        else:
            ba_label = "? bath"

        residents_label = f"Up to {int(max_res)} residents" if pd.notna(max_res) else "Up to ? residents"
        pet_label = (row.get("pet_policy") or "").strip() or "Pet friendly"
        utilities = (row.get("utilities") or "").strip()

        status_raw = row.get("status_raw") or ""
        status_class, status_text = _status_class_and_text(status_raw)

        price_text = f"${int(price):,}/installment" if pd.notna(price) else "Price not listed"

        ppp_text = ""
        if pd.notna(price) and pd.notna(max_res) and int(max_res) > 0:
            ppp_text = f"≈ ${price / int(max_res):,.0f} per person"

        listing_url = (row.get("listing_url") or "").strip()
        link_chip = ""
        if listing_url:
            link_chip = (
                f'<a href="{listing_url}" target="_blank" style="text-decoration:none;">'
                f'<span class="pill pill-gold">View listing ↗</span></a>'
            )

        image_url = (row.get("image_url") or "").strip()
        if image_url:
            img_html = f'<img src="{image_url}" alt="Listing photo" />'
        elif fallback_listing_uri:
            img_html = f'<img src="{fallback_listing_uri}" alt="UCSB" />'
        elif remote_fallback_url:
            img_html = f'<img src="{remote_fallback_url}" alt="UCSB" />'
        else:
            img_html = ""

        render_html(
            housing_listing_card_html(
                street=street,
                unit=unit,
                bed_label=bed_label,
                ba_label=ba_label,
                residents_label=residents_label,
                pet_label=pet_label,
                status_text=status_text,
                status_class=status_class,
                price_text=price_text,
                ppp_text=ppp_text,
                utilities=utilities,
                img_html=img_html,
                link_chip=link_chip,
            )
        )


# ---------------------------
# Public entrypoints
# ---------------------------

def housing_page_from_listings(
    *,
    listings: list[Listing],
    render_html: Callable[[str], None],
    fallback_listing_uri: Optional[str] = None,
    remote_fallback_url: Optional[str] = None,
):
    render_html(housing_header_html())

    df = listings_to_df(listings)
    _render_housing_from_df(
        df=df,
        render_html=render_html,
        fallback_listing_uri=fallback_listing_uri,
        remote_fallback_url=remote_fallback_url,
    )


def housing_page_from_csv(
    *,
    csv_path: str = "iv_housing_listings.csv",
    render_html: Callable[[str], None],
    fallback_listing_uri: Optional[str] = None,
    remote_fallback_url: Optional[str] = None,
):
    render_html(housing_header_html())

    if not os.path.exists(csv_path):
        st.error(f"Couldn't find {csv_path}. Put it in your project root (or update the path).")
        return

    raw = load_listings_csv(csv_path)
    df = normalize_csv_df(raw)

    _render_housing_from_df(
        df=df,
        render_html=render_html,
        fallback_listing_uri=fallback_listing_uri,
        remote_fallback_url=remote_fallback_url,
    )
