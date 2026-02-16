# ui_components.py
from __future__ import annotations

from typing import Optional


# ---------------------------
# Top UI blocks
# ---------------------------
def topbar_html() -> str:
    return """<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <span class="brand-dot"></span>
      <span>gauchoGPT</span>
      <small>UCSB Student Helper</small>
    </div>
    <div class="topbar-right">Home • Housing • Academics • Professors • Aid & Jobs • Q&A</div>
  </div>
</div>"""


def hero_html() -> str:
    return """<div class="hero">
  <div class="hero-title">UCSB tools, in one place.</div>
  <div class="hero-sub">
    Find housing, plan classes, check professors, and navigate aid & jobs — built for speed and clarity.
  </div>
</div>
<div class="section-gap"></div>"""


# ---------------------------
# Home cards
# ---------------------------
def home_row_html(title: str, desc: str, thumb_uri: Optional[str] = None) -> str:
    thumb_html = (
        f'<div class="home-thumb"><img src="{thumb_uri}" alt="UCSB" /></div>'
        if thumb_uri else ""
    )

    # IMPORTANT: no leading spaces, no indented multiline blocks
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



# ---------------------------
# Housing page blocks
# ---------------------------
def housing_header_html() -> str:
    return """<div class="card-soft">
  <div style="font-size:1.35rem; font-weight:950; letter-spacing:-0.02em;">Isla Vista Housing</div>
  <div class="small-muted">
    CSV snapshot from ivproperties.com (2026–27).
    Photos show if <code>image_url</code> exists. Add a local fallback in <code>assets/ucsb_fallback.jpg</code>.
  </div>
</div>
<div class="section-gap"></div>"""


def housing_summary_html(showing: int, total: int, price_limit: int) -> str:
    return f"""<div class="section-gap"></div>
<div class="card-soft">
  <div class="small-muted">
    Showing <strong>{showing}</strong> of <strong>{total}</strong> units
    • <span class="pill pill-blue">Price ≤ ${price_limit:,}</span>
  </div>
</div>
<div class="section-gap"></div>"""


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
    utilities_html = (
        f"<div class='small-muted' style='margin-top:6px;'>Included utilities: {utilities}</div>"
        if utilities
        else ""
    )
    ppp_html = f" · {ppp_text}" if ppp_text else ""

    return f"""<div class="card">
  <div class="listing-wrap">
    <div class="thumb">{img_html}</div>

    <div>
      <div class="listing-title">{street}</div>
      <div class="listing-sub">{unit}</div>

      <div class="pills">
        <span class="pill">{bed_label}</span>
        <span class="pill">{ba_label}</span>
        <span class="pill">{residents_label}</span>
        <span class="pill pill-gold">{pet_label}</span>
        {link_chip}
      </div>

      <div style="margin-top:10px;">
        <div class="{status_class}">{status_text}</div>
        <div class="price-row">
          {price_text}
          <span class="small-muted" style="font-weight:750;">{ppp_html}</span>
        </div>
        {utilities_html}
      </div>
    </div>
  </div>
</div>
<div class="section-gap"></div>"""
