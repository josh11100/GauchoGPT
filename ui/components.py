# ui/components.py
import streamlit as st

def pills(*labels: str) -> None:
    html = "<div class='small'>"
    for lab in labels:
        if lab:
            html += f"<span class='pill'>{lab}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def status_line(status_class: str, status_text: str, price_text: str, ppp_text: str = "") -> None:
    st.markdown(
        f"""
        <div class='small'>
            <span class='{status_class}'>{status_text}</span><br/>
            <span class='ok'>{price_text}</span>
            {" · " + ppp_text if ppp_text else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def small_muted(text: str) -> None:
    st.markdown(f"<div class='small muted'>{text}</div>", unsafe_allow_html=True)
