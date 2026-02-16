from __future__ import annotations

import os
from typing import Optional, Callable
import pandas as pd
import streamlit as st


HOUSING_CSV = "iv_housing_listings.csv"


def _safe_str(x) -> str:
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)


def _load_housing_df() -> Optional[pd.DataFrame]:
    if not os.path.exists(HOUSING_CSV):
        st.error(f"Missing CSV file: {HOUSING_CSV}. Put it next to gauchoGPT.py.")
        return None

    df = pd.read_csv(HOUSING_CSV)

    expected = [
        "street", "unit", "avail_start", "avail_end",
        "price", "bedrooms", "bathrooms", "max_residents",
        "utilities", "pet_policy", "pet_friendly", "status",
        "image_url", "listing_url",
    ]
    for col in expected:
        if col not in df.columns:
            df[col] = None

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")

    df["pet_friendly"] = df["pet_friendly"].fillna(False).astype(bool)
    df["status"] = df["status"].fillna("available").astype(str).str.lower().str.strip()

    df["is_studio"] = df["bedrooms"].fillna(0).astype(float).eq(0)

    df["price_per_person"] = df.apply(
        lambda r: r["price"] / r["max_residents"]
        if pd.notnull(r["price"]) and pd.notnull(r["max_residents"]) and r["max_residents"] > 0
        else None,
        axis=1,
    )

    return df


