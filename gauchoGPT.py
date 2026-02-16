from __future__ import annotations

import os
import base64
import textwrap
from typing import Dict, Any, Optional
import requests
from housingproperties import parse_isla_vista_properties
from housing_page import housing_page_from_listings


import streamlit as st
import pandas as pd
from urllib.parse import quote_plus

from academics import academics_page
from ui_components import (
    topbar_html,
    hero_html,
    home_row_html,
    housing_header_html,
    # If you added these from my expanded ui_components:
    # housing_summary_html,
    # housing_listing_card_html,
)

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="gauchoGPT — UCSB helper",
    page_icon="🧢",
    layout="wide",
)

# ---------------------------
# Core render helpers
# ---------------------------
def render_html(html: str) -> None:
    s = textwrap.dedent(html).strip()
    # strip EVERY line (not just lstrip) + remove empty lines
    s = "\n".join(line.strip() for line in s.splitlines() if line.strip())
    st.markdown(s, unsafe_allow_html=True)


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

def inject_css(css_path: str, *, bg_uri: Optional[str] = None) -> None:
    if not os.path.exists(css_path):
        st.error(f"Missing CSS file: {css_path}")
        return

    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    css = css.replace("{{BG_URI}}", bg_uri or "")
    render_html(f"<style>{css}</style>")

def safe_str(x) -> str:
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)

# ---------------------------
# Assets (optional)
# ---------------------------
BG_URI = (
    img_to_data_uri("assets/ucsb_bg.jpg")
    or img_to_data_uri("assets/ucsb_bg.jpeg")
    or img_to_data_uri("assets/ucsb_bg.png")
    or img_to_data_uri("assets/ucsb_bg.webp")
)

FALLBACK_LISTING_URI = (
    img_to_data_uri("assets/ucsb_fallback.jpg")
    or img_to_data_uri("assets/ucsb_fallback.jpeg")
    or img_to_data_uri("assets/ucsb_fallback.png")
    or img_to_data_uri("assets/ucsb_fallback.webp")
)

REMOTE_FALLBACK_IMAGE_URL = None  # set to public URL if you want

# ---------------------------
# Session state
# ---------------------------
NAV_LABELS = ["🏁 Home", "🏠 Housing", "📚 Academics", "👩‍🏫 Professors", "💸 Aid & Jobs", "💬 Q&A"]
st.session_state.setdefault("main_nav", "🏁 Home")
st.session_state.setdefault("sidebar_nav_open", False)

# ---------------------------
# Global UI (CSS + Topbar)
# ---------------------------
inject_css("assets/styles.css", bg_uri=BG_URI)
render_html(topbar_html())

# ---------------------------
# Sidebar Nav
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

# ---------------------------
# HOME
# ---------------------------
def _home_row(title: str, desc: str, btn_text: str, nav_target: str, thumb_uri: Optional[str] = None):
    render_html(home_row_html(title, desc, thumb_uri=thumb_uri))
    _, cbtn = st.columns([1, 0.25])
    with cbtn:
        if st.button(btn_text, use_container_width=True):
            st.session_state["main_nav"] = nav_target
            st.rerun()
    render_html('<div class="section-gap"></div>')

def home_page():
    render_html(hero_html())

    home_thumb = (
        img_to_data_uri("assets/home_thumb.jpg")
        or img_to_data_uri("assets/home_thumb.png")
    )

    _home_row("🏠 Housing", "Browse IV listings with clean filters + optional photos.", "Open Housing", "🏠 Housing", home_thumb)
    _home_row("📚 Academics", "Plan quarters, search courses, explore resources.", "Open Academics", "📚 Academics", home_thumb)
    _home_row("👩‍🏫 Professors", "Fast RMP searches + department pages.", "Open Professors", "👩‍🏫 Professors", home_thumb)
    _home_row("💸 Aid & Jobs", "FAFSA, work-study, UCSB aid + Handshake links.", "Open Aid & Jobs", "💸 Aid & Jobs", home_thumb)
    _home_row("💬 Q&A", "Optional: wire to an LLM (OpenAI/Anthropic/local).", "Open Q&A", "💬 Q&A", home_thumb)

# ---------------------------
# Housing (placeholder header only; swap in your full housing_page)
# ---------------------------
def housing_page():
    render_html(housing_header_html())
    st.info("Hook your full housing_page() here (filters + listing cards).")

# ---------------------------
# Professors (simple)
# ---------------------------
DEPT_SITES = {
    "PSTAT": "https://www.pstat.ucsb.edu/people",
    "CS": "https://www.cs.ucsb.edu/people/faculty",
    "MATH": "https://www.math.ucsb.edu/people/faculty",
}

def profs_page():
    render_html("""<div class="card-soft">
  <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Professors & course intel</div>
  <div class="small-muted">Quick links to RateMyProfessors searches and department faculty pages.</div>
</div>
<div class="section-gap"></div>""")

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
# Aid & Jobs (simple)
# ---------------------------
AID_LINKS = {
    "FAFSA": "https://studentaid.gov/h/apply-for-aid/fafsa",
    "UCSB Financial Aid": "https://www.finaid.ucsb.edu/",
    "Work-Study (UCSB)": "https://www.finaid.ucsb.edu/types-of-aid/work-study",
    "Handshake": "https://ucsb.joinhandshake.com/",
}

def aid_jobs_page():
    render_html("""<div class="card-soft">
  <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Financial aid, work-study & jobs</div>
  <div class="small-muted">Short explainers + quick links.</div>
</div>
<div class="section-gap"></div>""")

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
    for i, (label, url) in enumerate(AID_LINKS.items()):
        with cols[i % 4]:
            st.link_button(label, url)
    render_html("</div>")

# ---------------------------
# Q&A (placeholder)
# ---------------------------
def qa_page():
    render_html("""<div class="card-soft">
  <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Ask gauchoGPT</div>
  <div class="small-muted">Wire this to your preferred LLM API or a local model.</div>
</div>
<div class="section-gap"></div>""")

    render_html('<div class="card">')
    prompt = st.text_area("Ask a UCSB question", placeholder="e.g., How do I switch into the STAT&DS major?")
    if st.button("Answer"):
        st.info("Connect to an API (OpenAI / Anthropic / local) here.")
        st.caption(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    render_html("</div>")


def housing_page():
    # 1) get HTML (replace URL with the exact page you scrape)
    url = "https://www.ivproperties.com/"  # update this if needed
    html = requests.get(url, timeout=30).text

    # 2) parse into Listing objects
    listings = parse_isla_vista_properties(html)

    # 3) render styled page
    housing_page_from_listings(
        listings=listings,
        render_html=render_html,
        fallback_listing_uri=FALLBACK_LISTING_URI,
        remote_fallback_url=REMOTE_FALLBACK_IMAGE_URL,
    )


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


# ---------------------------
# Tiny debug footer (helps you catch "wrong entrypoint" instantly)
# ---------------------------
with st.expander("Debug (click to verify running file)"):
    st.write("Running file:", __file__)
    st.write("Nav:", st.session_state.get("main_nav"))


