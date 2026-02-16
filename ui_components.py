# ui_components.py
from __future__ import annotations
from typing import Optional


def topbar_html() -> str:
    return (
        '<div class="topbar">'
        '  <div class="topbar-inner">'
        '    <div class="brand">'
        '      <span class="brand-dot"></span>'
        '      <span>gauchoGPT</span>'
        '      <small>UCSB Student Helper</small>'
        '    </div>'
        '    <div class="topbar-right">Home • Housing • Academics • Professors • Aid & Jobs • Q&A</div>'
        '  </div>'
        '</div>'
    )


def hero_html() -> str:
    return (
        '<div class="hero">'
        '  <div class="hero-title">UCSB tools, in one place.</div>'
        '  <div class="hero-sub">Find housing, plan classes, check professors, and navigate aid & jobs — built for speed and clarity.</div>'
        '</div>'
        '<div class="section-gap"></div>'
    )


def home_row_html(title: str, desc: str, thumb_uri: Optional[str] = None) -> str:
    thumb_html = (
        f'<div class="home-thumb"><img src="{thumb_uri}" alt="UCSB" /></div>' if thumb_uri else ""
    )
    # Keep HTML non-indented so Streamlit never treats it as a code block
    return (
        f'<div class="card">'
        f'  <div class="home-row">'
        f'    <div class="home-left">'
        f'      {thumb_html}'
        f'      <div>'
        f'        <div class="home-title">{title}</div>'
        f'        <div class="small-muted home-desc">{desc}</div>'
        f'      </div>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )


def housing_header_html() -> str:
    return (
        '<div class="card-soft">'
        '  <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">🏠 Isla Vista Housing (CSV snapshot)</div>'
        '  <div class="small-muted">Snapshot of selected Isla Vista units from ivproperties.com for the 2026–27 lease term. '
        'Filters below help you find fits by price, bedrooms, status, and pet policy.</div>'
        '</div>'
        '<div class="section-gap"></div>'
    )


def housing_summary_html(showing: int, total: int, price_limit: int) -> str:
    return (
        '<div class="section-gap"></div>'
        '<div class="card-soft">'
        f'  <div class="small-muted">'
        f'    Showing <strong>{showing}</strong> of <strong>{total}</strong> units • Price ≤ '
        f'    <span class="pill pill-blue">${price_limit:,}</span>'
        f'  </div>'
        '</div>'
        '<div class="section-gap"></div>'
    )


def housing_listing_card_html(
    *,
    street: str,
    unit: str,
    bed_label: str,
    ba_label: str,
    residents_label: str,
    pet_label: str,
    status_text: str,
    status_class: str,
    price_text: str,
    ppp_text: str,
    utilities: str,
    img_html: str,
    link_chip: str,
) -> str:
    # unit line optional
    unit_html = f'<div class="listing-sub">{unit}</div>' if unit else ""

    utilities_html = (
        f"<div class='small-muted' style='margin-top:6px;'>Included utilities: {utilities}</div>"
        if utilities else ""
    )

    ppp_html = (
        f"<span class='small-muted' style='font-weight:750;'> · {ppp_text}</span>"
        if ppp_text else ""
    )

    return (
        '<div class="card">'
        '  <div class="listing-wrap">'
        f'    <div class="thumb">{img_html}</div>'
        '    <div>'
        f'      <div class="listing-title">{street}</div>'
        f'      {unit_html}'
        '      <div class="pills">'
        f'        <span class="pill">{bed_label}</span>'
        f'        <span class="pill">{ba_label}</span>'
        f'        <span class="pill">{residents_label}</span>'
        f'        <span class="pill pill-gold">{pet_label}</span>'
        f'        {link_chip}'
        '      </div>'
        '      <div style="margin-top:10px;">'
        f'        <div class="{status_class}">{status_text}</div>'
        f'        <div class="price-row">{price_text}{ppp_html}</div>'
        f'        {utilities_html}'
        '      </div>'
        '    </div>'
        '  </div>'
        '</div>'
        '<div class="section-gap"></div>'
    )
