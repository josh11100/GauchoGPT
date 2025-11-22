# academics.py
from __future__ import annotations
import os
from typing import Optional

import streamlit as st
import pandas as pd

try:
    from streamlit_folium import st_folium
    import folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

# ---------------------------
# ACADEMICS — classes by quarter (CSV)
# ---------------------------
COURSES_CSV = "major_courses_by_quarter.csv"  # CSV for classes by major & quarter

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
    "English": "https://www.english.ucsb.edu/undergraduate/for-majors/requirements/ ",
}

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


def load_courses_df() -> Optional[pd.DataFrame]:
    if not os.path.exists(COURSES_CSV):
        return None

    df = pd.read_csv(COURSES_CSV)

    df.columns = [c.strip().lower() for c in df.columns]

    for col in ["major", "course_code", "title", "quarter"]:
        if col not in df.columns:
            st.error(f"'{COURSES_CSV}' is missing required column: '{col}'")
            return None

    if "units" not in df.columns:
        df["units"] = None
    if "status" not in df.columns:
        df["status"] = ""
    if "notes" not in df.columns:
        df["notes"] = ""

    df["quarter"] = df["quarter"].astype(str).str.strip().str.title()
    return df


def academics_page():
    st.header("🎓 Academics — advising, classes & map")
    st.caption(
        "Open your major sheet, see classes by quarter from your CSV, build a schedule, "
        "and quickly locate buildings on a map."
    )

    courses_df = load_courses_df()

    # Major selector + link
    major = st.selectbox(
        "Select a major",
        list(MAJOR_SHEETS.keys()),
        index=0,
        key="acad_major",
    )

    st.markdown("#### Major plan sheet")
    st.link_button("Open major planning page", MAJOR_SHEETS[major])

    st.divider()

    tab_classes, tab_planner, tab_map, tab_faq = st.tabs(
        ["Classes by quarter", "My quarter planner", "Class locator map", "FAQ"]
    )

    # ========= TAB 1: CLASSES =========
    with tab_classes:
        st.subheader("Classes by quarter (from your CSV)")

        if courses_df is None:
            st.caption(
                "To use this section, add a CSV named `major_courses_by_quarter.csv` "
                "in this folder. Required columns: `major`, `course_code`, `title`, "
                "`quarter`. Optional: `units`, `status`, `notes`."
            )
        else:
            major_filtered = courses_df[courses_df["major"] == major]

            if major_filtered.empty:
                st.info(f"No entries found in the CSV yet for **{major}**.")
            else:
                available_quarters = (
                    major_filtered["quarter"]
                    .dropna()
                    .astype(str)
                    .str.title()
                    .unique()
                    .tolist()
                )
                available_quarters = sorted(available_quarters)

                default_q = "Winter" if "Winter" in available_quarters else (
                    available_quarters[0] if available_quarters else None
                )

                if available_quarters and default_q is not None:
                    quarter = st.selectbox(
                        "Quarter",
                        available_quarters,
                        index=available_quarters.index(default_q),
                        key="acad_quarter",
                    )

                    quarter_filtered = major_filtered[
                        major_filtered["quarter"].astype(str).str.title() == quarter
                    ].reset_index(drop=True)

                    if quarter_filtered.empty:
                        st.info(
                            f"No classes listed for **{major}** in **{quarter}** "
                            "in `major_courses_by_quarter.csv` yet."
                        )
                    else:
                        open_count = (quarter_filtered["status"].str.lower() == "open").sum()
                        full_count = (quarter_filtered["status"].str.lower() == "full").sum()
                        mixed_count = (quarter_filtered["status"].str.lower() == "mixed").sum()

                        st.markdown(
                            f"""
                            <div class='small muted'>
                                Showing <strong>{len(quarter_filtered)}</strong> class(es)
                                for <strong>{major}</strong> in <strong>{quarter}</strong> ·
                                <span class='ok'>Open: {open_count}</span> ·
                                <span class='warn'>Mixed: {mixed_count}</span> ·
                                <span class='err'>Full: {full_count}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown("---")

                        # 🔵 3 CARDS PER ROW
                        for i in range(0, len(quarter_filtered), 3):
                            cols = st.columns(3, gap="medium")
                            for j in range(3):
                                idx = i + j
                                if idx >= len(quarter_filtered):
                                    break
                                row = quarter_filtered.iloc[idx]

                                code = str(row.get("course_code", "")).strip()
                                title = str(row.get("title", "")).strip()
                                units = row.get("units", "")
                                status = str(row.get("status", "") or "").strip()
                                notes = str(row.get("notes", "") or "").strip()

                                units_label = (
                                    f"Units: {units}"
                                    if units not in (None, "", float("nan"))
                                    else "Units: n/a"
                                )

                                status_lower = status.lower()
                                if status_lower == "open":
                                    status_class = "ok"
                                    status_bg = "#ecfdf3"
                                elif status_lower == "full":
                                    status_class = "err"
                                    status_bg = "#fef2f2"
                                elif status_lower == "mixed":
                                    status_class = "warn"
                                    status_bg = "#fffbeb"
                                else:
                                    status_class = "muted"
                                    status_bg = "#f3f4f6"

                                with cols[j]:
                                    st.markdown(
                                        f"""
                                        <div style="border-radius: 8px; overflow: hidden;
                                                    border: 1px solid #e5e7eb; margin-bottom: 12px;
                                                    box-shadow: 0 1px 2px rgba(15,23,42,0.05);">
                                          <div style="background:#003660; color:#ffffff;
                                                      padding:6px 12px; font-weight:600;
                                                      font-size:0.95rem;">
                                            {code} — {title}
                                          </div>
                                          <div style="padding:8px 12px; font-size:0.9rem;">
                                            <span class="pill">{units_label}</span>
                                            <span class="pill" style="background:{status_bg};">
                                              <span class="{status_class}">{status or "Status n/a"}</span>
                                            </span>
                                            {"<div class='small muted' style='margin-top:4px;'>" + notes + "</div>" if notes else ""}
                                          </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                else:
                    st.info(
                        f"No quarter information found for **{major}** in the CSV."
                    )

    # ========= TAB 2: PLANNER =========
    with tab_planner:
        st.subheader("Build your quarter (scratchpad)")
        st.caption(
            "This is just a planner for you. It doesn’t talk to GOLD yet — use it to play "
            "with different course combos and unit loads."
        )

        default_rows = [
            {"Course": "PSTAT 5A", "Units": 5, "Type": "Major prep"},
            {"Course": "PSTAT 120A", "Units": 4, "Type": "Major"},
            {"Course": "GE Area D", "Units": 4, "Type": "GE"},
        ]

        data = st.data_editor(
            pd.DataFrame(default_rows),
            use_container_width=True,
            num_rows="dynamic",
            key="acad_planner",
        )

        total_units = int(sum(data["Units"])) if not data.empty and "Units" in data.columns else 0
        st.metric("Planned units", total_units)

        st.markdown(
            """
            **Tips**
            - Many students aim for **12–16 units** per quarter.
            - Try balancing **1–2 heavy technical** classes with **1 lighter GE**.
            - Check your major’s sample plan and talk to an advisor if you’re unsure.
            """
        )

    # ========= TAB 3: MAP =========
    with tab_map:
        st.subheader("🗺️ Quick class locator")

        bname = st.selectbox("Choose a building", list(BUILDINGS.keys()), key="acad_building")
        lat, lon = BUILDINGS[bname]

        if HAS_FOLIUM:
            m = folium.Map(location=[lat, lon], zoom_start=16, control_scale=True)
            folium.Marker([lat, lon], tooltip=bname).add_to(m)
            st_folium(m, width=900, height=500)
        else:
            st.info("Install folium + streamlit-folium for the interactive map: pip install folium streamlit-folium")
            st.write({"building": bname, "lat": lat, "lon": lon})

        st.caption("Future idea: auto-pin all buildings from your full GOLD schedule.")

    # ========= TAB 4: FAQ =========
    with tab_faq:
        st.subheader("Common advising questions")

        with st.expander("Still lost on what classes to take?"):
            st.markdown(
                """
                Use your department’s official advising resources (linked above) and schedule an
                appointment. Bring:
                - Your current and past schedules  
                - A list of courses you're considering  
                - Questions about double majors, minors, or 4-year plans  
                """
            )

        with st.expander("Can’t find your specific major in this app?"):
            st.markdown(
                """
                Right now this app only has a small set of majors.  
                You can:
                - Use the **UCSB Catalog** and your department’s website  
                - Ask the app maintainer to add your major + links in a future update  
                """
            )

        with st.expander("Not sure how many classes to take in a quarter?"):
            st.markdown(
                """
                A common pattern is:
                - **12 units** → lighter load  
                - **16 units** → typical full load  
                - **20+ units** → heavy load, usually needs approval  

                Always check:
                - Financial aid unit requirements  
                - Major sample plans  
                - How intense your technical courses are  
                """
            )

        with st.expander("Class is full or waitlisted — what now?"):
            st.markdown(
                """
                - Use the **GOLD waitlist** when available  
                - Watch for adds/drops right before the quarter starts  
                - Email the instructor or department about add-code/waitlist policies  
                - Keep backup GE/elective options ready in case you don’t get in  
                """
            )

        st.caption("Customize this FAQ over time with UCSB-specific tips you learn.")
