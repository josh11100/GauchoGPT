# gauchoGPT — Streamlit “Apple-clean” UI refresh + Modern box-tab navigation
# ------------------------------------------------------------
from __future__ import annotations

import os
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
from urllib.parse import quote_plus

try:
    from streamlit_folium import st_folium  # noqa: F401
    import folium  # noqa: F401
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

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
# “Apple-like” clean UI theme
# ---------------------------
APPLE_STYLE = """
<style>
:root{
  --bg: #f5f5f7;
  --card: #ffffff;
  --text: #1d1d1f;
  --muted: #6e6e73;
  --line: rgba(0,0,0,0.08);
  --shadow2: 0 2px 10px rgba(0,0,0,0.06);
  --radius: 18px;

  /* UCSB accents but subtle */
  --navy: #003660;
  --gold: #FDB515;

  /* Primary action (Apple-ish) */
  --accent: #0071e3;
  --accent2: #0a84ff;
}

/* App background + typography */
[data-testid="stAppViewContainer"]{
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji",
               "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
}

/* Center the content like a page */
.block-container{
  padding-top: 1.25rem;
  max-width: 1120px;
}

/* Headings */
h1,h2,h3,h4{
  color: var(--text);
  letter-spacing: -0.02em;
}
h1{ font-size: 2.35rem; font-weight: 850; }
h2{ font-size: 1.55rem; font-weight: 800; }
h3{ font-size: 1.15rem; font-weight: 750; }

/* Subtle helper text */
.small-muted{ color: var(--muted); font-size: 0.92rem; line-height: 1.35; }

/* Minimal sticky topbar */
.apple-topbar{
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(245,245,247,0.82);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
}
.apple-topbar-inner{
  max-width: 1120px;
  margin: 0 auto;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand{
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 850;
  letter-spacing: -0.02em;
}
.brand .dot{
  width: 10px;
  height: 10px;
  background: var(--accent);
  border-radius: 999px;
  box-shadow: 0 0 0 4px rgba(0,113,227,0.12);
}
.brand small{
  color: var(--muted);
  font-weight: 650;
}
.topbar-right{
  color: var(--muted);
  font-weight: 650;
  font-size: 0.92rem;
}

/* Card system */
.card{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow2);
  padding: 16px 18px;
}
.card-tight{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow2);
  padding: 12px 14px;
}
.section-gap{ height: 14px; }

/* Pills */
.pills{ display:flex; flex-wrap:wrap; gap:8px; margin: 10px 0 6px; }
.pill{
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.06);
  color: var(--text);
  font-weight: 650;
  font-size: 0.9rem;
}
.pill-blue{
  background: rgba(0,113,227,0.10);
  border-color: rgba(0,113,227,0.18);
  color: #0b3a6a;
}

/* Listing typography */
.listing-title{
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  margin: 0 0 6px 0;
}
.listing-sub{
  color: var(--muted);
  font-size: 0.92rem;
  margin-bottom: 8px;
}

/* Status */
.status-ok{ color: #1f7a1f; font-weight: 800; }
.status-warn{ color: #a35a00; font-weight: 800; }
.status-muted{ color: var(--muted); font-weight: 650; }

/* Buttons (global) */
.stButton > button{
  background: var(--accent);
  border: 1px solid rgba(0,0,0,0.0);
  color: white;
  border-radius: 999px;
  padding: 0.55rem 1.05rem;
  font-weight: 800;
  box-shadow: 0 10px 25px rgba(0,113,227,0.18);
}
.stButton > button:hover{
  background: var(--accent2);
}

/* Inputs */
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea{
  border-radius: 12px !important;
}
[data-baseweb="select"] > div{
  border-radius: 12px !important;
}

/* Dataframe header */
.stDataFrame thead tr th{
  background-color: rgba(0,0,0,0.06) !important;
  color: var(--text) !important;
  border-bottom: 1px solid var(--line) !important;
}

/* Sidebar: subtle */
[data-testid="stSidebar"]{
  background: rgba(245,245,247,0.92);
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .block-container{
  padding-top: 1.15rem;
}

/* --- Modern tab chips (button-based) --- */
.nav-chip button{
  width: 100%;
  background: rgba(0,0,0,0.04) !important;
  color: var(--text) !important;
  border: 1px solid rgba(0,0,0,0.08) !important;
  border-radius: 999px !important;
  padding: 0.55rem 0.9rem !important;
  font-weight: 850 !important;
  box-shadow: none !important;
}
.nav-chip button:hover{
  background: rgba(0,0,0,0.06) !important;
}

/* Active chip */
.nav-chip-active button{
  background: rgba(0,113,227,0.12) !important;
  border-color: rgba(0,113,227,0.22) !important;
  color: #0b3a6a !important;
}
</style>
"""
st.markdown(APPLE_STYLE, unsafe_allow_html=True)

