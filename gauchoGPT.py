# gauchoGPT — Streamlit GOLD-themed MVP
# ------------------------------------------------------------
# Main app file
# ------------------------------------------------------------
from __future__ import annotations
import os
import math
import sqlite3
import hashlib
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

# 🔹 import Academics tab from separate file
from academics import academics_page

# ------------------------------------------------------------
# 🔐 SIMPLE EMAIL/PASSWORD AUTH (SQLite db.sq)
# ------------------------------------------------------------
DB_PATH = "db.sq"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist yet."""
    conn = get_db()
    cur = conn.cursor()

    # Basic users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # You can add more tables later (plans, etc.)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash password with SHA-256 (simple demo, not enterprise-level)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(email: str, password: str) -> tuple[bool, str]:
    """Try to create a new user. Returns (success, message)."""
    email = email.strip().lower()
    if not email or not password:
        return False, "Email and password are required."

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, hash_password(password)),
        )
        conn.commit()
        return True, "Account created. You are now logged in."
    except sqlite3.IntegrityError:
        return False, "That email is already registered. Try logging in instead."
    finally:
        conn.close()


def check_user(email: str, password: str) -> bool:
    """Return True if the email/password combo is valid."""
    email = email.strip().lower()
    conn = get_db()
    cur = conn.execute(
        "SELECT password_hash FROM users WHERE email = ?",
        (email,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return row["password_hash"] == hash_password(password)


def ensure_session_keys():
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = None


def auth_sidebar():
    """
    Sidebar UI for login / signup.
    If user is not logged in, this will stop the app after showing the form.
    """
    ensure_session_keys()

    # If already logged in: show status + logout
    if st.session_state["user_email"]:
        st.sidebar.markdown(f"**Logged in as:** `{st.session_state['user_email']}`")
        if st.sidebar.button("Log out"):
            st.session_state["user_email"] = None
            st.experimental_rerun()
        return  # allow rest of app to render

    st.sidebar.subheader("Account")

    mode = st.sidebar.radio("Choose an option", ["Log in", "Sign up"], horizontal=True)

    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_password")

    if mode == "Sign up":
        password2 = st.sidebar.text_input(
            "Confirm password", type="password", key="auth_password2"
        )
        if st.sidebar.button("Create account"):
            if password != password2:
                st.sidebar.error("Passwords do not match.")
            else:
                ok, msg = create_user(email, password)
                if ok:
                    st.sidebar.success(msg)
                    st.session_state["user_email"] = email.strip().lower()
                    st.experimental_rerun()
                else:
                    st.sidebar.error(msg)
    else:  # Log in
        if st.sidebar.button("Log in"):
            if check_user(email, password):
                st.session_state["user_email"] = email.strip().lower()
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid email or password.")

    # If we got here, user is not logged in yet → stop app so pages don't show
    st.stop()


# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="gauchoGPT — UCSB helper",
    page_icon="🧢",
    layout="wide",
)

# Init DB (creates db.sq + tables if missing)
init_db()

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

# Sidebar title + auth box
st.sidebar.title("gauchoGPT")
st.sidebar.caption("UCSB helpers — housing · classes · professors · aid · jobs")

# 🔐 Show login / signup in the sidebar
auth_sidebar()  # stops app if not logged in

# At this point, st.session_state["user_email"] is guaranteed not None
st.sidebar.markdown(f"**Logged in as:** `{st.session_state['user_email']}`")

# ---------------------------
# HOUSING — CSV-backed listings
# ---------------------------
HOUSING_CSV = "iv_housing_listings.csv"

# (housing_page stays the same as you had)
# ... [KEEP your existing load_housing_df and housing_page definitions here]
# I’m not repeating them just to keep this message shorter, but you can
# paste your same housing code below this comment.

# ---------------------------
# (Put your existing load_housing_df and housing_page code here)
# ---------------------------

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
