# gauchoGPT — Streamlit “Premium UCSB” UI + Left Sidebar Hamburger Nav + Images (optional)
# --------------------------------------------------------------------------------------
from __future__ import annotations

import os
import base64
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
from urllib.parse import quote_plus

# 🔹 Import Academics tab from separate file
from academics import academics_page

# 🔹 Optional: Import scraper (for admin panel)
try:
    from ucsb_course_scraper import UCSBCourseScraper
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False


# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="gauchoGPT — UCSB helper",
    page_icon="🧢",
    layout="wide",
)


# ---------------------------
# Helpers: local image -> data URI
# ---------------------------
def img_to_data_uri(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        return None
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
    return f"data:image/{mime};base64,{b64}"


# Optional hero background (local file)
BG_URI = (
    img_to_data_uri("assets/ucsb_bg.jpg")
    or img_to_data_uri("assets/ucsb_bg.jpeg")
    or img_to_data_uri("assets/ucsb_bg.png")
    or img_to_data_uri("assets/ucsb_bg.webp")
)

# Optional fallback listing image (local file)
FALLBACK_LISTING_URI = (
    img_to_data_uri("assets/ucsb_fallback.jpg")
    or img_to_data_uri("assets/ucsb_fallback.jpeg")
    or img_to_data_uri("assets/ucsb_fallback.png")
    or img_to_data_uri("assets/ucsb_fallback.webp")
)

# Optional: You can set a remote fallback image URL instead (leave None to only use local)
REMOTE_FALLBACK_IMAGE_URL = None


# ---------------------------
# Session state defaults
# ---------------------------
NAV_LABELS = ["🏁 Home", "🏠 Housing", "📚 Academics", "👩‍🏫 Professors", "💸 Aid & Jobs", "💬 Q&A"]

if "main_nav" not in st.session_state:
    st.session_state["main_nav"] = "🏁 Home"

if "sidebar_nav_open" not in st.session_state:
    st.session_state["sidebar_nav_open"] = False


# ---------------------------
# Premium UCSB Style
# ---------------------------
UCSB_STYLE = f"""
<style>
:root{{
  --bg: #f6f7fb;
  --card: rgba(255,255,255,0.90);
  --card2: rgba(255,255,255,0.96);
  --text: #0f172a;
  --muted: #5b6475;
  --line: rgba(15,23,42,0.10);
  --shadow: 0 12px 35px rgba(2, 6, 23, 0.10);
  --shadow2: 0 6px 18px rgba(2, 6, 23, 0.08);
  --radius: 18px;

  --navy: #003660;
  --gold: #FDB515;
  --blue: #0a84ff;
  --blue2: #0071e3;

  --ok: #16a34a;
  --warn: #f59e0b;
  --bad: #ef4444;
}}

[data-testid="stAppViewContainer"]{{
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji",
               "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
}}

{f"""
/* HERO background image */
[data-testid="stAppViewContainer"]::before {{
  content: "";
  position: fixed;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(0,54,96,0.10) 0%, rgba(246,247,251,0.88) 40%, rgba(246,247,251,0.98) 100%),
    radial-gradient(900px 380px at 18% 10%, rgba(253,181,21,0.18), rgba(255,255,255,0.0)),
    url("{BG_URI}");
  background-size: cover;
  background-position: center;
  z-index: 0;
}}
""" if BG_URI else ""}

[data-testid="stAppViewContainer"] > .main {{
  position: relative;
  z-index: 1;
}}

.block-container{{
  padding-top: 5.1rem;   /* fixes top text blocked */
  max-width: 1480px;     /* less empty whitespace left/right */
}}

h1,h2,h3,h4{{ color: var(--text); letter-spacing: -0.02em; }}
h1{{ font-size: 2.35rem; font-weight: 900; }}
h2{{ font-size: 1.55rem; font-weight: 850; }}
h3{{ font-size: 1.15rem; font-weight: 800; }}

.small-muted{{ color: var(--muted); font-size: 0.93rem; line-height: 1.35; }}

/* Topbar */
.topbar{{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
  background: rgba(246,247,251,0.78);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
}}
.topbar-inner{{
  max-width: 1480px;
  margin: 0 auto;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.brand{{
  display:flex; align-items:center; gap:10px;
  font-weight: 900;
}}
.brand-dot{{
  width: 10px; height: 10px;
  background: var(--gold);
  border-radius: 999px;
  box-shadow: 0 0 0 5px rgba(253,181,21,0.18);
}}
.brand small{{ color: var(--muted); font-weight: 700; }}
.topbar-right{{
  color: var(--muted);
  font-weight: 700;
  font-size: 0.93rem;
}}

/* Cards */
.card{{
  background: var(--card2);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px 18px;
}}
.card-soft{{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow2);
  padding: 14px 16px;
}}
.section-gap{{ height: 14px; }}

/* Hero */
.hero{{
  background: linear-gradient(135deg, rgba(0,54,96,0.88), rgba(0,113,227,0.70));
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 22px;
  box-shadow: var(--shadow);
  padding: 22px 22px;
  color: white;
}}
.hero-title{{ font-size: 2.2rem; font-weight: 950; letter-spacing:-0.03em; }}
.hero-sub{{ opacity: 0.92; margin-top: 8px; font-weight: 650; }}

/* Pills */
.pills{{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
.pill{{
  display:inline-flex; align-items:center; gap:6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(2, 6, 23, 0.05);
  border: 1px solid rgba(2, 6, 23, 0.08);
  font-weight: 750;
  font-size: 0.90rem;
}}
.pill-gold{{
  background: rgba(253,181,21,0.18);
  border-color: rgba(253,181,21,0.30);
}}
.pill-blue{{
  background: rgba(10,132,255,0.14);
  border-color: rgba(10,132,255,0.28);
}}

/* Status */
.status-ok{{ color: var(--ok); font-weight: 900; }}
.status-warn{{ color: var(--warn); font-weight: 900; }}
.status-bad{{ color: var(--bad); font-weight: 900; }}
.status-muted{{ color: var(--muted); font-weight: 750; }}

/* Global buttons */
.stButton > button{{
  background: linear-gradient(135deg, var(--blue2), var(--blue));
  border: 1px solid rgba(255,255,255,0.12);
  color: white;
  border-radius: 999px;
  padding: 0.60rem 1.05rem;
  font-weight: 900;
  box-shadow: 0 10px 25px rgba(0,113,227,0.20);
}}
.stButton > button:hover{{
  filter: brightness(1.05);
}}

/* Inputs visibility */
[data-baseweb="select"] > div {{
  background: rgba(255,255,255,0.96) !important;
  border: 1px solid rgba(15,23,42,0.22) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 12px rgba(2,6,23,0.06) !important;
}}
div[data-testid="stSlider"] {{
  padding: 10px 12px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(15,23,42,0.16);
  border-radius: 14px;
}}

/* Sidebar */
[data-testid="stSidebar"]{{
  background: rgba(246,247,251,0.92);
  border-right: 1px solid var(--line);
}}
[data-testid="stSidebar"] .block-container{{ padding-top: 1.10rem; }}

/* Sidebar hamburger */
.sidebar-hamburger .stButton > button {{
  width: 46px !important;
  height: 46px !important;
  padding: 0 !important;
  border-radius: 999px !important;
  background: rgba(0,54,96,0.10) !important;
  color: var(--navy) !important;
  border: 1px solid rgba(0,54,96,0.18) !important;
  box-shadow: none !important;
  font-size: 18px !important;
}}
.sidebar-hamburger .stButton > button:hover {{
  background: rgba(0,54,96,0.14) !important;
}}

/* Sidebar nav buttons */
.sidebar-nav button {{
  width: 100%;
  background: rgba(0,54,96,0.06) !important;
  color: var(--navy) !important;
  border: 1px solid rgba(0,54,96,0.14) !important;
  border-radius: 14px !important;
  padding: 0.70rem 0.9rem !important;
  font-weight: 950 !important;
  text-align: left !important;
}}
.sidebar-nav button:hover {{
  background: rgba(0,54,96,0.10) !important;
}}
.sidebar-nav-active button {{
  background: rgba(253,181,21,0.24) !important;
  border-color: rgba(253,181,21,0.42) !important;
  color: #1f2937 !important;
}}

/* Housing listing card layout */
.listing-wrap{{
  display:grid;
  grid-template-columns: 210px 1fr;
  gap: 14px;
  align-items: stretch;
}}
@media (max-width: 900px) {{
  .listing-wrap{{ grid-template-columns: 1fr; }}
}}
.thumb{{
  width: 100%;
  height: 150px;
  border-radius: 16px;
  border: 1px solid rgba(2,6,23,0.10);
  overflow: hidden;
  background: rgba(0,0,0,0.04);
}}
.thumb img{{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}
.listing-title{{
  font-size: 1.25rem;
  font-weight: 950;
  letter-spacing:-0.02em;
}}
.listing-sub{{
  color: var(--muted);
  font-size: 0.92rem;
  margin-top: 3px;
}}
.price-row{{
  margin-top: 10px;
  font-weight: 950;
  font-size: 1.05rem;
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
"""
st.markdown(UCSB_STYLE, unsafe_allow_html=True)


