# gauchoGPT — Streamlit “Premium UCSB” UI + Left Sidebar Hamburger Nav + Images (optional)
# --------------------------------------------------------------------------------------
from __future__ import annotations

import os
import base64
import textwrap
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
# Helpers
# ---------------------------
def render_html(html: str) -> None:
    """Render HTML reliably (prevents Streamlit from printing raw tags)."""
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)

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

def safe_str(x) -> str:
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)

def first_existing_data_uri(*paths: str) -> Optional[str]:
    for p in paths:
        uri = img_to_data_uri(p)
        if uri:
            return uri
    return None


# ---------------------------
# Optional background + fallback images
# Put files in: assets/
# ---------------------------
BG_URI = first_existing_data_uri(
    "assets/ucsb_bg.jpg", "assets/ucsb_bg.jpeg", "assets/ucsb_bg.png", "assets/ucsb_bg.webp"
)

FALLBACK_LISTING_URI = first_existing_data_uri(
    "assets/ucsb_fallback.jpg", "assets/ucsb_fallback.jpeg", "assets/ucsb_fallback.png", "assets/ucsb_fallback.webp"
)

# Optional thumbnails for home rows (add any of these; totally optional)
HOME_HOUSING_URI = first_existing_data_uri(
    "assets/home_housing.jpg", "assets/home_housing.jpeg", "assets/home_housing.png", "assets/home_housing.webp"
)
HOME_ACADEMICS_URI = first_existing_data_uri(
    "assets/home_academics.jpg", "assets/home_academics.jpeg", "assets/home_academics.png", "assets/home_academics.webp"
)
HOME_PROFS_URI = first_existing_data_uri(
    "assets/home_profs.jpg", "assets/home_profs.jpeg", "assets/home_profs.png", "assets/home_profs.webp"
)
HOME_AID_URI = first_existing_data_uri(
    "assets/home_aid.jpg", "assets/home_aid.jpeg", "assets/home_aid.png", "assets/home_aid.webp"
)
HOME_QA_URI = first_existing_data_uri(
    "assets/home_qa.jpg", "assets/home_qa.jpeg", "assets/home_qa.png", "assets/home_qa.webp"
)

