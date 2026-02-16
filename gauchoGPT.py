from __future__ import annotations

import os
import base64
import textwrap
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
from urllib.parse import quote_plus

from academics import academics_page
from ui_components import topbar_html, hero_html, home_row_html
from housing_page import housing_page  # ✅ CSV housing page lives here


# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="gauchoGPT — UCSB helper",
    page_icon="🧢",
    layout="wide",
)

# ---------------------------
# Render helpers
# ---------------------------
def render_html(html: str) -> None:
    # IMPORTANT: don't strip each line; can break HTML rendering
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)

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

# ---------------------------
# Assets
# ---------------------------
BG_URI = (
    img_to_data_uri("assets/ucsb_bg.jpg")
    or img_to_data_uri("assets/ucsb_bg.jpeg")
    or img_to_data_uri("assets/ucsb_bg.png")
    or img_to_data_uri("assets/ucsb_bg.webp")
)

HOME_THUMB = (
    img_to_data_uri("assets/home_thumb.jpg")
    or img_to_data_uri("assets/home_thumb.png")
)

FALLBACK_LISTING_URI = (
    img_to_data_uri("assets/ucsb_fallback.jpg")
    or img_to_data_uri("assets/ucsb_fallback.jpeg")
    or img_to_data_uri("assets/ucsb_fallback.png")
    or img_to_data_uri("assets/ucsb_fallback.webp")
)

REMOTE_FALLBACK_IMAGE_URL = None

# ---------------------------
# State
# ---------------------------
NAV_LABELS = ["🏁 Home", "🏠 Housing", "📚 Academics", "👩‍🏫 Professors", "💸 Aid & Jobs", "💬 Q&A"]
st.session_state.setdefault("main_nav", "🏁 Home")
st.session_state.setdefault("sidebar_nav_open", False)

# ---------------------------
# Global UI
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
    _home_row("🏠 Housing", "Browse IV listings with clean filters + optional photos.", "Open Housing", "🏠 Housing", HOME_THUMB)
    _home_row("📚 Academics", "Plan quarters, search courses, explore resources.", "Open Academics", "📚 Academics", HOME_THUMB)
    _home_row("👩‍🏫 Professors", "Fast RMP searches + department pages.", "Open Professors", "👩‍🏫 Professors", HOME_THUMB)
    _home_row("💸 Aid & Jobs", "FAFSA, work-study, UCSB aid + Handshake links.", "Open Aid & Jobs", "💸 Aid & Jobs", HOME_THUMB)
    _home_row("💬 Q&A", "Optional: wire to an LLM (OpenAI/Anthropic/local).", "Open Q&A", "💬 Q&A", HOME_THUMB)

# ---------------------------
# Professors
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
# Aid & Jobs
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
# Q&A
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
    render_html("</div>")

# ---------------------------
# Routing
# ---------------------------
PAGES: Dict[str, Any] = {
    "🏁 Home": home_page,
    "🏠 Housing": lambda: housing_page(
        render_html=render_html,
        fallback_listing_uri=FALLBACK_LISTING_URI,
        remote_fallback_url=REMOTE_FALLBACK_IMAGE_URL,
    ),
    "📚 Academics": academics_page,
    "👩‍🏫 Professors": profs_page,
    "💸 Aid & Jobs": aid_jobs_page,
    "💬 Q&A": qa_page,
}
PAGES[st.session_state["main_nav"]]()