# ---------------------------
# Topbar + Hero
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
        <div class="topbar-right">Housing • Academics • Professors • Aid & Jobs</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="card" style="padding:22px 22px;">
      <div style="font-size:2.2rem; font-weight:900; letter-spacing:-0.03em;">UCSB tools, in one place.</div>
      <div class="small-muted" style="margin-top:6px;">
        Find housing, plan classes, check professors, and navigate aid & jobs — faster.
      </div>
    </div>
    <div class="section-gap"></div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Sidebar (clean)
# ---------------------------
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

st.sidebar.divider()
st.sidebar.markdown("### 📊 Data Status")

db_exists = os.path.exists("gauchoGPT.db")
csv_exists = os.path.exists("major_courses_by_quarter.csv")

if db_exists:
    st.sidebar.success("✅ Course database active")

    import sqlite3
    try:
        conn = sqlite3.connect("gauchoGPT.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(scraped_at) FROM course_offerings")
        last_update = cursor.fetchone()[0]
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
        if st.button("🔄 Run Scraper", type="primary", use_container_width=True):
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

# ---------------------------
# HOUSING — CSV-backed listings
# ---------------------------
HOUSING_CSV = "iv_housing_listings.csv"


def load_housing_df() -> Optional[pd.DataFrame]:
    """Load and lightly clean the housing CSV."""
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

    if "pet_friendly" in df.columns:
        df["pet_friendly"] = df["pet_friendly"].fillna(False).astype(bool)
    else:
        df["pet_friendly"] = False

    df["price_per_person"] = df.apply(
        lambda row: row["price"] / row["max_residents"]
        if pd.notnull(row["price"]) and pd.notnull(row["max_residents"]) and row["max_residents"] > 0
        else None,
        axis=1,
    )

    return df


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

    # Filters card
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
        bedroom_choice = st.selectbox(
            "Bedrooms",
            ["Any", "Studio", "1", "2", "3", "4", "5+"],
            index=0,
        )

    with col_f3:
        status_choice = st.selectbox(
            "Status",
            ["Available only", "All statuses", "Processing only", "Leased only"],
            index=0,
        )

    with col_f4:
        pet_choice = st.selectbox(
            "Pets",
            ["Any", "Only pet-friendly", "No pets allowed"],
            index=0,
        )

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
            • Price ≤ <span class="pill pill-blue">${price_limit:,}</span>
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

    # Listing cards
    for _, row in filtered.sort_values(["street", "unit"]).iterrows():
        street = row.get("street", "")
        unit = row.get("unit", "")
        price = row.get("price", None)
        bd = row.get("bedrooms", None)
        ba = row.get("bathrooms", None)
        max_res = row.get("max_residents", None)
        utilities = row.get("utilities", "")
        pet_policy = row.get("pet_policy", "")
        pet_friendly = bool(row.get("pet_friendly", False))
        avail_start = row.get("avail_start", "")
        avail_end = row.get("avail_end", "")
        status = (row.get("status") or "available").lower()
        is_studio = bool(row.get("is_studio", False))
        ppp = row.get("price_per_person", None)

        if status == "available":
            status_text = f"Available {avail_start}–{avail_end} (applications open)"
            status_class = "status-ok"
        elif status == "processing":
            status_text = "Processing applications"
            status_class = "status-warn"
        elif status == "leased":
            status_text = f"Currently leased (through {avail_end})" if avail_end else "Currently leased"
            status_class = "status-muted"
        else:
            status_text = status
            status_class = "status-muted"

        bed_label = "Studio" if is_studio else f"{int(bd) if pd.notna(bd) else '?'} bed"

        if pd.notna(ba):
            ba_label = f"{int(ba)} bath" if float(ba).is_integer() else f"{ba} bath"
        else:
            ba_label = "? bath"

        residents_label = f"Up to {int(max_res)} residents" if pd.notna(max_res) else "Max residents: ?"

        price_text = f"${int(price):,}/installment" if pd.notna(price) else "Price not listed"
        ppp_text = f"≈ ${ppp:,.0f} per person" if ppp is not None else ""

        pet_label = pet_policy or ("Pet friendly" if pet_friendly else "No pets info")

        st.markdown(
            f"""
            <div class="card">
              <div class="listing-title">{street}</div>
              <div class="listing-sub">{unit}</div>

              <div class="pills">
                <span class="pill">{bed_label}</span>
                <span class="pill">{ba_label}</span>
                <span class="pill">{residents_label}</span>
                <span class="pill">{pet_label}</span>
              </div>

              <div style="margin-top:10px;">
                <div class="{status_class}">{status_text}</div>
                <div style="margin-top:6px; font-weight:900; font-size:1.05rem;">
                  {price_text}
                  <span style="color:#6e6e73; font-weight:650;">{(" · " + ppp_text) if ppp_text else ""}</span>
                </div>
                {f"<div class='small-muted' style='margin-top:6px;'>Included utilities: {utilities}</div>" if utilities else ""}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-gap"></div>
        <div class="card-tight">
          <div class="small-muted">
            Note: This is a manually curated CSV snapshot based on ivproperties.com.
            Always verify current availability and pricing directly with the property manager.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------
# PROFESSORS (RMP + dept)
# ---------------------------
DEPT_SITES = {
    "PSTAT": "https://www.pstat.ucsb.edu/people",
    "CS": "https://www.cs.ucsb.edu/people/faculty",
    "MATH": "https://www.math.ucsb.edu/people/faculty",
}


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

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
          <div style="font-weight:900; font-size:1.05rem;">What to look for</div>
          <div class="small-muted" style="margin-top:8px;">
            • Syllabi from prior quarters (grading, workload, curve)<br/>
            • RMP comments: focus on <strong>recent</strong> terms & specific anecdotes<br/>
            • Department Discord/Slack/Reddit for up-to-date tips<br/>
            • Ask students who took the course last quarter
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------
# FINANCIAL AID & JOBS
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
        <div class="card">
          <div style="font-size:1.35rem; font-weight:900; letter-spacing:-0.02em;">Financial aid, work-study & jobs</div>
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

    with st.expander("How to get a job quickly"):
        st.markdown(
            """
            1) Set up your Handshake profile + upload a resume  
            2) Filter by On-campus or Work-study eligible  
            3) Apply to 5–10 postings and follow up  
            4) Ask department offices about openings  
            5) Consider research assistant roles if you have relevant skills
            """
        )

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Quick links")
    cols = st.columns(4)
    items = list(AID_LINKS.items())
    for i, (label, url) in enumerate(items):
        with cols[i % 4]:
            st.link_button(label, url)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Q&A placeholder
# ---------------------------
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
        st.info("Connect to an API (e.g., OpenAI, Anthropic) or a local model here.")
        st.code(
            """