# ---------------------------
# Topbar
# ---------------------------
st.markdown(
    """
    <div class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <span class="brand-dot"></span>
          <span>gauchoGPT</span>
          <small>UCSB Student Helper</small>
        </div>
        <div class="topbar-right">Home • Housing • Academics • Professors • Aid & Jobs • Q&A</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Sidebar: hamburger + nav + status/admin
# ---------------------------
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

st.sidebar.markdown('<div class="sidebar-hamburger">', unsafe_allow_html=True)
hamb_label = "☰" if not st.session_state["sidebar_nav_open"] else "✕"
if st.sidebar.button(hamb_label, key="sidebar_hamburger"):
    st.session_state["sidebar_nav_open"] = not st.session_state["sidebar_nav_open"]
    st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

if st.session_state["sidebar_nav_open"]:
    st.sidebar.divider()
    st.sidebar.markdown("### Navigation")
    for label in NAV_LABELS:
        is_active = (st.session_state["main_nav"] == label)
        cls = "sidebar-nav-active" if is_active else "sidebar-nav"
        st.sidebar.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.sidebar.button(label, key=f"side_nav_{label}"):
            st.session_state["main_nav"] = label
            st.session_state["sidebar_nav_open"] = False
            st.rerun()
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Data Status")

db_exists = os.path.exists("gauchoGPT.db")
csv_exists = os.path.exists("major_courses_by_quarter.csv")

if db_exists:
    st.sidebar.success("✅ Course database active")
elif csv_exists:
    st.sidebar.info("📄 Using CSV data")
else:
    st.sidebar.warning("⚠️ No course data found")

if HAS_SCRAPER:
    st.sidebar.divider()
    st.sidebar.markdown("### 🔧 Admin Tools")
    with st.sidebar.expander("Update course data"):
        st.caption("Scrape latest courses from UCSB")
        if st.sidebar.button("🔄 Run Scraper", use_container_width=True):
            with st.spinner("Scraping UCSB courses..."):
                try:
                    scraper = UCSBCourseScraper()
                    scraper.create_database_schema()
                    courses_df = scraper.scrape_all_departments()
                    if not courses_df.empty:
                        scraper.save_to_database(courses_df)
                        st.success(f"✅ Scraped {len(courses_df)} courses!")
                        st.rerun()
                    else:
                        st.error("No courses found. Check scraper configuration.")
                except Exception as e:
                    st.error(f"Scraper error: {e}")

st.sidebar.divider()
st.sidebar.markdown(
    """
**Next steps (quick)**
- Keep CSV updated
- Configure scraper selectors
- Connect LLM for Q&A
"""
)


# ---------------------------
# HOUSING — CSV-backed
# ---------------------------
HOUSING_CSV = "iv_housing_listings.csv"


def load_housing_df() -> Optional[pd.DataFrame]:
    if not os.path.exists(HOUSING_CSV):
        st.error(f"Missing CSV file: {HOUSING_CSV}. Place it next to gauchoGPT.py.")
        return None

    df = pd.read_csv(HOUSING_CSV)

    # expected columns (create if missing)
    for col in [
        "street", "unit", "avail_start", "avail_end",
        "price", "bedrooms", "bathrooms", "max_residents",
        "utilities", "pet_policy", "pet_friendly", "status",
        "image_url", "listing_url"
    ]:
        if col not in df.columns:
            df[col] = None

    if "status" not in df.columns or df["status"].isna().all():
        df["status"] = "available"

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")

    df["pet_friendly"] = df["pet_friendly"].fillna(False).astype(bool)
    df["is_studio"] = df["bedrooms"].fillna(0).astype(float).eq(0)

    df["price_per_person"] = df.apply(
        lambda r: r["price"] / r["max_residents"]
        if pd.notnull(r["price"]) and pd.notnull(r["max_residents"]) and r["max_residents"] > 0
        else None,
        axis=1,
    )
    return df


def home_page():
    st.markdown(
        """
        <div class="hero">
          <div class="hero-title">UCSB tools, in one place.</div>
          <div class="hero-sub">
            Find housing, plan classes, check professors, and navigate aid & jobs — built for speed and clarity.
          </div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="card-soft">
              <div style="font-weight:950;">🏠 Housing</div>
              <div class="small-muted" style="margin-top:8px;">Browse IV listings with clean filters + optional photos.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Housing", use_container_width=True):
            st.session_state["main_nav"] = "🏠 Housing"
            st.rerun()

    with c2:
        st.markdown(
            """
            <div class="card-soft">
              <div style="font-weight:950;">📚 Academics</div>
              <div class="small-muted" style="margin-top:8px;">Plan quarters, search courses, explore resources.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Academics", use_container_width=True):
            st.session_state["main_nav"] = "📚 Academics"
            st.rerun()

    with c3:
        st.markdown(
            """
            <div class="card-soft">
              <div style="font-weight:950;">👩‍🏫 Professors</div>
              <div class="small-muted" style="margin-top:8px;">Fast RMP searches + department pages.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Professors", use_container_width=True):
            st.session_state["main_nav"] = "👩‍🏫 Professors"
            st.rerun()

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card-soft">
          <div style="font-weight:950;">Want more visuals?</div>
          <div class="small-muted" style="margin-top:6px;">
            Add <code>assets/ucsb_bg.jpg</code> for a hero background + <code>assets/ucsb_fallback.jpg</code> for listing thumbnails.
            If your housing CSV has <code>image_url</code>, listings will show real photos automatically.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def housing_page():
    st.markdown(
        """
        <div class="card-soft">
          <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Isla Vista Housing</div>
          <div class="small-muted">CSV snapshot from ivproperties.com (2026–27). Photos show if <code>image_url</code> exists.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    df = load_housing_df()
    if df is None or df.empty:
        st.warning("No housing data found in the CSV.")
        return

    # Filters
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.3, 1.3, 1.3])

    with col_f1:
        max_price_val = int(df["price"].max()) if df["price"].notna().any() else 10000
        min_price_val = int(df["price"].min()) if df["price"].notna().any() else 0
        price_limit = st.slider("Max monthly installment", min_value=min_price_val, max_value=max_price_val, value=max_price_val, step=100)

    with col_f2:
        bedroom_choice = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4", "5+"], index=0)

    with col_f3:
        status_choice = st.selectbox("Status", ["Available only", "All statuses", "Processing only", "Leased only"], index=0)

    with col_f4:
        pet_choice = st.selectbox("Pets", ["Any", "Only pet-friendly", "No pets allowed"], index=0)

    st.markdown("</div>", unsafe_allow_html=True)

    # Apply filters
    filtered = df.copy()
    filtered = filtered[(filtered["price"].isna()) | (filtered["price"] <= price_limit)]

    if bedroom_choice == "Studio":
        filtered = filtered[filtered["is_studio"] == True]
    elif bedroom_choice == "5+":
        filtered = filtered[filtered["bedrooms"] >= 5]
    elif bedroom_choice not in ("Any", "Studio", "5+"):
        try:
            b_val = int(bedroom_choice)
            filtered = filtered[filtered["bedrooms"] == b_val]
        except ValueError:
            pass

    s = status_choice.lower()
    if s.startswith("available"):
        filtered = filtered[filtered["status"].fillna("").str.lower() == "available"]
    elif s.startswith("processing"):
        filtered = filtered[filtered["status"].fillna("").str.lower() == "processing"]
    elif s.startswith("leased"):
        filtered = filtered[filtered["status"].fillna("").str.lower() == "leased"]

    if pet_choice == "Only pet-friendly":
        filtered = filtered[filtered["pet_friendly"] == True]
    elif pet_choice == "No pets allowed":
        filtered = filtered[
            (filtered["pet_friendly"] == False)
            | (filtered["pet_policy"].fillna("").str.contains("No pets", case=False))
        ]

    st.markdown(
        f"""
        <div class="section-gap"></div>
        <div class="card-soft">
          <div class="small-muted">
            Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> units
            • <span class="pill pill-blue">Price ≤ ${price_limit:,}</span>
          </div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.info("No units match your filters. Try raising your max price or widening status/bedroom filters.")
        return

    with st.expander("View table of filtered units"):
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

    # Listing cards with optional image
    for _, row in filtered.sort_values(["street", "unit"]).iterrows():
        street = str(row.get("street") or "").strip()
        unit = str(row.get("unit") or "").strip()
        status = str(row.get("status") or "available").lower().strip()

        price = row.get("price")
        bedrooms = row.get("bedrooms")
        bathrooms = row.get("bathrooms")
        max_res = row.get("max_residents")
        utilities = str(row.get("utilities") or "").strip()
        pet_policy = str(row.get("pet_policy") or "").strip()
        pet_friendly = bool(row.get("pet_friendly", False))
        ppp = row.get("price_per_person")
        avail_start = str(row.get("avail_start") or "").strip()
        avail_end = str(row.get("avail_end") or "").strip()

        image_url = row.get("image_url")
        listing_url = row.get("listing_url")

        # Status styling
        if status == "available":
            status_text = f"Available {avail_start}–{avail_end} (applications open)".strip()
            status_class = "status-ok"
        elif status == "processing":
            status_text = "Processing applications"
            status_class = "status-warn"
        elif status == "leased":
            status_text = f"Currently leased (through {avail_end})" if avail_end else "Currently leased"
            status_class = "status-muted"
        else:
            status_text = status.title()
            status_class = "status-muted"

        # Labels
        is_studio = pd.isna(bedrooms) or float(bedrooms) == 0
        bed_label = "Studio" if is_studio else f"{int(bedrooms) if pd.notna(bedrooms) else '?'} bed"
        if pd.notna(bathrooms):
            ba_label = f"{int(bathrooms)} bath" if float(bathrooms).is_integer() else f"{bathrooms} bath"
        else:
            ba_label = "? bath"
        residents_label = f"Up to {int(max_res)} residents" if pd.notna(max_res) else "Max residents: ?"
        pet_label = pet_policy or ("Pet friendly" if pet_friendly else "No pets info")

        # Price
        price_text = f"${int(price):,}/installment" if pd.notna(price) else "Price not listed"
        ppp_text = f"≈ ${ppp:,.0f} per person" if ppp is not None else ""

        # Image choice: listing image_url -> local fallback -> remote fallback -> none
        img_html = ""
        if isinstance(image_url, str) and image_url.strip():
            img_html = f'<img src="{image_url.strip()}" alt="Listing photo" />'
        elif FALLBACK_LISTING_URI:
            img_html = f'<img src="{FALLBACK_LISTING_URI}" alt="UCSB" />'
        elif REMOTE_FALLBACK_IMAGE_URL:
            img_html = f'<img src="{REMOTE_FALLBACK_IMAGE_URL}" alt="UCSB" />'
        else:
            img_html = ""

        # Optional listing link button
        link_btn = ""
        if isinstance(listing_url, str) and listing_url.strip():
            link_btn = f'<a href="{listing_url.strip()}" target="_blank" style="text-decoration:none;"><span class="pill pill-gold">View listing ↗</span></a>'

        st.markdown(
            f"""
            <div class="card">
              <div class="listing-wrap">
                <div class="thumb">{img_html}</div>

                <div>
                  <div class="listing-title">{street}</div>
                  <div class="listing-sub">{unit}</div>

                  <div class="pills">
                    <span class="pill">{bed_label}</span>
                    <span class="pill">{ba_label}</span>
                    <span class="pill">{residents_label}</span>
                    <span class="pill pill-gold">{pet_label}</span>
                    {link_btn}
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
            """,
            unsafe_allow_html=True,
        )


# ---------------------------
# Professors
# ---------------------------
DEPT_SITES = {
    "PSTAT": "https://www.pstat.ucsb.edu/people",
    "CS": "https://www.cs.ucsb.edu/people/faculty",
    "MATH": "https://www.math.ucsb.edu/people/faculty",
}


def profs_page():
    st.markdown(
        """
        <div class="card-soft">
          <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Professors & course intel</div>
          <div class="small-muted">Quick links to RateMyProfessors searches and department faculty pages.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    name = st.text_input("Professor name", placeholder="e.g., Palaniappan, Porter, Levkowitz…")
    dept = st.selectbox("Department site", list(DEPT_SITES.keys()))
    col1, col2 = st.columns(2)

    with col1:
        if name:
            q = quote_plus(f"{name} site:ratemyprofessors.com UCSB")
            st.link_button("Search on RateMyProfessors", f"https://www.google.com/search?q={q}")
        else:
            st.caption("Enter a name to generate a quick RMP search link.")
    with col2:
        st.link_button("Open dept faculty page", DEPT_SITES[dept])

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Aid & Jobs
# ---------------------------
AID_LINKS = {
    "FAFSA": "https://studentaid.gov/h/apply-for-aid/fafsa",
    "UCSB Financial Aid": "https://www.finaid.ucsb.edu/",
    "Work-Study (UCSB)": "https://www.finaid.ucsb.edu/types-of-aid/work-study",
    "Handshake": "https://ucsb.joinhandshake.com/",
}


def aid_jobs_page():
    st.markdown(
        """
        <div class="card-soft">
          <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Financial aid, work-study & jobs</div>
          <div class="small-muted">Short explainers + quick links.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What is financial aid?"):
        st.write(
            """
            Financial aid reduces your cost of attendance via grants, scholarships, work-study, and loans.
            File the FAFSA (or CADAA if applicable) early each year and watch priority deadlines.
            """
        )

    with st.expander("What is work-study?"):
        st.write(
            """
            Work-study is a need-based program that lets you earn money via part-time jobs on or near campus.
            Your award caps how much you can earn under work-study each year.
            """
        )

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    cols = st.columns(4)
    items = list(AID_LINKS.items())
    for i, (label, url) in enumerate(items):
        with cols[i % 4]:
            st.link_button(label, url)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Q&A
# ---------------------------
def qa_page():
    st.markdown(
        """
        <div class="card-soft">
          <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Ask gauchoGPT</div>
          <div class="small-muted">Wire this to your preferred LLM API or a local model.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="card">', unsafe_allow_html=True)
    prompt = st.text_area("Ask a UCSB question", placeholder="e.g., How do I switch into the STAT&DS major?")
    if st.button("Answer"):
        st.info("Connect to an API (OpenAI / Anthropic / local) here.")
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Routing
# ---------------------------
PAGES: Dict[str, Any] = {
    "🏁 Home": home_page,
    "🏠 Housing": housing_page,
    "📚 Academics": academics_page,
    "👩‍🏫 Professors": profs_page,
    "💸 Aid & Jobs": aid_jobs_page,
    "💬 Q&A": qa_page,
}

PAGES[st.session_state["main_nav"]]()