def housing_page(
    *,
    render_html: Callable[[str], None],
    fallback_listing_uri: Optional[str],
    remote_fallback_url: Optional[str],
) -> None:
    render_html("""
<div class="card-soft">
  <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">🏠 Isla Vista Housing (CSV snapshot)</div>
  <div class="small-muted">
    Snapshot of selected Isla Vista units for the 2026–27 lease term. Filters below help you find fits by price, bedrooms,
    status, and pet policy.
  </div>
</div>
<div class="section-gap"></div>
""")

    df = _load_housing_df()
    if df is None or df.empty:
        st.warning("No housing data found in the CSV.")
        return

    # -------- Filters row (Streamlit widgets) --------
    render_html('<div class="card">')
    c1, c2, c3, c4 = st.columns([1.6, 1.1, 1.1, 1.1])

    with c1:
        max_price = int(df["price"].max()) if df["price"].notna().any() else 12000
        min_price = int(df["price"].min()) if df["price"].notna().any() else 0
        price_limit = st.slider("Max monthly installment", min_value=min_price, max_value=max_price, value=max_price, step=100)

    with c2:
        bedroom_choice = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4", "5+"], index=0)

    with c3:
        status_choice = st.selectbox("Status filter", ["Available only", "All statuses", "Processing only", "Leased only"], index=0)

    with c4:
        pet_choice = st.selectbox("Pet policy", ["Any", "Only pet-friendly", "No pets allowed"], index=0)

    render_html("</div>")

    # -------- Apply filters --------
    filtered = df.copy()
    filtered = filtered[(filtered["price"].isna()) | (filtered["price"] <= price_limit)]

    if bedroom_choice == "Studio":
        filtered = filtered[filtered["is_studio"] == True]
    elif bedroom_choice == "5+":
        filtered = filtered[filtered["bedrooms"] >= 5]
    elif bedroom_choice not in ("Any", "Studio", "5+"):
        try:
            b = int(bedroom_choice)
            filtered = filtered[filtered["bedrooms"] == b]
        except ValueError:
            pass

    s = status_choice.lower()
    status_lower = filtered["status"].fillna("").astype(str).str.lower().str.strip()
    if s.startswith("available"):
        filtered = filtered[status_lower == "available"]
    elif s.startswith("processing"):
        filtered = filtered[status_lower == "processing"]
    elif s.startswith("leased"):
        filtered = filtered[status_lower == "leased"]

    if pet_choice == "Only pet-friendly":
        filtered = filtered[filtered["pet_friendly"] == True]
    elif pet_choice == "No pets allowed":
        filtered = filtered[(filtered["pet_friendly"] == False) | (filtered["pet_policy"].fillna("").astype(str).str.contains("No pets", case=False))]

    # -------- Summary --------
    render_html(f"""
<div class="section-gap"></div>
<div class="card-soft">
  <div class="small-muted">
    Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> units • Price ≤
    <span class="pill pill-blue">${price_limit:,}</span>
  </div>
</div>
<div class="section-gap"></div>
""")

    if filtered.empty:
        st.info("No units match your filters. Try raising your max price or widening status/bedroom filters.")
        return

    with st.expander("📊 View table of filtered units"):
        st.dataframe(
            filtered[
                [
                    "street", "unit", "status",
                    "avail_start", "avail_end",
                    "price", "bedrooms", "bathrooms",
                    "max_residents", "pet_policy",
                    "utilities", "price_per_person",
                    "image_url", "listing_url",
                ]
            ],
            use_container_width=True,
        )

    # -------- Listing cards --------
    for _, row in filtered.sort_values(["street", "unit"], na_position="last").iterrows():
        street = _safe_str(row.get("street")).strip()
        unit = _safe_str(row.get("unit")).strip()
        status = _safe_str(row.get("status")).lower().strip()

        price = row.get("price")
        bedrooms = row.get("bedrooms")
        bathrooms = row.get("bathrooms")
        max_res = row.get("max_residents")
        utilities = _safe_str(row.get("utilities")).strip()
        pet_policy = _safe_str(row.get("pet_policy")).strip()
        pet_friendly = bool(row.get("pet_friendly", False))
        ppp = row.get("price_per_person")
        avail_start = _safe_str(row.get("avail_start")).strip()
        avail_end = _safe_str(row.get("avail_end")).strip()

        image_url = _safe_str(row.get("image_url")).strip()
        listing_url = _safe_str(row.get("listing_url")).strip()

        # Status styling
        if status == "available":
            date_part = f"{avail_start}–{avail_end}".strip("–")
            status_text = f"Available {date_part} (applications open)".strip()
            status_class = "status-ok"
        elif status == "processing":
            status_text = "Processing applications"
            status_class = "status-warn"
        elif status == "leased":
            status_text = f"Currently leased (through {avail_end})" if avail_end else "Currently leased"
            status_class = "status-muted"
        else:
            status_text = status.title() if status else "Status unknown"
            status_class = "status-muted"

        is_studio = pd.isna(bedrooms) or float(bedrooms) == 0
        bed_label = "Studio" if is_studio else f"{int(bedrooms) if pd.notna(bedrooms) else '?'} bed"

        if pd.notna(bathrooms):
            ba_label = f"{int(bathrooms)} bath" if float(bathrooms).is_integer() else f"{bathrooms} bath"
        else:
            ba_label = "? bath"

        residents_label = f"Up to {int(max_res)} residents" if pd.notna(max_res) else "Up to ? residents"
        pet_label = pet_policy or ("Pet friendly" if pet_friendly else "No pets info")

        price_text = f"${int(price):,}/installment" if pd.notna(price) else "Price not listed"
        ppp_text = f"≈ ${ppp:,.0f} per person" if ppp is not None else ""

        # Image
        img_html = ""
        if image_url:
            img_html = f'<img src="{image_url}" alt="Listing photo" />'
        elif fallback_listing_uri:
            img_html = f'<img src="{fallback_listing_uri}" alt="UCSB" />'
        elif remote_fallback_url:
            img_html = f'<img src="{remote_fallback_url}" alt="UCSB" />'

        link_chip = ""
        if listing_url:
            link_chip = (
                f'<a href="{listing_url}" target="_blank" style="text-decoration:none;">'
                f'<span class="pill pill-gold">View listing ↗</span></a>'
            )

        render_html(f"""
<div class="card">
  <div class="listing-wrap">
    <div class="thumb">{img_html}</div>

    <div>
      <div class="listing-title">{street}, Isla Vista, CA</div>
      <div class="listing-sub">{street} - {unit}</div>

      <div class="pills">
        <span class="pill">{bed_label}</span>
        <span class="pill">{ba_label}</span>
        <span class="pill">{residents_label}</span>
        <span class="pill pill-gold">{pet_label}</span>
        {link_chip}
      </div>

      <div style="margin-top:10px;">
        <div class="{status_class}">{status_text}</div>
        <div class="price-row">
          {price_text}
          <span class="small-muted" style="font-weight:750;">{(" · " + ppp_text) if ppp_text else ""}</span>
        </div>
        {f"<div class='small-muted' style='margin-top:6px;'>Included utilities: {utilities}</div>" if utilities else ""}
      </div>
    </div>
  </div>
</div>
<div class="section-gap"></div>
""")
