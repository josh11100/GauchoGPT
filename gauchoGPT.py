# gauchoGPT — Streamlit GOLD-themed MVP
# ------------------------------------------------------------
# A single-file Streamlit web app to help UCSB students with:
# - Housing in Isla Vista (scraper for ivproperties Isla Vista page)
# - Academic advising quick links (major sheets / prereqs — placeholders)
# - Class/location helper with campus map pins
# - Professor info shortcuts (RateMyProfessors + UCSB departmental pages)
# - Financial aid & jobs FAQs (with handy links)
# ------------------------------------------------------------

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

try:
    from streamlit_folium import st_folium
    import folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="gauchoGPT — UCSB helper",
    page_icon="🧢",
    layout="wide"
)

# ---------------------------
# UCSB GOLD theme + style helpers
# ---------------------------
HIDE_STREAMLIT_STYLE = """
<style>
    /* ------- App background + base text ------- */
    [data-testid="stAppViewContainer"] {
        background: #ffffff;
    }
    h1, h2, h3, h4 {
        color: #003660; /* UCSB navy */
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body, p, label, span, div {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* ------- Top GOLD-style header bar ------- */
    .gold-topbar {
        width: 100%;
        background: #003660; /* deep navy */
        color: #ffffff;
        padding: 10px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.95rem;
        box-shadow: 0 2px 4px rgba(15,23,42,0.25);
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    .gold-topbar-left {
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .gold-topbar-right {
        font-weight: 500;
        opacity: 0.9;
    }

    /* ------- Second bar: GOLD navigation tabs (horizontal radio in main area) ------- */
    .gold-nav-wrapper {
        width: 100%;
        background: #FDB515; /* UCSB gold */
        padding: 4px 24px 0 24px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.15);
        margin-bottom: 12px;
    }

    /* Make the radio look like GOLD tabs (hide circles, style labels) */
    [data-testid="stHorizontalBlock"] [role="radiogroup"] {
        gap: 0;
    }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] label {
        cursor: pointer;
        padding: 10px 22px;
        border-radius: 0;
        border: none;
        background: #F6C453;   /* light-ish gold */
        color: #111827;
        margin-right: 0;
    }
    /* remove the default radio circles */
    [data-testid="stHorizontalBlock"] [role="radio"] > div:first-child {
        display: none;
    }
    [data-testid="stHorizontalBlock"] [role="radio"] p {
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0;
    }
    [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] {
        background: #FBBF24;
        box-shadow: inset 0 -3px 0 0 #D97706;
    }
    [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] p {
        color: #003660;
    }

    /* ------- Sidebar: light column like GOLD left section ------- */
    [data-testid="stSidebar"] {
        background: #f3f4f6;
        border-right: 1px solid #d1d5db;
        min-width: 260px;
        max-width: 280px;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    [data-testid="stSidebar"] * {
        color: #111827 !important;
    }

    /* ------- Buttons in GOLD/NAVY ------- */
    .stButton > button, .st-link-button {
        border-radius: 9999px;
        border-width: 0;
        padding: 0.35rem 1.05rem;
        font-weight: 600;
        background: #003660;
        color: #ffffff;
        box-shadow: 0 3px 8px rgba(15,23,42,0.25);
    }
    .stButton > button:hover, .st-link-button:hover {
        background: #FDB515;
        color: #111827;
    }

    /* ------- Tables / cards look closer to GOLD ------- */
    .stDataFrame thead tr th {
        background-color: #003660 !important;
        color: #f9fafb !important;
    }

    .small {font-size: 0.85rem; color: #4b5563;}
    .muted {color:#6b7280;}
    .pill {
        display:inline-block;
        padding:4px 10px;
        border-radius:9999px;
        background:#e5e7eb;
        color:#003660;
        font-weight:600;
        margin-right:8px;
    }
    .tag  {
        display:inline-block;
        padding:2px 8px;
        border-radius:9999px;
        background:#eff6ff;
        color:#1d4ed8;
        font-weight:500;
        margin-right:6px
    }
    .code {
        font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        background:#0b1021;
        color:#d1e1ff;
        padding:3px 6px;
        border-radius:6px
    }
    .ok   {color:#059669; font-weight:600}
    .warn {color:#b45309; font-weight:600}
    .err  {color:#b91c1c; font-weight:700}

    /* Expander headers hover */
    [data-testid="stExpander"] > summary:hover {
        color: #003660;
    }
</style>
"""