import os
# Example sketch (pseudocode):
# from openai import OpenAI
# client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
# resp = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[{"role": "user", "content": prompt}],
# )
# st.write(resp.choices[0].message.content)
            """,
            language="python",
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# Modern “word-box” navigation (symmetric)
# ---------------------------
PAGES: Dict[str, Any] = {
    "🏠 Housing": housing_page,
    "📚 Academics": academics_page,
    "👩‍🏫 Professors": profs_page,
    "💸 Aid & Jobs": aid_jobs_page,
    "💬 Q&A": qa_page,
}

# Default nav state
if "main_nav" not in st.session_state:
    st.session_state["main_nav"] = "🏠 Housing"

st.markdown('<div class="card">', unsafe_allow_html=True)

labels = list(PAGES.keys())
cols = st.columns(len(labels))

for i, label in enumerate(labels):
    is_active = (st.session_state["main_nav"] == label)
    cls = "nav-chip-active" if is_active else "nav-chip"
    with cols[i]:
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{label}", use_container_width=True):
            st.session_state["main_nav"] = label
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# Render selected page
PAGES[st.session_state["main_nav"]]()
# Optional: if you want the sidebar “Next steps” only, delete this card.
st.markdown(
    """
    <div class="section-gap"></div>
    <div class="card">
      <div style="font-weight:900; font-size:1.05rem;">Next steps</div>
      <div class="small-muted" style="margin-top:8px;">
        • Keep housing CSV updated as availability changes<br/>
        • Add non-available units with correct status (processing / leased)<br/>
        • Expand to more property managers or data sources<br/>
        • Fill in <code>major_courses_by_quarter.csv</code> for classes by major & quarter<br/>
        • Connect an LLM for the Q&A tab
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
**Next steps (quick)**
- Keep CSV updated
- Configure scraper selectors
- Connect LLM for Q&A
"""
)

