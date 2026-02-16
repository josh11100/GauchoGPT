from __future__ import annotations

import os, base64, textwrap
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
from urllib.parse import quote_plus

from academics import academics_page
from ui_components import topbar_html, hero_html, home_row_html, housing_header_html

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="gauchoGPT — UCSB helper", page_icon="🧢", layout="wide")

# ---------------------------
# Helpers
# ---------------------------
def render_html(html: str) -> None:
    s = textwrap.dedent(html).strip("\n")
    s = "\n".join(line.lstrip() for line in s.splitlines())
    st.markdown(s, unsafe_allow_html=True)

def img_to_data_uri(path: str) -> Optional[str]:
    if not os.path.exists(path): return None
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    if ext not in {"jpg","jpeg","png","webp"}: return None
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    mime = "jpeg" if ext in {"jpg","jpeg"} else ext
    return f"data:image/{mime};base64,{b64}"

def inject_css(css_path: str, bg_uri: Optional[str] = None) -> None:
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    if bg_uri:
        css = css.replace("{{BG_URI}}", bg_uri)
    else:
        # If no bg image, replace with empty so it doesn't request "None"
        css = css.replace("{{BG_URI}}", "")
    render_html(f"<style>{css}</style>")

def safe_str(x) -> str:
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)

# ---------------------------
# Images
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

# ---------------------------
# State
# ---------------------------
NAV_LABELS = ["🏁 Home", "🏠 Housing", "📚 Academics", "👩‍🏫 Professors", "💸 Aid & Jobs", "💬 Q&A"]
st.session_state.setdefault("main_nav", "🏁 Home")
st.session_state.setdefault("sidebar_nav_open", False)

# ---------------------------
# Inject CSS + Topbar
# ---------------------------
inject_css("assets/styles.css", bg_uri=BG_URI)
render_html(topbar_html())

# ---------------------------
# Sidebar (same logic as before)
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
# Home
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
    home_thumb = img_to_data_uri("assets/home_thumb.jpg") or img_to_data_uri("assets/home_thumb.png")
    _home_row("🏠 Housing", "Browse IV listings with clean filters + optional photos.", "Open Housing", "🏠 Housing", home_thumb)
    _home_row("📚 Academics", "Plan quarters, search courses, explore resources.", "Open Academics", "📚 Academics", home_thumb)
    _home_row("👩‍🏫 Professors", "Fast RMP searches + department pages.", "Open Professors", "👩‍🏫 Professors", home_thumb)
    _home_row("💸 Aid & Jobs", "FAFSA, work-study, UCSB aid + Handshake links.", "Open Aid & Jobs", "💸 Aid & Jobs", home_thumb)
    _home_row("💬 Q&A", "Optional: wire to an LLM (OpenAI/Anthropic/local).", "Open Q&A", "💬 Q&A", home_thumb)

# (Keep your other pages the same; just swap header blocks to call render_html(housing_header_html()) etc.)

PAGES: Dict[str, Any] = {
    "🏁 Home": home_page,
    "🏠 Housing": lambda: render_html(housing_header_html()),  # replace with your full housing_page
    "📚 Academics": academics_page,
}
PAGES[st.session_state["main_nav"]]()