st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

# GOLD-style header bar (like UCSB GOLD)
st.markdown(
    """
    <div class="gold-topbar">
        <div class="gold-topbar-left">UCSB Gaucho On-Line Data</div>
        <div class="gold-topbar-right">gauchoGPT · UCSB Student Helper</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar info
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing • classes • professors • aid • jobs")

# ---------------------------
# Utilities
# ---------------------------
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0 Safari/537.36"
)

def fetch(url: str, *, timeout: int = 20) -> Optional[requests.Response]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        if r.status_code == 200:
            return r
        st.warning(f"Request to {url} returned status {r.status_code}")
        return None
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

# ---------------------------
# HOUSING (static CSV from IV Properties 2026–27)
# ---------------------------

HOUSING_CSV = "iv_housing_2026_27.csv"


@st.cache_data
def load_housing() -> pd.DataFrame:
    """Load the local IV housing snapshot."""
    df = pd.read_csv(HOUSING_CSV)

    # force numeric types where we care about filtering
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")
    df["pet_friendly"] = df["pet_friendly"].astype(bool)

    return df


def housing_page():
    st.header("🏠 Isla Vista Housing (beta)")
    st.caption(
        "Data loaded from a local snapshot of IV Properties' Isla Vista page "
        "for the 2026–27 term. Always verify details with the property manager."
    )

    df = load_housing()

    # ---- filters ----
    col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
    with col_a:
        q = st.text_input(
            "Search keyword (optional)",
            placeholder="Del Playa, Pasado, studio…",
        )
    with col_b:
        max_price = st.number_input(
            "Max $/mo (optional)",
            min_value=0,
            value=0,
            step=100,
        )
    with col_c:
        beds = st.selectbox(
            "Bedrooms",
            ["Any", "Studio", "1", "2", "3", "4+"],
            index=0,
        )
    with col_d:
        pet = st.selectbox(
            "Pet policy",
            ["Any", "Pet friendly only", "No pets only"],
            index=0,
        )

    st.markdown(
        """
        <div class='small muted'>
        <span class='pill'>Source</span>
        iv_housing_2026_27.csv (snapshot) · Always confirm price & availability with the property manager.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- apply filters ----
    filtered = df.copy()

    # keyword against street + unit
    if q:
        q_lower = q.lower()
        mask = (
            filtered["street"].str.lower().str.contains(q_lower)
            | filtered["unit"].str.lower().str.contains(q_lower)
        )
        filtered = filtered[mask]

    # price filter
    if max_price:
        filtered = filtered[filtered["price"] <= max_price]

    # bedroom filter
    if beds != "Any":
        if beds == "Studio":
            filtered = filtered[filtered["bedrooms"] == 0]
        elif beds == "4+":
            filtered = filtered[filtered["bedrooms"] >= 4]
        else:
            filtered = filtered[filtered["bedrooms"] == int(beds)]

    # pet policy filter
    if pet == "Pet friendly only":
        filtered = filtered[filtered["pet_friendly"] == True]
    elif pet == "No pets only":
        filtered = filtered[filtered["pet_friendly"] == False]

    if filtered.empty:
        st.info(
            "No matching results in the local snapshot. "
            "Try loosening your filters or updating the CSV."
        )
        return

    # table view
    st.dataframe(
        filtered[
            [
                "street",
                "unit",
                "price",
                "bedrooms",
                "bathrooms",
                "max_residents",
                "utilities",
                "pet_policy",
            ]
        ],
        use_container_width=True,
    )

    # nice bullet list view
    st.subheader("Listings")
    for _, r in filtered.iterrows():
        price_str = f"${int(r['price']):,}/installment"
        beds_str = f"{int(r['bedrooms'])} bed" if r["bedrooms"] > 0 else "Studio"
        line = (
            f"**{r['unit']}** — {price_str} · "
            f"{beds_str} / {r['bathrooms']} bath · "
            f"Max {int(r['max_residents'])} residents  \n"
            f"{r['street']}  \n"
            f"Included utilities: {r['utilities']} · {r['pet_policy']}"
        )
        st.markdown("- " + line)

# ---------------------------
# ACADEMICS (advising quick links)
# ---------------------------
MAJOR_SHEETS = {
    "Statistics & Data Science": "https://www.pstat.ucsb.edu/undergraduate/majors-minors/stats-and-data-science-major",
    "Computer Science": "https://cs.ucsb.edu/education/undergraduate/current-students",
    "Economics": "https://econ.ucsb.edu/programs/undergraduate/majors",
    "Mathematics": "https://www.math.ucsb.edu/undergraduate/proposed-courses-study-plans",
    "Biology": "https://ucsbcatalog.coursedog.com/programs/BSBIOSC",
    "Psychology": "https://psych.ucsb.edu/undergraduate/major-requirements",
    "Chemistry": "https://undergrad.chem.ucsb.edu/academic-programs/chemistry-bs",
    "Physics": "https://www.physics.ucsb.edu/academics/undergraduate/majors",
    "Philosophy": "https://www.philosophy.ucsb.edu/undergraduate/undergraduate-major-philosophy",
    "English": "https://www.english.ucsb.edu/undergraduate/for-majors/requirements/",
}

def academics_page():
    st.header("🎓 Academics — advising quick links")
    st.caption(
        "Every major has its own plan sheet / prereqs. These are placeholders — swap with official UCSB links."
    )

    col1, col2 = st.columns([1.2, 2])
    with col1:
        major = st.selectbox("Select a major", list(MAJOR_SHEETS.keys()))
        st.link_button("Open major planning page", MAJOR_SHEETS[major])
        st.divider()

        st.subheader("Most asked questions")

        with st.expander("Still lost on what classes to take?"):
            st.markdown(
                """
                Talk to your department’s advisor. Using the **Open major planning page** button
                above, you should be able to find official advising info and schedule an appointment.
                """
            )

        with st.expander("Can’t find your specific major on this site?"):
            st.markdown(
                """
                Go to the **Help / Feedback** tab in this app and send us a request so we can
                update the major list and add the correct links.
                """
            )

        with st.expander("Not sure how many classes to take in a quarter?"):
            st.markdown(
                """
                A common pattern is **1–2 heavier technical courses plus 1 lighter GE**, but always
                confirm with your advisor and check your major’s sample plan for your major.
                """
            )

        with st.expander("Class is full or waitlisted — what now?"):
            st.markdown(
                """
                Use the **GOLD waitlist**, watch for enrollment changes before the quarter starts, and
                email the instructor or department to ask about waitlist/add-code policies.
                """
            )

    with col2:
        st.subheader("Build your quarter (scratchpad)")
        data = st.data_editor(
            pd.DataFrame(
                [
                    {"Course": "PSTAT 120A", "Units": 4, "Type": "Major"},
                    {"Course": "MATH 6A", "Units": 4, "Type": "Support"},
                    {"Course": "GE Area D", "Units": 4, "Type": "GE"},
                ]
            ),
            use_container_width=True,
            num_rows="dynamic",
        )
        st.metric("Planned units", int(sum(data["Units"])) if not data.empty else 0)

    with st.expander("🔗 Add more official links"):
        st.write("Paste your department URLs here for quick access in future iterations.")

# ---------------------------
# CLASS LOCATION (map)
# ---------------------------
BUILDINGS = {
    "Phelps Hall (PHELP)": (34.41239, -119.84862),
    "Harold Frank Hall (HFH)": (34.41434, -119.84246),
    "Chemistry (CHEM)": (34.41165, -119.84586),
    "HSSB": (34.41496, -119.84571),
    "Library": (34.41388, -119.84627),
    "IV Theater": (34.41249, -119.86155),
}

def locator_page():
    st.header("🗺️ Quick class locator")
    bname = st.selectbox("Choose a building", list(BUILDINGS.keys()))
    lat, lon = BUILDINGS[bname]

    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=16, control_scale=True)
        folium.Marker([lat, lon], tooltip=bname).add_to(m)
        st_folium(m, width=900, height=500)
    else:
        st.info(
            "Install folium + streamlit-folium for the interactive map:\n"
            "`pip install folium streamlit-folium`"
        )
        st.write({"building": bname, "lat": lat, "lon": lon})

    st.caption("Tip: A future version could load your GOLD schedule and auto-pin buildings.")