REMOTE_FALLBACK_IMAGE_URL = None  # optional, set to a public image URL if you want


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
:root {{
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

[data-testid="stAppViewContainer"] {{
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji",
               "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
}}

{"".join([
f"""
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
""" if BG_URI else ""
])}

[data-testid="stAppViewContainer"] > .main {{
  position: relative;
  z-index: 1;
}}

.block-container {{
  padding-top: 5.2rem;
  max-width: 1480px;
}}

.small-muted {{ color: var(--muted); font-size: 0.93rem; line-height: 1.35; }}

/* Topbar */
.topbar {{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
  background: rgba(246,247,251,0.78);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
}}
.topbar-inner {{
  max-width: 1480px;
  margin: 0 auto;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.brand {{ display:flex; align-items:center; gap:10px; font-weight: 900; }}
.brand-dot {{
  width: 10px; height: 10px;
  background: var(--gold);
  border-radius: 999px;
  box-shadow: 0 0 0 5px rgba(253,181,21,0.18);
}}
.brand small {{ color: var(--muted); font-weight: 700; }}
.topbar-right {{ color: var(--muted); font-weight: 700; font-size: 0.93rem; }}

/* Cards */
.card {{
  background: var(--card2);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px 18px;
}}
.card-soft {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow2);
  padding: 14px 16px;
}}
.section-gap {{ height: 14px; }}

/* Hero */
.hero {{
  background: linear-gradient(135deg, rgba(0,54,96,0.92), rgba(0,113,227,0.78));
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 22px;
  box-shadow: var(--shadow);
  padding: 22px 22px;
  color: white;
}}
.hero-title {{ font-size: 2.2rem; font-weight: 950; letter-spacing:-0.03em; }}
.hero-sub {{ opacity: 0.92; margin-top: 8px; font-weight: 650; }}

/* Pills */
.pills {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
.pill {{
  display:inline-flex; align-items:center; gap:6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(2, 6, 23, 0.05);
  border: 1px solid rgba(2, 6, 23, 0.08);
  font-weight: 750;
  font-size: 0.90rem;
}}
.pill-gold {{ background: rgba(253,181,21,0.18); border-color: rgba(253,181,21,0.30); }}
.pill-blue {{ background: rgba(10,132,255,0.14); border-color: rgba(10,132,255,0.28); }}

/* Status */
.status-ok {{ color: var(--ok); font-weight: 900; }}
.status-warn {{ color: var(--warn); font-weight: 900; }}
.status-muted {{ color: var(--muted); font-weight: 800; }}

/* Buttons */
.stButton > button {{
  background: linear-gradient(135deg, var(--blue2), var(--blue));
  border: 1px solid rgba(255,255,255,0.12);
  color: white;
  border-radius: 999px;
  padding: 0.60rem 1.05rem;
  font-weight: 900;
  box-shadow: 0 10px 25px rgba(0,113,227,0.20);
}}
.stButton > button:hover {{ filter: brightness(1.05); }}

/* Inputs visibility (select + slider) */
[data-baseweb="select"] > div {{
  background: rgba(255,255,255,0.98) !important;
  border: 1px solid rgba(15,23,42,0.22) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 12px rgba(2,6,23,0.06) !important;
}}
div[data-testid="stSlider"] {{
  padding: 10px 12px;
  background: rgba(255,255,255,0.94);
  border: 1px solid rgba(15,23,42,0.16);
  border-radius: 14px;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
  background: rgba(246,247,251,0.92);
  border-right: 1px solid var(--line);
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.10rem; }}

/* Sidebar hamburger */
.sidebar-hamburger .stButton > button {{
  width: 46px !important; height: 46px !important;
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
.sidebar-nav button:hover {{ background: rgba(0,54,96,0.10) !important; }}
.sidebar-nav-active button {{
  background: rgba(253,181,21,0.24) !important;
  border-color: rgba(253,181,21,0.42) !important;
  color: #1f2937 !important;
}}

/* Home: stacked rows */
.home-row {{
  display:flex;
  gap:16px;
  align-items:center;
  justify-content:space-between;
}}
.home-left {{
  display:flex;
  gap:16px;
  align-items:center;
}}
.home-thumb {{
  width: 160px;
  height: 96px;
  border-radius: 16px;
  border: 1px solid rgba(2,6,23,0.10);
  overflow: hidden;
  background: rgba(0,0,0,0.04);
  flex: 0 0 auto;
}}
.home-thumb img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}
.home-title {{
  font-size: 1.20rem;
  font-weight: 950;
  letter-spacing: -0.02em;
}}
.home-desc {{
  margin-top: 6px;
  max-width: 820px;
}}
@media (max-width: 900px) {{
  .home-row {{ flex-direction: column; align-items: flex-start; }}
  .home-thumb {{ width: 100%; height: 160px; }}
}}

/* Housing listing layout */
.listing-wrap {{
  display:grid;
  grid-template-columns: 210px 1fr;
  gap: 14px;
  align-items: stretch;
}}
@media (max-width: 900px) {{
  .listing-wrap {{ grid-template-columns: 1fr; }}
}}
.thumb {{
  width: 100%;
  height: 150px;
  border-radius: 16px;
  border: 1px solid rgba(2,6,23,0.10);
  overflow: hidden;
  background: rgba(0,0,0,0.04);
}}
.thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
.listing-title {{ font-size: 1.25rem; font-weight: 950; letter-spacing:-0.02em; }}
.listing-sub {{ color: var(--muted); font-size: 0.92rem; margin-top: 3px; }}
.price-row {{ margin-top: 10px; font-weight: 950; font-size: 1.05rem; }}

/* Hide Streamlit chrome */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
"""
render_html(UCSB_STYLE)


# ---------------------------
# Topbar
# ---------------------------
render_html("""
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
""")


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
st.sidebar.markdown("""
**Next steps (quick)**
- Keep CSV updated
- Configure scraper selectors
- Connect LLM for Q&A
""")


# ---------------------------
# HOUSING — CSV-backed
# ---------------------------
HOUSING_CSV = "iv_housing_listings.csv"

def load_housing_df() -> Optional[pd.DataFrame]:
    if not os.path.exists(HOUSING_CSV):
        st.error(f"Missing CSV file: {HOUSING_CSV}. Place it next to gauchoGPT.py.")
        return None

    df = pd.read_csv(HOUSING_CSV)

    # Ensure expected columns exist
    for col in [
        "street", "unit", "avail_start", "avail_end",
        "price", "bedrooms", "bathrooms", "max_residents",
        "utilities", "pet_policy", "pet_friendly", "status",
        "image_url", "listing_url",
    ]:
        if col not in df.columns:
            df[col] = None

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")

    df["pet_friendly"] = df["pet_friendly"].fillna(False).astype(bool)

    # Normalize status so filters work reliably
    df["status"] = df["status"].fillna("available").astype(str).str.lower().str.strip()
    df["is_studio"] = df["bedrooms"].fillna(0).astype(float).eq(0)

    df["price_per_person"] = df.apply(
        lambda r: r["price"] / r["max_residents"]
        if pd.notnull(r["price"]) and pd.notnull(r["max_residents"]) and r["max_residents"] > 0
        else None,
        axis=1,
    )
    return df


# ---------------------------
# HOME (UPDATED: stacked full-width rows)
# ---------------------------
def _home_row(title: str, desc: str, btn_text: str, nav_target: str, img_uri: Optional[str] = None):
    img_html = ""
    if img_uri:
        img_html = f'<div class="home-thumb"><img src="{img_uri}" alt="UCSB" /></div>'

    render_html(f"""
    <div class="card">
      <div class="home-row">
        <div class="home-left">
          {img_html}
          <div>
            <div class="home-title">{title}</div>
            <div class="small-muted home-desc">{desc}</div>
          </div>
        </div>
        <div style="min-width:230px;"></div>
      </div>
    </div>
    """)

    # Keep Streamlit button outside the HTML so it remains clickable/reliable
    _, cbtn = st.columns([1, 0.25])
    with cbtn:
        if st.button(btn_text, use_container_width=True):
            st.session_state["main_nav"] = nav_target
            st.rerun()

    render_html('<div class="section-gap"></div>')


def home_page():
    render_html("""
    <div class="hero">
      <div class="hero-title">UCSB tools, in one place.</div>
      <div class="hero-sub">
        Find housing, plan classes, check professors, and navigate aid & jobs — built for speed and clarity.
      </div>
    </div>
    <div class="section-gap"></div>
    """)

    _home_row(
        "🏠 Housing",
        "Browse IV listings with clean filters + optional photos.",
        "Open Housing",
        "🏠 Housing",
        HOME_HOUSING_URI,
    )
    _home_row(
        "📚 Academics",
        "Plan quarters, search courses, explore resources.",
        "Open Academics",
        "📚 Academics",
        HOME_ACADEMICS_URI,
    )
    _home_row(
        "👩‍🏫 Professors",
        "Fast RMP searches + department pages.",
        "Open Professors",
        "👩‍🏫 Professors",
        HOME_PROFS_URI,
    )
    _home_row(
        "💸 Aid & Jobs",
        "FAFSA, work-study, UCSB aid + Handshake links.",
        "Open Aid & Jobs",
        "💸 Aid & Jobs",
        HOME_AID_URI,
    )
    _home_row(
        "💬 Q&A",
        "Optional: wire to an LLM (OpenAI/Anthropic/local).",
        "Open Q&A",
        "💬 Q&A",
        HOME_QA_URI,
    )

    render_html("""
    <div class="card-soft">
      <div style="font-weight:950;">🧢 Tip</div>
      <div class="small-muted" style="margin-top:8px;">
        Add <code>assets/home_housing.jpg</code>, <code>assets/home_academics.jpg</code>, etc. for thumbnails.
        Background: <code>assets/ucsb_bg.jpg</code>.
      </div>
    </div>
    """)


# ---------------------------
# HOUSING PAGE
# ---------------------------
def housing_page():
    render_html("""
    <div class="card-soft">
      <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Isla Vista Housing</div>
      <div class="small-muted">
        CSV snapshot from ivproperties.com (2026–27).
        Photos show if <code>image_url</code> exists. Add a local fallback in <code>assets/ucsb_fallback.jpg</code>.
      </div>
    </div>
    <div class="section-gap"></div>
    """)

    df = load_housing_df()
    if df is None or df.empty:
        st.warning("No housing data found in the CSV.")
        return

    # Filters
    render_html('<div class="card">')
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.3, 1.3, 1.3])

    with col_f1:
        max_price_val = int(df["price"].max()) if df["price"].notna().any() else 10000
        min_price_val = int(df["price"].min()) if df["price"].notna().any() else 0
        price_limit = st.slider(
            "Max monthly installment",
            min_value=min_price_val,
            max_value=max_price_val,
            value=max_price_val,
            step=100,
        )

    with col_f2:
        bedroom_choice = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4", "5+"], index=0)

    with col_f3:
        status_choice = st.selectbox("Status", ["Available only", "All statuses", "Processing only", "Leased only"], index=0)

    with col_f4:
        pet_choice = st.selectbox("Pets", ["Any", "Only pet-friendly", "No pets allowed"], index=0)

    render_html("</div>")

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

    status_lower = filtered["status"].fillna("").astype(str).str.lower().str.strip()
    s = status_choice.lower()
    if s.startswith("available"):
        filtered = filtered[status_lower == "available"]
    elif s.startswith("processing"):
        filtered = filtered[status_lower == "processing"]
    elif s.startswith("leased"):
        filtered = filtered[status_lower == "leased"]

    if pet_choice == "Only pet-friendly":
        filtered = filtered[filtered["pet_friendly"] == True]
    elif pet_choice == "No pets allowed":
        filtered = filtered[
            (filtered["pet_friendly"] == False)
            | (filtered["pet_policy"].fillna("").astype(str).str.contains("No pets", case=False))
        ]

    render_html(f"""
    <div class="section-gap"></div>
    <div class="card-soft">
      <div class="small-muted">
        Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> units
        • <span class="pill pill-blue">Price ≤ ${price_limit:,}</span>
      </div>
    </div>
    <div class="section-gap"></div>
    """)

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

    # Listing cards
    for _, row in filtered.sort_values(["street", "unit"], na_position="last").iterrows():
        street = safe_str(row.get("street")).strip()
        unit = safe_str(row.get("unit")).strip()
        status = safe_str(row.get("status")).lower().strip()

        price = row.get("price")
        bedrooms = row.get("bedrooms")
        bathrooms = row.get("bathrooms")
        max_res = row.get("max_residents")
        utilities = safe_str(row.get("utilities")).strip()
        pet_policy = safe_str(row.get("pet_policy")).strip()
        pet_friendly = bool(row.get("pet_friendly", False))
        ppp = row.get("price_per_person")
        avail_start = safe_str(row.get("avail_start")).strip()
        avail_end = safe_str(row.get("avail_end")).strip()

        image_url = safe_str(row.get("image_url")).strip()
        listing_url = safe_str(row.get("listing_url")).strip()

        # Status styling
        if status == "available":
            date_part = ""
            if avail_start or avail_end:
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

        residents_label = f"Up to {int(max_res)} residents" if pd.notna(max_res) else "Max residents: ?"
        pet_label = pet_policy or ("Pet friendly" if pet_friendly else "No pets info")

        price_text = f"${int(price):,}/installment" if pd.notna(price) else "Price not listed"
        ppp_text = f"≈ ${ppp:,.0f} per person" if ppp is not None else ""

        # Image selection
        img_html = ""
        if image_url:
            img_html = f'<img src="{image_url}" alt="Listing photo" />'
        elif FALLBACK_LISTING_URI:
            img_html = f'<img src="{FALLBACK_LISTING_URI}" alt="UCSB" />'
        elif REMOTE_FALLBACK_IMAGE_URL:
            img_html = f'<img src="{REMOTE_FALLBACK_IMAGE_URL}" alt="UCSB" />'

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
              <div class="listing-title">{street}</div>
              <div class="listing-sub">{unit}</div>

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


# ---------------------------
# PROFESSORS
# ---------------------------
DEPT_SITES = {
    "PSTAT": "https://www.pstat.ucsb.edu/people",
    "CS": "https://www.cs.ucsb.edu/people/faculty",
    "MATH": "https://www.math.ucsb.edu/people/faculty",
}

def profs_page():
    render_html("""
    <div class="card-soft">
      <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Professors & course intel</div>
      <div class="small-muted">Quick links to RateMyProfessors searches and department faculty pages.</div>
    </div>
    <div class="section-gap"></div>
    """)

    render_html('<div class="card">')
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

    render_html("</div>")


# ---------------------------
# AID & JOBS
# ---------------------------
AID_LINKS = {
    "FAFSA": "https://studentaid.gov/h/apply-for-aid/fafsa",
    "UCSB Financial Aid": "https://www.finaid.ucsb.edu/",
    "Work-Study (UCSB)": "https://www.finaid.ucsb.edu/types-of-aid/work-study",
    "Handshake": "https://ucsb.joinhandshake.com/",
}

def aid_jobs_page():
    render_html("""
    <div class="card-soft">
      <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Financial aid, work-study & jobs</div>
      <div class="small-muted">Short explainers + quick links.</div>
    </div>
    <div class="section-gap"></div>
    """)

    with st.expander("What is financial aid?"):
        st.write(
            "Financial aid reduces your cost of attendance via grants, scholarships, work-study, and loans. "
            "File the FAFSA (or CADAA if applicable) early each year and watch priority deadlines."
        )

    with st.expander("What is work-study?"):
        st.write(
            "Work-study is a need-based program that lets you earn money via part-time jobs on or near campus. "
            "Your award caps how much you can earn under work-study each year."
        )

    render_html('<div class="section-gap"></div>')
    render_html('<div class="card">')
    cols = st.columns(4)
    items = list(AID_LINKS.items())
    for i, (label, url) in enumerate(items):
        with cols[i % 4]:
            st.link_button(label, url)
    render_html("</div>")


# ---------------------------
# Q&A
# ---------------------------
def qa_page():
    render_html("""
    <div class="card-soft">
      <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Ask gauchoGPT</div>
      <div class="small-muted">Wire this to your preferred LLM API or a local model.</div>
    </div>
    <div class="section-gap"></div>
    """)
    render_html('<div class="card">')
    prompt = st.text_area("Ask a UCSB question", placeholder="e.g., How do I switch into the STAT&DS major?")
    if st.button("Answer"):
        st.info("Connect to an API (OpenAI / Anthropic / local) here.")
        st.caption(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    render_html("</div>")


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
