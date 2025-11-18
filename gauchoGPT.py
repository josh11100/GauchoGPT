# gauchoGPT — Streamlit GOLD-themed MVP (CSV snapshot version)
# ------------------------------------------------------------
# A Streamlit app to help UCSB students with:
# - Isla Vista housing (from a local CSV snapshot of IV Properties)
# - Academic advising quick links
# - Class/location helper with campus map pins
# - Professor info shortcuts (RMP + department pages)
# - Financial aid & jobs quick links
# - Q&A (placeholder to connect an LLM later)
# ------------------------------------------------------------

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import pandas as pd
import streamlit as st

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

    /* Treat the horizontal radio like GOLD-style tabs */
    [data-testid="stHorizontalBlock"] [role="radiogroup"] {
        gap: 0;
    }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] label {
        cursor: pointer;
        padding: 8px 22px;
        border-radius: 0;
        border: 1px solid rgba(15,23,42,0.18);
        border-bottom: none;
        background: #FDE68A;   /* light gold */
        color: #111827;
        margin-right: 0;
    }
    [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] {
        background: #ffffff;
        border-bottom: 3px solid #ffffff;
        box-shadow: 0 -2px 0 0 #ffffff;
    }
    [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] p {
        color: #003660;
        font-weight: 700;
    }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] label p {
        font-size: 0.88rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
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

    /* DataFrame header */
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
        margin-right:6px;
    }
    .code {
        font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        background:#0b1021;
        color:#d1e1ff;
        padding:3px 6px;
        border-radius:6px;
    }
    .ok   {color:#059669; font-weight:600;}
    .warn {color:#b45309; font-weight:600;}
    .err  {color:#4b5563; font-weight:600;}

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

# Sidebar info (not used for nav anymore)
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing • classes • professors • aid • jobs")

# ============================================================
# HOUSING (CSV snapshot from ivproperties.com)
# ============================================================

CSV_FILENAME = "iv_housing_listings.csv"


@st.cache_data(show_spinner=False)
def load_housing_csv() -> Optional[pd.DataFrame]:
    """Load local housing snapshot CSV if present."""
    if not os.path.exists(CSV_FILENAME):
        return None

    df = pd.read_csv(CSV_FILENAME)

    # Basic clean-up / type casting
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

    for col in ("bedrooms", "bathrooms", "max_residents"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "pet_friendly" in df.columns:
        # Coerce to bool
        df["pet_friendly"] = df["pet_friendly"].astype(str).str.lower().isin(
            ["true", "1", "yes", "y"]
        )

    if "status" in df.columns:
        df["status"] = df["status"].str.lower().str.strip()
    else:
        # If status column is missing, treat everything as "available"
        df["status"] = "available"

    if "is_studio" not in df.columns:
        df["is_studio"] = False

    return df


def format_status_row(row: pd.Series) -> str:
    """Return HTML snippet for the status line, with the right color."""
    status = (row.get("status") or "").lower()

    avail_start = row.get("avail_start") or ""
    avail_end = row.get("avail_end") or ""

    if status == "available":
        # Green + dates
        date_text = ""
        if avail_start and avail_end:
            date_text = f"{avail_start}–{avail_end}"
        elif avail_start:
            date_text = avail_start
        if date_text:
            msg = f"Available {date_text} (applications open)"
        else:
            msg = "Available (applications open)"

        return f"<span class='ok'>{msg}</span>"

    if status == "processing":
        return "<span class='warn'>Processing applications</span>"

    if status == "leased":
        # Grey
        msg = "Currently leased"
        if avail_end:
            msg += f" through {avail_end}"
        return f"<span class='err'>{msg}</span>"

    # Fallback if status is unknown
    return f"<span class='small muted'>{row.get('status', 'Status unknown')}</span>"


def housing_page():
    st.header("🏡 Isla Vista Housing (CSV snapshot)")
    st.caption(
        "Snapshot of selected Isla Vista units from ivproperties.com for the 2026–27 lease term. "
        "Filters below help you find fits by price, bedrooms, status, and pet policy."
    )

    df = load_housing_csv()
    if df is None or df.empty:
        st.error(
            f"Missing CSV file: **{CSV_FILENAME}**. "
            "Place it next to `gauchoGPT.py` and reload the app."
        )
        st.info("No housing data found in the CSV.")
        return

    # --------------------------------------------------------
    # Filter controls
    # --------------------------------------------------------
    max_price_default = float(df["price"].dropna().max() or 12000)
    max_price = st.slider(
        "Max monthly installment",
        min_value=0.0,
        max_value=max_price_default,
        value=max_price_default,
        step=100.0,
    )

    # bedrooms choices
    bedroom_values = sorted(df["bedrooms"].dropna().unique().tolist())
    bedroom_labels = ["Any"]
    bedroom_map = {"Any": None}
    for b in bedroom_values:
        if int(b) == 0:
            label = "Studio"
        else:
            label = f"{int(b)}"
        bedroom_labels.append(label)
        bedroom_map[label] = int(b)

    selected_bed_label = st.selectbox("Bedrooms", bedroom_labels, index=0)
    selected_bedrooms = bedroom_map[selected_bed_label]

    # status filter – uses normalized string statuses
    status_options = [
        "Available only",
        "Processing applications only",
        "Currently leased only",
        "Any status",
    ]
    status_choice = st.selectbox("Status filter", status_options, index=0)

    # pet policy filter
    pet_options = ["Any", "Pet friendly only", "No pets only"]
    pet_choice = st.selectbox("Pet policy", pet_options, index=0)

    # --------------------------------------------------------
    # Apply filters
    # --------------------------------------------------------
    filtered = df.copy()

    filtered = filtered[filtered["price"] <= max_price]

    if selected_bedrooms is not None:
        filtered = filtered[filtered["bedrooms"] == selected_bedrooms]

    if status_choice == "Available only":
        filtered = filtered[filtered["status"] == "available"]
    elif status_choice == "Processing applications only":
        filtered = filtered[filtered["status"] == "processing"]
    elif status_choice == "Currently leased only":
        filtered = filtered[filtered["status"] == "leased"]
    # "Any status" → no extra filter

    if pet_choice == "Pet friendly only":
        # pet_friendly True OR pet_policy contains "pet friendly"
        if "pet_friendly" in filtered.columns:
            mask = filtered["pet_friendly"]
        else:
            mask = filtered["pet_policy"].fillna("").str.contains(
                "pet friendly", case=False
            )
        filtered = filtered[mask]

    elif pet_choice == "No pets only":
        mask = filtered["pet_policy"].fillna("").str.contains("no pets", case=False)
        filtered = filtered[mask]

    filtered = filtered.sort_values(["street", "unit"]).reset_index(drop=True)

    # Info line
    st.write(
        f"Showing **{len(filtered)}** of **{len(df)}** units · "
        f"Price ≤ **${int(max_price):,}**"
    )

    # Optional table
    with st.expander("📊 View table of filtered units"):
        show_cols = [
            c
            for c in [
                "street",
                "unit",
                "price",
                "bedrooms",
                "bathrooms",
                "max_residents",
                "utilities",
                "pet_policy",
                "status",
            ]
            if c in filtered.columns
        ]
        st.dataframe(filtered[show_cols], use_container_width=True)

    # --------------------------------------------------------
    # Card-style listing display
    # --------------------------------------------------------
    st.markdown("---")
    st.subheader("Listings")

    if filtered.empty:
        st.info("No units match these filters. Try raising the price or changing status.")
        return

    for _, row in filtered.iterrows():
        # Street as bold title
        st.markdown(f"### {row.get('street', 'Isla Vista, CA')}")

        # Unit name
        st.markdown(f"**{row.get('unit', '').strip()}**")

        # Tag row
        tags = []

        beds = row.get("bedrooms")
        if pd.notna(beds):
            if int(beds) == 0 or bool(row.get("is_studio", False)):
                tags.append("Studio")
            else:
                tags.append(f"{int(beds)} bed")

        baths = row.get("bathrooms")
        if pd.notna(baths):
            if float(baths).is_integer():
                tags.append(f"{int(baths)} bath")
            else:
                tags.append(f"{baths:g} bath")

        max_res = row.get("max_residents")
        if pd.notna(max_res):
            tags.append(f"Up to {int(max_res)} residents")

        pet_policy = str(row.get("pet_policy", "")).strip()
        if pet_policy:
            # Short pill
            if "no pets" in pet_policy.lower():
                tags.append("No pets")
            elif "pet friendly" in pet_policy.lower():
                tags.append("Pet friendly")

        if tags:
            st.markdown(
                " · ".join(f"`{t}`" for t in tags),
            )

        # Status line
        st.markdown(format_status_row(row), unsafe_allow_html=True)

        # Price + utilities line
        price = row.get("price")
        if pd.notna(price):
            st.write(f"**${int(price):,}/installment**")

        utilities = str(row.get("utilities", "")).strip()
        if utilities:
            st.caption(f"Included utilities: {utilities}")

        st.markdown("---")


# ============================================================
# ACADEMICS (advising quick links)
# ============================================================

MAJOR_SHEETS: Dict[str, str] = {
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
                Talk to your department’s advisor. Using the **Open major planning page**
                button above, you should be able to find official advising info and
                schedule an appointment.
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
                confirm with your advisor and check your major’s sample plan.
                """
            )

        with st.expander("Class is full or waitlisted — what now?"):
            st.markdown(
                """
                Use the **GOLD waitlist**, watch for enrollment changes before the quarter starts,
                and email the instructor or department to ask about waitlist/add-code policies.
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
        st.metric("Planned units", int(data["Units"].sum()) if not data.empty else 0)

    with st.expander("🔗 Add more official links"):
        st.write("Paste your department URLs here for quick access in future iterations.")


# ============================================================
# CLASS LOCATION (map)
# ============================================================

BUILDINGS: Dict[str, tuple[float, float]] = {
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
            "Install folium + streamlit-folium for the interactive map: "
            "`pip install folium streamlit-folium`"
        )
        st.write({"building": bname, "lat": lat, "lon": lon})

    st.caption("Tip: Future versions could auto-pin buildings from your GOLD schedule.")


# ============================================================
# PROFESSORS (RMP + dept)
# ============================================================

DEPT_SITES = {
    "PSTAT": "https://www.pstat.ucsb.edu/people",
    "CS": "https://www.cs.ucsb.edu/people/faculty",
    "MATH": "https://www.math.ucsb.edu/people/faculty",
}


def profs_page():
    st.header("👩‍🏫 Professors & course intel")

    name = st.text_input(
        "Professor name", placeholder="e.g., Palaniappan, Porter, Levkowitz…"
    )
    dept = st.selectbox("Department site", list(DEPT_SITES.keys()))

    col1, col2 = st.columns(2)
    with col1:
        if name:
            from urllib.parse import quote_plus

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


# ============================================================
# FINANCIAL AID & JOBS
# ============================================================

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
            Financial aid reduces your cost of attendance via grants, scholarships,
            work-study, and loans. File the **FAFSA** (or CADAA if applicable) as early
            as possible each year and watch priority deadlines.
            """
        )

    with st.expander("What is work-study?"):
        st.write(
            """
            Work-study is a need-based program that lets you earn money via part-time
            jobs on or near campus. Your award caps how much you can earn under
            work-study each year.
            """
        )

    with st.expander("How to get a job quickly"):
        st.markdown(
            """
            1. Set up your **Handshake** profile and upload a resume.  
            2. Filter by *On-campus* or *Work-study eligible*.  
            3. Apply to 5–10 postings and follow up.  
            4. Visit department offices and ask about openings.  
            5. Consider research assistant roles if you have relevant skills.
            """
        )

    st.subheader("Quick links")
    for label, url in AID_LINKS.items():
        st.link_button(label, url)


# ============================================================
# Q&A placeholder
# ============================================================

def qa_page():
    st.header("💬 Ask gauchoGPT (placeholder)")
    st.caption("Wire this to your preferred LLM API or a local model in the future.")

    prompt = st.text_area(
        "Ask a UCSB question", placeholder="e.g., How do I switch into the STAT&DS major?"
    )
    if st.button("Answer"):
        st.info("Hook this up to an LLM API (OpenAI, Anthropic, etc.).")
        st.code(
            """
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


# ============================================================
# GOLD-style main navigation (horizontal tabs)
# ============================================================

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

# Render the selected page
PAGES[choice]()

# Sidebar helper text (like GOLD help/info column)
st.sidebar.divider()
st.sidebar.markdown(
    """
**Next steps**
- Keep `iv_housing_listings.csv` updated as IV Properties changes.
- Add more majors and departments you care about.
- Connect an LLM for the Q&A tab.
"""
)
