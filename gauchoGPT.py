# gauchoGPT — Streamlit “Apple-clean” UI + LEFT sidebar hamburger + Sidebar nav + Optional UCSB background
# ------------------------------------------------------------------------------------------------------
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
# Optional UCSB background image (local file)
# Put an image at: assets/ucsb_bg.jpg  (or .png)
# ---------------------------
def _img_to_data_uri(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        return None
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
    return f"data:image/{mime};base64,{b64}"


BG_URI = (
    _img_to_data_uri("assets/ucsb_bg.jpg")
    or _img_to_data_uri("assets/ucsb_bg.jpeg")
    or _img_to_data_uri("assets/ucsb_bg.png")
    or _img_to_data_uri("assets/ucsb_bg.webp")
)

# ---------------------------
# Session state defaults
# ---------------------------
NAV_LABELS = ["🏁 Home", "🏠 Housing", "📚 Academics", "👩‍🏫 Professors", "💸 Aid & Jobs", "💬 Q&A"]

if "main_nav" not in st.session_state:
    st.session_state["main_nav"] = "🏁 Home"

# THIS is the hamburger behavior you asked for:
# When closed -> show Admin + Status only
# When open   -> show Admin + Status + Navigation buttons (Home/Housing/...)
if "sidebar_nav_open" not in st.session_state:
    st.session_state["sidebar_nav_open"] = False

# ---------------------------
# Styles
# ---------------------------
APPLE_STYLE = f"""
<style>
:root{{
  --bg: #f5f5f7;
  --card: #ffffff;
  --text: #1d1d1f;
  --muted: #6e6e73;
  --line: rgba(0,0,0,0.10);
  --shadow1: 0 2px 10px rgba(0,0,0,0.06);
  --radius: 18px;

  --accent: #0071e3;
  --accent2: #0a84ff;
}}

[data-testid="stAppViewContainer"]{{
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji",
               "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
}}

{f"""
/* Optional full-page background image */
[data-testid="stAppViewContainer"]::before {{
  content: "";
  position: fixed;
  inset: 0;
  background:
    radial-gradient(1000px 450px at 20% 10%, rgba(255,255,255,0.60), rgba(255,255,255,0.0)),
    linear-gradient(rgba(245,245,247,0.86), rgba(245,245,247,0.94)),
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
  padding-top: 4.75rem;   /* fixes “top text blocked” */
  max-width: 1400px;      /* reduces side whitespace */
}}

h1,h2,h3,h4{{ color: var(--text); letter-spacing: -0.02em; }}
h1{{ font-size: 2.35rem; font-weight: 850; }}
h2{{ font-size: 1.55rem; font-weight: 800; }}
h3{{ font-size: 1.15rem; font-weight: 750; }}

.small-muted{{ color: var(--muted); font-size: 0.92rem; line-height: 1.35; }}

.apple-topbar{{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
  background: rgba(245,245,247,0.82);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
}}
.apple-topbar-inner{{
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.brand{{
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 850;
  letter-spacing: -0.02em;
}}
.brand .dot{{
  width: 10px; height: 10px;
  background: var(--accent);
  border-radius: 999px;
  box-shadow: 0 0 0 4px rgba(0,113,227,0.12);
}}
.brand small{{ color: var(--muted); font-weight: 650; }}
.topbar-right{{ color: var(--muted); font-weight: 650; font-size: 0.92rem; }}

.card{{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow1);
  padding: 16px 18px;
}}
.card-tight{{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow1);
  padding: 12px 14px;
}}
.section-gap{{ height: 14px; }}

/* Buttons */
.stButton > button{{
  background: var(--accent);
  border: 1px solid rgba(0,0,0,0.0);
  color: white;
  border-radius: 999px;
  padding: 0.58rem 1.05rem;
  font-weight: 850;
}}
.stButton > button:hover{{ background: var(--accent2); }}

/* Make selects/sliders more visible */
[data-baseweb="select"] > div {{
  background: rgba(255,255,255,0.92) !important;
  border: 1px solid rgba(0,0,0,0.18) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04) !important;
}}
div[data-testid="stSlider"] {{
  padding: 10px 12px;
  background: rgba(255,255,255,0.80);
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 14px;
}}

/* Sidebar */
[data-testid="stSidebar"]{{
  background: rgba(245,245,247,0.92);
  border-right: 1px solid var(--line);
}}
[data-testid="stSidebar"] .block-container{{ padding-top: 1.15rem; }}

