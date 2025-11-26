# gauchoGPT — Streamlit GOLD-themed MVP
# ------------------------------------------------------------
# Main app file
# ------------------------------------------------------------
from __future__ import annotations
import os
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

# 🔹 import Academics tab from separate file
from academics import academics_page

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
    [data-testid="stAppViewContainer"] { background: #ffffff; }
    h1, h2, h3, h4 {
        color: #003660;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body, p, label, span, div {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .gold-topbar {
        width: 100%;
        background: #003660;
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
    .gold-topbar-right { font-weight: 500; opacity: 0.9; }
    .gold-nav-wrapper {
        width: 100%;
        background: #FDB515;
        padding: 4px 24px 0 24px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.15);
        margin-bottom: 12px;
    }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] { gap: 0; }
    [data-testid="stHorizontalBlock"] [role="radiogroup"] label {
        cursor: pointer;
        padding: 10px 24px;
        border-radius: 0;
        border: none;
        background: transparent;
        color: #374151;
        margin-right: 16px;
    }
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
    [data-testid="stSidebar"] * { color: #111827 !important; }
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
st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

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

    df["pet_friendly"] = df["pet_friendly"].astype(bool)

    df["price_per_person"] = df.apply(
        lambda row: row["price"] / row["max_residents"]
        if pd.notnull(row["price"]) and pd.notnull(row["max_residents"]) and row["max_residents"] > 0
        else None,
        axis=1,
    )

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

    status_choice_lower = status_choice.lower()
    if status_choice_lower.startswith("available"):
        filtered = filtered[filtered["status"] == "available"]
    elif status_choice_lower.startswith("processing"):
        filtered = filtered[filtered["status"] == "processing"]
    elif status_choice_lower.startswith("leased"):
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

        if is_studio:
            bed_label = "Studio"
        else:
            bed_label = f"{int(bd) if not pd.isna(bd) else '?'} bed"

        if not pd.isna(ba):
            if float(ba).is_integer():
                ba_label = f"{int(ba)} bath"
            else:
                ba_label = f"{ba} bath"
        else:
            ba_label = "? bath"

        residents_label = f"Up to {int(max_res)} residents" if not pd.isna(max_res) else "Max residents: ?"

        if not pd.isna(price):
            price_text = f"${int(price):,}/installment"
        else:
            price_text = "Price not listed"

        ppp_text = f"≈ ${ppp:,.0f} per person" if ppp is not None else ""

        st.markdown("---")
        st.markdown(f"### {street}")
        st.markdown(f"**{unit}**")

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
    "Academics": academics_page,  # from academics.py
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
    label_visibility="collapsed",
)
st.markdown("</div>", unsafe_allow_html=True)

PAGES[choice]()

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
