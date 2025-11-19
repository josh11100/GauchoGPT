# gauchoGPT — Streamlit GOLD-themed MVP
# ------------------------------------------------------------
# A single-file Streamlit web app to help UCSB students with:
# - Housing in Isla Vista (CSV-backed listings from ivproperties.com)
# - Academic advising quick links (major sheets / prereqs — placeholders)
# - Class/location helper with campus map pins
# - Professor info shortcuts (RateMyProfessors + UCSB departmental pages)
# - Financial aid & jobs FAQs (with handy links)
# ------------------------------------------------------------

from __future__ import annotations
import os
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
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
    layout="wide",
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

    /* This targets the the horizontal radio group we use for main nav */
    [data-testid="stHorizontalBlock"] [role="radiogroup"] {
        gap: 0;
    }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] label {
        cursor: pointer;
        padding: 10px 24px;
        border-radius: 0;
        border: none;
        background: transparent;
        color: #374151; /* slate */
        margin-right: 16px;
    }
    /* hide the actual radio circle in the top nav */
    [data-testid="stHorizontalBlock"] [role="radio"] > div:first-child {
        display: none !important;
    }
    [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] {
        background: transparent;
        border-bottom: 3px solid #ffffff;
        box-shadow: none;
    }
    [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] p {
        color: #003660;
        font-weight: 700;
    }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] label p {
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0;
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

    /* ------- Buttons in GOLD/NAVY (general buttons, NOT top nav) ------- */
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

# Sidebar info (not main nav anymore)
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

# ---------------------------
# HOUSING — CSV-backed listings
# ---------------------------
HOUSING_CSV = "iv_housing_listings.csv"  # <- make sure this file exists in the same folder

# ---------------------------
# ACADEMICS — classes by quarter (CSV)
# ---------------------------
COURSES_CSV = "major_courses_by_quarter.csv"  # <- new CSV for classes by major & quarter


def load_housing_df() -> Optional[pd.DataFrame]:
    """Load and lightly clean the housing CSV."""
    if not os.path.exists(HOUSING_CSV):
        st.error(f"Missing CSV file: {HOUSING_CSV}. Place it next to gauchoGPT.py.")
        return None

    df = pd.read_csv(HOUSING_CSV)

    # Ensure expected columns exist (with safe defaults)
    for col in [
        "street", "unit", "avail_start", "avail_end",
        "price", "bedrooms", "bathrooms", "max_residents",
        "utilities", "pet_policy", "pet_friendly",
    ]:
        if col not in df.columns:
            df[col] = None

    # Optional / new columns
    if "status" not in df.columns:
        # default: treat everything as available if status not given
        df["status"] = "available"
    if "is_studio" not in df.columns:
        # infer from bedrooms==0 if present, else default False
        df["is_studio"] = df.get("bedrooms", 0).fillna(0).astype(float).eq(0)

    # Type cleaning
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["max_residents"] = pd.to_numeric(df["max_residents"], errors="coerce")

    # booleans
    df["pet_friendly"] = df["pet_friendly"].astype(bool)

    # Derived feature: price per person
    df["price_per_person"] = df.apply(
        lambda row: row["price"] / row["max_residents"]
        if pd.notnull(row["price"]) and pd.notnull(row["max_residents"]) and row["max_residents"] > 0
        else None,
        axis=1,
    )

    return df


def load_courses_df() -> Optional[pd.DataFrame]:
    """
    Load a CSV with class offerings by major and quarter.

    Expected columns (case-insensitive, but best to match exactly):
    - major            (e.g., 'Statistics & Data Science', 'Computer Science')
    - course_code      (e.g., 'PSTAT 120A')
    - title            (e.g., 'Probability and Statistics')
    - quarter          (one of: 'Fall', 'Winter', 'Spring', 'Summer')
    - units            (optional, numeric)
    - notes            (optional, text)
    """
    if not os.path.exists(COURSES_CSV):
        # We'll handle None gracefully in the Academics page
        return None

    df = pd.read_csv(COURSES_CSV)

    # Normalize column names a bit
    df.columns = [c.strip().lower() for c in df.columns]

    # Make sure minimum columns exist
    for col in ["major", "course_code", "title", "quarter"]:
        if col not in df.columns:
            st.error(f"'{COURSES_CSV}' is missing required column: '{col}'")
            return None

    # Optional columns
    if "units" not in df.columns:
        df["units"] = None
    if "notes" not in df.columns:
        df["notes"] = ""

    # Normalize quarter text
    df["quarter"] = df["quarter"].astype(str).str.strip().str.title()  # e.g., 'fall' -> 'Fall'

    return df


def housing_page():
    st.header("🏠 Isla Vista Housing (CSV snapshot)")
    st.caption(
        "Snapshot of selected Isla Vista units from ivproperties.com for the 2026–27 lease term. "
        "Filters below help you find fits by price, bedrooms, status, and pet policy."
    )

    df = load_housing_df()
    if df is None or df.empty:
        st.warning("No housing data found in the CSV.")
        return

    # ---------------- Filters ----------------
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1.5])

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
        # Bedrooms filter
        bedroom_choice = st.selectbox(
            "Bedrooms",
            ["Any", "Studio", "1", "2", "3", "4", "5+"],
            index=0,
        )

    with col_f3:
        status_choice = st.selectbox(
            "Status filter",
            ["Available only", "All statuses", "Processing only", "Leased only"],
            index=0,
        )

    with col_f4:
        pet_choice = st.selectbox(
            "Pet policy",
            ["Any", "Only pet-friendly", "No pets allowed"],
            index=0,
        )

    # ---------------- Apply filters ----------------
    filtered = df.copy()

    # Price filter
    filtered = filtered[(filtered["price"].isna()) | (filtered["price"] <= price_limit)]

    # Bedrooms / studio filter
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

    # Status filter
    status_choice_lower = status_choice.lower()
    if status_choice_lower.startswith("available"):
        filtered = filtered[filtered["status"] == "available"]
    elif status_choice_lower.startswith("processing"):
        filtered = filtered[filtered["status"] == "processing"]
    elif status_choice_lower.startswith("leased"):
        filtered = filtered[filtered["status"] == "leased"]

    # Pet filter
    if pet_choice == "Only pet-friendly":
        filtered = filtered[filtered["pet_friendly"] == True]
    elif pet_choice == "No pets allowed":
        # assume "No pets" in pet_policy means no pets
        filtered = filtered[
            (filtered["pet_friendly"] == False)
            | (filtered["pet_policy"].fillna("").str.contains("No pets", case=False))
        ]

    # ---------------- Summary / metrics ----------------
    st.markdown(
        f"""
        <div class='small muted'>
        Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> units
        • Price ≤ <span class='pill'>${price_limit:,}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.info("No units match your filters. Try raising your max price or widening status/bedroom filters.")
        return

    # Optional: small summary table
    with st.expander("📊 View table of filtered units"):
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

    # ---------------- Card-style results ----------------
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

        # Human-friendly status text
        if status == "available":
            status_text = f"Available {avail_start}–{avail_end} (applications open)"
            status_badge_class = "ok"
        elif status == "processing":
            status_text = "Processing applications"
            status_badge_class = "warn"
        elif status == "leased":
            status_text = f"Currently leased (through {avail_end})" if avail_end else "Currently leased"
            status_badge_class = "muted"
        else:
            status_text = status
            status_badge_class = "muted"

        # Bedrooms label
        if is_studio:
            bed_label = "Studio"
        else:
            bed_label = f"{int(bd) if not pd.isna(bd) else '?'} bed"

        # Bathrooms label
        if not pd.isna(ba):
            if float(ba).is_integer():
                ba_label = f"{int(ba)} bath"
            else:
                ba_label = f"{ba} bath"
        else:
            ba_label = "? bath"

        residents_label = f"Up to {int(max_res)} residents" if not pd.isna(max_res) else "Max residents: ?"

        # Price text
        if not pd.isna(price):
            price_text = f"${int(price):,}/installment"
        else:
            price_text = "Price not listed"

        ppp_text = f"≈ ${ppp:,.0f} per person" if ppp is not None else ""

        st.markdown("---")
        st.markdown(f"### {street}")
        st.markdown(f"**{unit}**")

        # Badges row
        st.markdown(
            f"""
            <div class='small'>
                <span class='pill'>{bed_label}</span>
                <span class='pill'>{ba_label}</span>
                <span class='pill'>{residents_label}</span>
                <span class='pill'>{pet_policy or ("Pet friendly" if pet_friendly else "No pets info")}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Status + pricing
        st.markdown(
            f"""
            <div class='small'>
                <span class='{status_badge_class}'>{status_text}</span><br/>
                <span class='ok'>{price_text}</span>
                {" · " + ppp_text if ppp_text else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if utilities:
            st.markdown(
                f"<div class='small muted'>Included utilities: {utilities}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.caption(
        "Note: This is a manually curated CSV snapshot based on ivproperties.com. "
        "Always verify current availability and pricing directly with the property manager."
    )

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
    "English": "https://www.english.ucsb.edu/undergraduate/for-majors/requirements/ ",
}


def academics_page():
    st.header("🎓 Academics — advising quick links")
    st.caption("Every major has its own plan sheet / prereqs. These are placeholders — swap with official UCSB links.")

    courses_df = load_courses_df()

    col1, col2 = st.columns([1.2, 2])
    with col1:
        # ---- Major planning sheet (existing) ----
        major = st.selectbox("Select a major", list(MAJOR_SHEETS.keys()))
        st.link_button("Open major planning page", MAJOR_SHEETS[major])
        st.divider()

        # ---- NEW: Classes available by quarter ----
        st.subheader("Classes available by quarter")

        if courses_df is None:
            st.caption(
                "Add a CSV named `major_courses_by_quarter.csv` in this folder to show "
                "classes by major and quarter."
            )
        else:
            quarter = st.selectbox(
                "Quarter",
                ["Fall", "Winter", "Spring", "Summer"],
                index=1,  # default to Winter
            )

            # Filter by selected major + quarter
            filtered = courses_df[
                (courses_df["major"] == major) &
                (courses_df["quarter"] == quarter)
            ]

            if filtered.empty:
                st.info(f"No classes listed for **{major}** in **{quarter}** in your CSV yet.")
            else:
                st.dataframe(
                    filtered[["course_code", "title", "units", "notes"]],
                    use_container_width=True,
                )

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
        st.markdown(
            """
            Paste your department URLs here for quick access in future iterations.
            """
        )

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
        st.info("Install folium + streamlit-folium for the interactive map: pip install folium streamlit-folium")
        st.write({"building": bname, "lat": lat, "lon": lon})

    st.caption("Tip: You can load your full schedule and auto-pin buildings in a future version.")

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
        - RMP comments: look for **recent** terms and specific anecdotes
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
            1) Set up your **Handshake** profile, upload resume.
            2) Filter by *On-campus* or *Work-study eligible*.
            3) Apply to 5–10 postings and follow up.
            4) Visit department offices; ask about openings.
            5) Consider research assistant roles if you have relevant skills.
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

# ---------------------------
# GOLD-style main navigation (horizontal, like GOLD tabs)
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
    "Main navigation",  # visually styled as GOLD tabs by CSS above
    list(PAGES.keys()),
    horizontal=True,
    index=0,
    key="main_nav",
    label_visibility="collapsed",
)
st.markdown("</div>", unsafe_allow_html=True)

# Render the selected page
PAGES[choice]()

# Sidebar helper text (like GOLD help/info column)
st.sidebar.divider()
st.sidebar.markdown(
    """
**Next steps**
- Keep the housing CSV updated as availability changes.
- Add non-available units with correct `status` (processing / leased).
- Expand to more property managers or data sources.
- Fill in `major_courses_by_quarter.csv` for classes by major & quarter.
- Connect an LLM for the Q&A tab.
"""
)