/* Sidebar hamburger icon button */
.sidebar-hamburger .stButton > button {{
  width: 44px !important;
  height: 44px !important;
  padding: 0 !important;
  border-radius: 999px !important;
  background: rgba(0,0,0,0.06) !important;
  color: var(--text) !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  box-shadow: none !important;
  font-size: 18px !important;
}}
.sidebar-hamburger .stButton > button:hover {{
  background: rgba(0,0,0,0.10) !important;
}}

/* Sidebar nav buttons (dark text, “chip” look) */
.sidebar-nav button {{
  width: 100%;
  background: rgba(0,0,0,0.04) !important;
  color: var(--text) !important;
  border: 1px solid rgba(0,0,0,0.10) !important;
  border-radius: 14px !important;
  padding: 0.65rem 0.9rem !important;
  font-weight: 900 !important;
  box-shadow: none !important;
  text-align: left !important;
}}
.sidebar-nav button:hover {{
  background: rgba(0,0,0,0.07) !important;
}}
.sidebar-nav-active button {{
  background: rgba(0,113,227,0.12) !important;
  border-color: rgba(0,113,227,0.26) !important;
  color: #0b3a6a !important;
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
"""
st.markdown(APPLE_STYLE, unsafe_allow_html=True)

# ---------------------------
# Topbar (visual only)
# ---------------------------
st.markdown(
    """
    <div class="apple-topbar">
      <div class="apple-topbar-inner">
        <div class="brand">
          <span class="dot"></span>
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
# Sidebar: hamburger + status/admin + (toggleable) nav
# ---------------------------
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

# Hamburger toggle INSIDE the sidebar (what you asked for)
st.sidebar.markdown('<div class="sidebar-hamburger">', unsafe_allow_html=True)
hamb_label = "☰" if not st.session_state["sidebar_nav_open"] else "✕"
if st.sidebar.button(hamb_label, key="sidebar_hamburger"):
    st.session_state["sidebar_nav_open"] = not st.session_state["sidebar_nav_open"]
    st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# When hamburger is open: show nav buttons in the LEFT sidebar (with admin/status)
if st.session_state["sidebar_nav_open"]:
    st.sidebar.divider()
    st.sidebar.markdown("### Navigation")
    for label in NAV_LABELS:
        is_active = (st.session_state["main_nav"] == label)
        cls = "sidebar-nav-active" if is_active else "sidebar-nav"
        st.sidebar.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.sidebar.button(label, key=f"side_nav_{label}"):
            st.session_state["main_nav"] = label
            st.session_state["sidebar_nav_open"] = False  # auto-close after choosing
            st.rerun()
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Status/Admin always visible (still on the left)
st.sidebar.divider()
st.sidebar.markdown("### 📊 Data Status")

db_exists = os.path.exists("gauchoGPT.db")
csv_exists = os.path.exists("major_courses_by_quarter.csv")

if db_exists:
    st.sidebar.success("✅ Course database active")
    import sqlite3
    try:
        conn = sqlite3.connect("gauchoGPT.db")
        cur = conn.cursor()
        cur.execute("SELECT MAX(scraped_at) FROM course_offerings")
        last_update = cur.fetchone()[0]
        conn.close()
        if last_update:
            st.sidebar.caption(f"Last scraped: {str(last_update)[:10]}")
    except Exception:
        pass
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
# Pages
# ---------------------------
HOUSING_CSV = "iv_housing_listings.csv"


def load_housing_df() -> Optional[pd.DataFrame]:
    if not os.path.exists(HOUSING_CSV):
        st.error(f"Missing CSV file: {HOUSING_CSV}. Place it next to gauchoGPT.py.")
        return None

    df = pd.read_csv(HOUSING_CSV)

    for col in [
        "street", "unit", "avail_start", "avail_end",
        "price", "bedrooms", "bathrooms", "max_residents",
        "utilities", "pet_policy", "pet_friendly",
    ]:
        if col not in df.columns:
            df[col] = None

    if "status" not in df.columns:
        df["status"] = "available"
    if "is_studio" not in df.columns:
        df["is_studio"] = df.get("bedrooms", 0).fillna(0).astype(float).eq(0)

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")

    df["pet_friendly"] = df.get("pet_friendly", False)
    df["pet_friendly"] = df["pet_friendly"].fillna(False).astype(bool)

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
        <div class="card" style="padding:22px 22px;">
          <div style="font-size:2.2rem; font-weight:900; letter-spacing:-0.03em;">UCSB tools, in one place.</div>
          <div class="small-muted" style="margin-top:6px;">
            gauchoGPT is a student-first dashboard to find housing, plan classes, check professors, and navigate aid & jobs — fast.
          </div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><b>🏠 Housing</b><div class="small-muted" style="margin-top:8px;">Filter IV listings by price, beds, status, and pets.</div></div>', unsafe_allow_html=True)
        if st.button("Open Housing", use_container_width=True):
            st.session_state["main_nav"] = "🏠 Housing"
            st.rerun()

    with c2:
        st.markdown('<div class="card"><b>📚 Academics</b><div class="small-muted" style="margin-top:8px;">Plan quarters, search courses, and explore advising resources.</div></div>', unsafe_allow_html=True)
        if st.button("Open Academics", use_container_width=True):
            st.session_state["main_nav"] = "📚 Academics"
            st.rerun()

    with c3:
        st.markdown('<div class="card"><b>👩‍🏫 Professors</b><div class="small-muted" style="margin-top:8px;">Quick RMP searches + department directories.</div></div>', unsafe_allow_html=True)
        if st.button("Open Professors", use_container_width=True):
            st.session_state["main_nav"] = "👩‍🏫 Professors"
            st.rerun()


def housing_page():
    st.markdown(
        """
        <div class="card">
          <div style="font-size:1.35rem; font-weight:900; letter-spacing:-0.02em;">Isla Vista Housing</div>
          <div class="small-muted">CSV snapshot from ivproperties.com (2026–27). Filter and browse cleanly.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    df = load_housing_df()
    if df is None or df.empty:
        st.warning("No housing data found in the CSV.")
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)

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
        filtered = filtered[filtered["status"] == "available"]
    elif s.startswith("processing"):
        filtered = filtered[filtered["status"] == "processing"]
    elif s.startswith("leased"):
        filtered = filtered[filtered["status"] == "leased"]

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
        <div class="card-tight">
          <div class="small-muted">
            Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> units
            • Price ≤ <span style="display:inline-flex;padding:6px 10px;border-radius:999px;background:rgba(0,113,227,0.10);border:1px solid rgba(0,113,227,0.26);color:#0b3a6a;font-weight:800;">
              ${price_limit:,}
            </span>
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
                    "street",
                    "unit",
                    "status",
                    "avail_start",
                    "avail_end",
                    "price",
                    "bedrooms",
                    "bathrooms",
                    "max_residents",
                    "pet_policy",
                    "utilities",
                    "price_per_person",
                ]
            ],
            use_container_width=True,
        )

    # Simple listing render (keep your existing card version if you prefer)
    for _, row in filtered.sort_values(["street", "unit"]).iterrows():
        st.markdown(
            f"""
            <div class="card">
              <div style="font-size:1.25rem;font-weight:900;">{row.get("street","")}</div>
              <div class="small-muted">{row.get("unit","")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def profs_page():
    st.markdown(
        """
        <div class="card">
          <div style="font-size:1.35rem; font-weight:900; letter-spacing:-0.02em;">Professors & course intel</div>
          <div class="small-muted">Quick links to RateMyProfessors searches and department faculty pages.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    DEPT_SITES = {
        "PSTAT": "https://www.pstat.ucsb.edu/people",
        "CS": "https://www.cs.ucsb.edu/people/faculty",
        "MATH": "https://www.math.ucsb.edu/people/faculty",
    }

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


def aid_jobs_page():
    st.markdown(
        """
        <div class="card">
          <div style="font-size:1.35rem; font-weight:900; letter-spacing:-0.02em;">Financial aid, work-study & jobs</div>
          <div class="small-muted">Short explainers + quick links.</div>
        </div>
        <div class="section-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    AID_LINKS = {
        "FAFSA": "https://studentaid.gov/h/apply-for-aid/fafsa",
        "UCSB Financial Aid": "https://www.finaid.ucsb.edu/",
        "Work-Study (UCSB)": "https://www.finaid.ucsb.edu/types-of-aid/work-study",
        "Handshake": "https://ucsb.joinhandshake.com/",
    }

    st.markdown('<div class="card">', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (label, url) in enumerate(AID_LINKS.items()):
        with cols[i % 4]:
            st.link_button(label, url)
    st.markdown("</div>", unsafe_allow_html=True)


def qa_page():
    st.markdown(
        """
        <div class="card">
          <div style="font-size:1.35rem; font-weight:900; letter-spacing:-0.02em;">Ask gauchoGPT</div>
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


PAGES: Dict[str, Any] = {
    "🏁 Home": home_page,
    "🏠 Housing": housing_page,
    "📚 Academics": academics_page,
    "👩‍🏫 Professors": profs_page,
    "💸 Aid & Jobs": aid_jobs_page,
    "💬 Q&A": qa_page,
}

# ---------------------------
# Render selected page
# ---------------------------
PAGES[st.session_state["main_nav"]]()
