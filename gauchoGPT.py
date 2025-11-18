# gauchoGPT — Streamlit GOLD-themed MVP
# ------------------------------------------------------------
# A single-file Streamlit web app to help UCSB students with:
# - Housing in Isla Vista (Isla Vista Properties 2026-27 page)
# - Academic advising quick links (major sheets / prereqs — placeholders)
# - Class/location helper with campus map pins
# - Professor info shortcuts (RateMyProfessors + UCSB departmental pages)
# - Financial aid & jobs FAQs (with handy links)
# ------------------------------------------------------------

from __future__ import annotations
import os
import re
import time
import math
import json
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

    /* ------- Second bar: GOLD navigation tabs ------- */
    .gold-nav-wrapper {
        width: 100%;
        background: #FDB515; /* UCSB gold */
        padding: 0 24px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.15);
        margin-bottom: 12px;
    }

    /* Hide the "Main navigation" label text */
    .gold-nav-wrapper [data-testid="stRadio"] > label {
        display: none;
    }

    /* Layout the horizontal radio like a tab row */
    .gold-nav-wrapper [data-testid="stHorizontalBlock"] {
        padding-top: 4px;
        padding-bottom: 0;
    }

    .gold-nav-wrapper [data-testid="stHorizontalBlock"] [role="radiogroup"] {
        gap: 0;
        display: flex;
    }

    /* Hide the default radio input dots */
    .gold-nav-wrapper input[type="radio"] {
        display: none !important;
    }

    /* Base tab style */
    .gold-nav-wrapper [data-testid="stHorizontalBlock"] [role="radio"] {
        border-radius: 0;
        border: none;
        background: #FDE68A; /* light gold */
        padding: 10px 22px;
        margin: 0;
        box-shadow: none;
        cursor: pointer;
    }

    /* Label text inside tabs */
    .gold-nav-wrapper [data-testid="stHorizontalBlock"] [role="radio"] p {
        font-size: 0.86rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #374151;
        margin: 0;
    }

    /* Active tab (aria-checked=true) */
    .gold-nav-wrapper [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] {
        background: #ffffff;
        box-shadow: 0 -2px 0 0 #ffffff;
        border-top: 2px solid #003660;
        border-left: 1px solid rgba(15,23,42,0.18);
        border-right: 1px solid rgba(15,23,42,0.18);
    }
    .gold-nav-wrapper [data-testid="stHorizontalBlock"] [role="radio"][aria-checked="true"] p {
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

# Sidebar info (not main nav anymore)
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

def fetch(url: str, *, timeout: int = 15) -> Optional[requests.Response]:
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
# HOUSING (Isla Vista Properties 2026–27)
# ---------------------------

@dataclass
class Listing:
    title: str
    address: str
    price: str
    beds: str
    baths: str
    max_residents: str
    status: str
    utilities: str
    pet_friendly: Optional[bool]
    link: str

IVP_ISLA_VISTA_URL = "https://www.ivproperties.com/properties/isla-vista-properties/"

BEDROOM_RE = re.compile(r"(\d+(?:\.\d+)?)\s+bedroom", re.IGNORECASE)
BATHROOM_RE = re.compile(r"(\d+(?:\.\d+)?)\s+bathroom", re.IGNORECASE)
MAX_RES_RE = re.compile(r"(?:Maximum\s+|)(\d+)\s+residents?", re.IGNORECASE)
PRICE_RE = re.compile(r"\$([\d,]+)")

def _parse_listing_from_block(
    street: str,
    unit_title: str,
    block_text: List[str],
    link: str
) -> Listing:
    """Given the street, unit title, and list of text lines, build a Listing."""
    # Clean lines
    lines = [ln.strip() for ln in block_text if ln.strip()]
    full_text = " ".join(lines)

    status = ""
    price = ""
    beds = ""
    baths = ""
    max_residents = ""
    utilities = ""
    pet_friendly: Optional[bool] = None

    # Status: usually first non-empty line
    if lines:
        for ln in lines:
            if any(
                key in ln.lower()
                for key in ["available", "processing applications", "leased", "currently leased"]
            ):
                status = ln
                break

    # Price line
    for ln in lines:
        if "$" in ln:
            price = ln
            break

    # Beds / baths / max residents / utilities
    for ln in lines:
        if "bedroom" in ln.lower() or "studio" in ln.lower():
            beds = ln
        if "bathroom" in ln.lower():
            baths = ln
        if "resident" in ln.lower():
            max_residents = ln
        if "Included Utilities" in ln:
            utilities = ln

    # Pet friendly / No pets
    if "pet friendly" in full_text.lower():
        pet_friendly = True
    elif "no pets" in full_text.lower():
        pet_friendly = False

    return Listing(
        title=unit_title,
        address=street,
        price=price,
        beds=beds,
        baths=baths,
        max_residents=max_residents,
        status=status,
        utilities=utilities,
        pet_friendly=pet_friendly,
        link=link,
    )


def parse_isla_vista_properties(html: str) -> List[Listing]:
    """
    Parser tailored to https://www.ivproperties.com/properties/isla-vista-properties/
    It walks h2 (street) and h3 (unit) headings and collects the text lines between them.
    """
    soup = BeautifulSoup(html, "html.parser")
    listings: List[Listing] = []

    # All h2s that look like street addresses for Isla Vista housing
    for h2 in soup.find_all(["h2"]):
        street = h2.get_text(strip=True)
        if "Isla Vista" not in street and "Pasado Road" not in street and "Sueno Road" not in street:
            # quick guard — avoids header / filter sections
            continue

        # Walk forward until the next h2
        node = h2.next_sibling
        current_unit_title: Optional[str] = None
        current_block: List[str] = []
        current_link: str = ""
        saw_any_unit = False

        def flush():
            nonlocal current_unit_title, current_block, current_link, saw_any_unit
            if current_unit_title and current_block:
                listings.append(
                    _parse_listing_from_block(
                        street=street,
                        unit_title=current_unit_title,
                        block_text=current_block,
                        link=current_link,
                    )
                )
            current_unit_title = None
            current_block = []
            current_link = ""

        while node is not None:
            if getattr(node, "name", None) == "h2":
                # next property
                break

            if getattr(node, "name", None) == "h3":
                # starting a new unit
                # flush previous
                flush()
                saw_any_unit = True
                unit_title = node.get_text(strip=True)
                current_unit_title = unit_title

                # link is usually on the <a> inside the h3
                link_tag = node.find("a")
                if link_tag and link_tag.get("href"):
                    href = link_tag.get("href")
                    if href.startswith("http"):
                        current_link = href
                    else:
                        current_link = "https://www.ivproperties.com" + href
                else:
                    current_link = IVP_ISLA_VISTA_URL

            else:
                # normal content between headings
                if getattr(node, "name", None) in ("p", "li"):
                    text = node.get_text(" ", strip=True)
                    if text:
                        current_block.append(text)

            node = node.next_sibling

        # Flush last unit for this street
        flush()

        # Some properties (like single-house entries) might not have h3 units,
        # but only text under the h2. Handle that as one big "unit".
        if not saw_any_unit:
            # Collect text between h2 and next h2
            block: List[str] = []
            node2 = h2.next_sibling
            while node2 is not None and getattr(node2, "name", None) != "h2":
                if getattr(node2, "name", None) in ("p", "li"):
                    t = node2.get_text(" ", strip=True)
                    if t:
                        block.append(t)
                node2 = node2.next_sibling

            if block:
                listings.append(
                    _parse_listing_from_block(
                        street=street,
                        unit_title=street,
                        block_text=block,
                        link=IVP_ISLA_VISTA_URL,
                    )
                )

    return listings


def housing_page():
    st.header("🏠 Isla Vista Housing (beta)")
    st.caption(
        "Data pulled from IV Properties' Isla Vista page for the 2026–27 term. "
        "Always verify details with the property manager."
    )

    col_a, col_b, col_c, col_d, col_e = st.columns([2, 1, 1, 1, 1])
    with col_a:
        q = st.text_input("Search keyword (optional)", placeholder="2 bed, Del Playa, studio…")
    with col_b:
        max_price = st.number_input("Max $/mo (optional)", min_value=0, value=0, step=50)
    with col_c:
        beds = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4+"], index=0)
    with col_d:
        sublease = st.checkbox("Sublease")
    with col_e:
        fetch_btn = st.button("Fetch IVProperties")

    st.markdown(
        """
        <div class='small muted'>
        <span class='pill'>Source</span> ivproperties.com · Respect robots.txt · Use responsibly
        </div>
        """,
        unsafe_allow_html=True,
    )

    if fetch_btn:
        with st.spinner("Contacting ivproperties.com…"):
            url = IVP_ISLA_VISTA_URL
            resp = fetch(url)
            if not resp:
                return

            listings = parse_isla_vista_properties(resp.text)

            def price_to_int(p: str) -> Optional[int]:
                m = PRICE_RE.search(p)
                if not m:
                    return None
                try:
                    return int(m.group(1).replace(",", ""))
                except Exception:
                    return None

            rows = []
            for L in listings:
                p_int = price_to_int(L.price)

                # Max price filter
                if max_price and (p_int is not None) and p_int > max_price:
                    continue

                # Bedrooms filter
                if beds != "Any":
                    text = (L.beds or "").lower()
                    if beds == "Studio":
                        if "studio" not in text:
                            continue
                    elif beds == "4+":
                        m = BEDROOM_RE.search(text)
                        if not (m and float(m.group(1)) >= 4):
                            continue
                    else:
                        # "1", "2", "3" etc.
                        m = BEDROOM_RE.search(text)
                        if not (m and m.group(1) == beds):
                            continue

                # Sublease filter (site rarely uses this word but keep as placeholder)
                if sublease:
                    if "sublease" not in L.status.lower() and "sublease" not in (L.title.lower() + L.address.lower()):
                        continue

                rows.append(
                    {
                        "Title": L.title,
                        "Address": L.address,
                        "Price": L.price,
                        "Beds": L.beds,
                        "Baths": L.baths,
                        "Max Residents": L.max_residents,
                        "Status": L.status,
                        "Utilities": L.utilities,
                        "Pets": (
                            "Pet friendly" if L.pet_friendly is True
                            else "No pets" if L.pet_friendly is False
                            else ""
                        ),
                        "Link": L.link,
                    }
                )

            # Simple keyword search across a few text fields
            if q:
                q_lower = q.lower()
                rows = [
                    r for r in rows
                    if q_lower in r["Title"].lower()
                    or q_lower in r["Address"].lower()
                    or q_lower in r["Beds"].lower()
                    or q_lower in r["Status"].lower()
                ]

            if not rows:
                st.info(
                    "No matching results found with the current filters, or the site layout changed. "
                    "Try clearing filters or check the site directly."
                )
                return

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            for r in rows:
                st.markdown(
                    f"- [{r['Title']}]({r['Link']}) — {r['Price'] or 'Price N/A'} · "
                    f"{r['Beds']} · {r['Baths']} · {r['Address']} · {r['Status']}"
                )

            st.success(
                "Fetched Isla Vista 2026–27 listings. Always cross-check availability with the property manager."
            )

    with st.expander("⚖️ Legal & ethics (read me)"):
        st.write(
            """
            • Scraping public pages can break if the site changes. Keep requests minimal and cached.
            • Check each site's **Terms of Service** and **robots.txt**. If scraping is disallowed, remove it.
            • Prefer official APIs or email the property manager for a feed.
            """
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
    "English": "https://www.english.ucsb.edu/undergraduate/for-majors/requirements/",
}

def academics_page():
    st.header("🎓 Academics — advising quick links")
    st.caption("Every major has its own plan sheet / prereqs. These are placeholders — swap with official UCSB links.")

    col1, col2 = st.columns([1.2, 2])
    with col1:
        major = st.selectbox("Select a major", list(MAJOR_SHEETS.keys()))
        st.link_button("Open major planning page", MAJOR_SHEETS[major])
        st.divider()

        st.subheader("Most asked questions")

        # Q&A as interactive expanders
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
    "Main navigation",  # visually styled as tabs by CSS above
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
- Swap placeholder links with official UCSB URLs you trust.
- Expand the Isla Vista parser as the site changes or you want more features (price per person, etc.).
- Connect an LLM for the Q&A tab.
"""
)
