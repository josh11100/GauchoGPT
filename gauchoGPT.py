# gauchoGPT — Streamlit MVP
# ------------------------------------------------------------
# A single-file Streamlit web app to help UCSB students with:
# - Housing in Isla Vista (basic scraper for ivproperties.com with polite headers)
# - Academic advising quick links (major sheets / prereqs — placeholders)
# - Class/location helper with campus map pins
# - Professor info shortcuts (RateMyProfessors + UCSB departmental pages)
# - Financial aid & jobs FAQs (with handy links)
# 
# Notes:
# • This is an MVP scaffold designed for easy local launch and iteration.
# • Scraping is best-effort and may break if site structure changes; see TODOs.
# • Before deploying publicly, check each site's Terms of Service and robots.txt.
# • Replace placeholder links with official UCSB URLs you curate.
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
# Style helpers
# ---------------------------
HIDE_STREAMLIT_STYLE = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .small {font-size: 0.85rem; color: #666;}
        .muted {color:#6b7280}
        .pill {display:inline-block; padding:4px 10px; border-radius:9999px; background:#eef2ff; color:#3730a3; font-weight:600; margin-right:8px}
        .tag  {display:inline-block; padding:2px 8px; border-radius:9999px; background:#f1f5f9; color:#334155; font-weight:500; margin-right:6px}
        .code {font-family: ui-monospace, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; background:#0b1021; color:#d1e1ff; padding:3px 6px; border-radius:6px}
        .ok   {color:#059669; font-weight:600}
        .warn {color:#b45309; font-weight:600}
        .err  {color:#b91c1c; font-weight:700}
    </style>
"""
st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

st.sidebar.title("🧢 gauchoGPT")
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
# HOUSING (ivproperties.com)
# ---------------------------
@dataclass
class Listing:
    title: str
    address: str
    price: str
    beds: str
    baths: str
    link: str


def parse_ivproperties_listings(html: str) -> List[Listing]:
    """Best-effort parser for ivproperties.com catalog pages.
    This may need updates if the site's markup changes.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards = []

    # Try a few common patterns
    selectors = [
        "div.listing",               # generic
        "article.property-card",     # alt pattern
        "div.property-card",         # alt pattern
        "li.property"                # alt
    ]

    for sel in selectors:
        nodes = soup.select(sel)
        if nodes:
            for node in nodes:
                # Heuristics to extract fields
                title = (node.select_one(".title") or node.select_one("h2") or node.select_one("h3"))
                address = node.select_one(".address")
                price = node.select_one(".price")
                beds  = node.select_one(".beds, .bedrooms")
                baths = node.select_one(".baths, .bathrooms")
                link  = node.select_one("a")

                listing = Listing(
                    title=title.get_text(strip=True) if title else "Listing",
                    address=address.get_text(strip=True) if address else "Isla Vista, CA",
                    price=price.get_text(strip=True) if price else "—",
                    beds=beds.get_text(strip=True) if beds else "—",
                    baths=baths.get_text(strip=True) if baths else "—",
                    link=link.get("href") if link else ""
                )
                cards.append(listing)
            break

    return cards


def housing_page():
    st.header("🏠 Isla Vista Housing (beta)")
    st.caption("Data pulled live from public pages when possible. Always verify details with the property manager.")

    col_a, col_b, col_c, col_d, col_e = st.columns([2,1,1,1,1])
    with col_a:
        q = st.text_input("Search keyword (optional)", placeholder="2 bed, Del Playa, studio…")
    with col_b:
        max_price = st.number_input("Max $/mo (optional)", min_value=0, value=0, step=50)
    with col_c:
        beds = st.selectbox("Bedrooms", ["Any", "Studio", "1", "2", "3", "4+"], index=0)
    with col_d:
        fetch_btn = st.button("Fetch IVProperties")
    with col_e:
        only_available = st.checkbox("Only Available")

    st.markdown("""
    <div class='small muted'>
    <span class='pill'>Source</span> ivproperties.com · Respect robots.txt · Use responsibly
    </div>
    """, unsafe_allow_html=True)

    if fetch_btn:
        with st.spinner("Contacting ivproperties.com…"):
            # This is a generic catalog URL; adjust if the real site filters exist
            url = "https://www.ivproperties.com/"
            if q:
                # some sites ignore query params; this ensures we hit the homepage then filter client-side
                url = f"https://www.ivproperties.com/?q={quote_plus(q)}"
            resp = fetch(url)
            if not resp:
                return

            listings = parse_ivproperties_listings(resp.text)

            # Optional client-side filters
            def price_to_int(p: str) -> Optional[int]:
                m = re.search(r"(\$?)([\d,]+)", p)
                if not m:
                    return None
                try:
                    return int(m.group(2).replace(",", ""))
                except:
                    return None

            rows = []
            for L in listings:
                p_int = price_to_int(L.price)
                if max_price and (p_int is not None) and p_int > max_price:
                    continue
                if beds != "Any":
                    if beds == "4+":
                        # accept 4 or more
                        b = re.search(r"(\d+)", L.beds or "")
                        if not (b and int(b.group(1)) >= 4):
                            continue
                    else:
                        if beds.lower() not in (L.beds or "").lower():
                            continue
                rows.append({
                    "Title": L.title,
                    "Address": L.address,
                    "Price": L.price,
                    "Beds": L.beds,
                    "Baths": L.baths,
                    "Link": L.link if L.link.startswith("http") else ("https://www.ivproperties.com" + L.link if L.link else "")
                })

            if not rows:
                st.info("No matching results found (or the site's markup changed). Try clearing filters.")
                st.caption("Tip: You can expand this parser for different selectors unique to the site.")
                return

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            for r in rows:
                st.markdown(f"- [{r['Title']}]({r['Link']}) — {r['Price']} · {r['Beds']} · {r['Baths']} · {r['Address']}")

            st.success("Fetched listings. Always cross-check availability with the property manager.")

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
    # Replace with the official links you curate later
    "Statistics & Data Science": "https://www.pstat.ucsb.edu/undergrad/majors",
    "Computer Science": "https://www.cs.ucsb.edu/education/undergraduate",
    "Economics": "https://econ.ucsb.edu/undergrad",
    "Mathematics": "https://www.math.ucsb.edu/undergrad",
}

def academics_page():
    st.header("🎓 Academics — advising quick links")
    st.caption("Every major has its own plan sheet / prereqs. These are placeholders — swap with official UCSB links.")

    col1, col2 = st.columns([1.2, 2])
    with col1:
        major = st.selectbox("Pick a major", list(MAJOR_SHEETS.keys()))
        st.link_button("Open major planning page", MAJOR_SHEETS[major])
        st.divider()
        st.subheader("General tips")
        st.markdown(
            """
            - Check for **pre-major** vs **full major** requirements early.
            - Balance load: 1–2 heavy technicals + 1 lighter GE when possible.
            - Use GOLD waitlist smartly; watch enrollment windows.
            - Talk to advisors and upperclassmen in your dept Discord/Slack.
            """
        )
    with col2:
        st.subheader("Build your quarter (scratchpad)")
        data = st.experimental_data_editor(
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
    # Approximate campus coordinates (lat, lon). Add more as needed.
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
# (Optional) Q&A assistant placeholder
# ---------------------------
# To wire this up to an LLM, add a function that calls your preferred API.
# Keep keys in environment variables and never hardcode.

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
            # resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content": prompt}])
            # st.write(resp.choices[0].message.content)
            """,
            language="python",
        )

# ---------------------------
# Sidebar navigation
# ---------------------------
PAGES = {
    "Housing (IV)": housing_page,
    "Academics": academics_page,
    "Class Locator": locator_page,
    "Professors": profs_page,
    "Aid & Jobs": aid_jobs_page,
    "Q&A (WIP)": qa_page,
}

choice = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[choice]()

st.sidebar.divider()
st.sidebar.markdown("""
**Next steps**
- Swap placeholder links with official UCSB URLs you trust.
- Expand the ivproperties parser for site-specific selectors.
- Add caching and rate limiting if you fetch often.
- Connect an LLM for the Q&A tab.
""")