# ---------------------------
# PROFESSORS (RMP + dept)
# ---------------------------
DEPT_SITES = {
    "PSTAT": "https://www.pstat.ucsb.edu/people",
    "CS": "https://www.cs.ucsb.edu/people/faculty",
    "MATH": "https://www.math.ucsb.edu/people/faculty",
}

def profs_page():
    st.header("👩‍🏫 Professors & course intel")
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

    st.divider()
    st.subheader("What to look for")
    st.markdown(
        """
        - Syllabi from prior quarters (grading, workload, curve)  
        - RMP comments: focus on **recent** terms and specific anecdotes  
        - Department Discord/Slack/Reddit for up-to-date tips  
        - Talk to students who recently took the course
        """
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
    st.header("💸 Financial aid, work-study & jobs")

    with st.expander("What is financial aid?"):
        st.write(
            """
            Financial aid reduces your cost of attendance via grants, scholarships, work-study, and loans.
            File the **FAFSA** (or CADAA if applicable) as early as possible each year. Watch priority deadlines.
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
            1. Set up your **Handshake** profile and upload your resume.  
            2. Filter by *On-campus* or *Work-study eligible*.  
            3. Apply to 5–10 postings and follow up.  
            4. Visit department offices; ask about openings.  
            5. Consider research assistant roles if you have relevant skills.
            """
        )

    st.subheader("Quick links")
    for label, url in AID_LINKS.items():
        st.link_button(label, url)

# ---------------------------
# Q&A placeholder
# ---------------------------
def qa_page():
    st.header("💬 Ask gauchoGPT (placeholder)")
    st.caption("Wire this to your preferred LLM API or a local model.")

    prompt = st.text_area(
        "Ask a UCSB question",
        placeholder="e.g., How do I switch into the STAT&DS major?"
    )
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

# ---------------------------
# GOLD-style main navigation
# ---------------------------
PAGES: Dict[str, Any] = {
    "Housing (IV)": housing_page,
    "Academics": academics_page,
    "Class Locator": locator_page,
    "Professors": profs_page,
    "Aid & Jobs": aid_jobs_page,
    "Q&A (WIP)": qa_page,
}

st.markdown('<div class="gold-nav-wrapper">', unsafe_allow_html=True)
choice = st.radio(
    "Main navigation",
    list(PAGES.keys()),
    horizontal=True,
    index=0,
    key="main_nav",
)
st.markdown("</div>", unsafe_allow_html=True)

# Render selected page
PAGES[choice]()

# Sidebar helper text (like GOLD help/info column)
st.sidebar.divider()
st.sidebar.markdown(
    """
**Next steps**
- Swap placeholder links with official UCSB URLs you trust.  
- Tighten up the Isla Vista parser (add more fields, caching, error handling).  
- Connect an LLM for the Q&A tab.
"""
)

