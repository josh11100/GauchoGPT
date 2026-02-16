# ui/layout.py
import streamlit as st
from pathlib import Path

def apply_theme(css_path: str) -> None:
    css = Path(css_path).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def topbar() -> None:
    st.markdown(
        """
        <div class="gold-topbar">
            <div class="gold-topbar-left">UCSB Gaucho On-Line Data</div>
            <div class="gold-topbar-right">gauchoGPT · UCSB Student Helper</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def sidebar_intro() -> None:
    st.sidebar.title("gauchoGPT")
    st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

def gold_tabs(page_names, default_index=0, key="main_nav"):
    st.markdown('<div class="gold-nav-wrapper">', unsafe_allow_html=True)
    choice = st.radio(
        "Main navigation",
        page_names,
        horizontal=True,
        index=default_index,
        key=key,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return choice
