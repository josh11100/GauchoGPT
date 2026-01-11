# academics_enhanced.py
from __future__ import annotations
import os
import sqlite3
from typing import Optional

import streamlit as st
import pandas as pd

try:
    from streamlit_folium import st_folium
    import folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

# Database path
DB_PATH = "gauchoGPT.db"

# Legacy CSV support
COURSES_CSV = "major_courses_by_quarter.csv"

# Majors mapping
MAJOR_DEPARTMENTS = {
    "Statistics & Data Science": ["PSTAT"],
    "Computer Science": ["CMPSC"],
    "Economics": ["ECON"],
    "Mathematics": ["MATH"],
    "Biology": ["MCDB", "EEMB"],
    "Psychology": ["PSY"],
    "Chemistry": ["CHEM"],
    "Physics": ["PHYS"],
    "Philosophy": ["PHIL"],
    "English": ["ENGL"],
}

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
    "English": "https://www.english.ucsb.edu/undergraduate/for-majors/requirements/",
}

BUILDINGS = {
    "Phelps Hall (PHELP)": (34.41239, -119.84862),
    "Harold Frank Hall (HFH)": (34.41434, -119.84246),
    "Chemistry (CHEM)": (34.41165, -119.84586),
    "HSSB": (34.41496, -119.84571),
    "Library": (34.41388, -119.84627),
    "IV Theater": (34.41249, -119.86155),
    "Buchanan Hall": (34.41340, -119.84568),
    "Girvetz Hall": (34.41559, -119.84714),
    "Ellison Hall": (34.41282, -119.84989),
}


@st.cache_data(ttl=3600)
def load_courses_from_db(major: str, quarter: str = "Winter 2025") -> Optional[pd.DataFrame]:
    """Load courses from SQL database for a specific major and quarter"""
    if not os.path.exists(DB_PATH):
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        departments = MAJOR_DEPARTMENTS.get(major, [])
        if not departments:
            return None
        
        placeholders = ','.join('?' * len(departments))
        query = f'''
            SELECT 
                c.course_code,
                c.title,
                c.units,
                c.description,
                c.prerequisites,
                o.instructor,
                o.days,
                o.time,
                o.location,
                o.enrolled,
                o.capacity,
                o.status,
                o.quarter
            FROM courses c
            LEFT JOIN course_offerings o ON c.course_code = o.course_code
            WHERE c.dept IN ({placeholders})
            AND (o.quarter = ? OR o.quarter IS NULL)
            ORDER BY c.course_code
        '''
        
        params = departments + [quarter]
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df if not df.empty else None
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return None


def load_courses_df() -> Optional[pd.DataFrame]:
    """Fallback: load from CSV if database doesn't exist"""
    if not os.path.exists(COURSES_CSV):
        return None

    df = pd.read_csv(COURSES_CSV)
    df.columns = [c.strip().lower() for c in df.columns]

    for col in ["major", "course_code", "title", "quarter"]:
        if col not in df.columns:
            return None

    if "units" not in df.columns:
        df["units"] = None
    if "status" not in df.columns:
        df["status"] = ""
    if "notes" not in df.columns:
        df["notes"] = ""

    df["quarter"] = df["quarter"].astype(str).str.strip().str.title()
    return df


def get_course_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics for courses"""
    stats = {
        'total': len(df),
        'open': (df['status'].str.lower() == 'open').sum(),
        'full': (df['status'].str.lower() == 'full').sum(),
        'mixed': (df['status'].str.lower() == 'mixed').sum(),
        'avg_units': df['units'].mean() if 'units' in df.columns else 0,
    }
    return stats


def display_course_card(row, col_container):
    """Display a single course as a card"""
    with col_container:
        code = str(row.get("course_code", "")).strip()
        title = str(row.get("title", "")).strip()
        units = row.get("units", "")
        status = str(row.get("status", "") or "").strip()
        instructor = str(row.get("instructor", "") or "").strip()
        location = str(row.get("location", "") or "").strip()
        time_info = str(row.get("time", "") or "").strip()
        days = str(row.get("days", "") or "").strip()
        enrolled = row.get("enrolled", 0)
        capacity = row.get("capacity", 0)

        units_label = f"{units} units" if units not in (None, "", float("nan")) else "Units: n/a"

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

        enrollment_info = f"{enrolled}/{capacity}" if capacity > 0 else "N/A"
        
        info_parts = []
        if instructor:
            info_parts.append(f"👨‍🏫 {instructor}")
        if days and time_info:
            info_parts.append(f"📅 {days} {time_info}")
        if location:
            info_parts.append(f"📍 {location}")
        
        info_html = "<br>".join(info_parts) if info_parts else ""

        st.markdown(
            f"""
            <div style="border-radius: 8px; overflow: hidden;
                        border: 1px solid #e5e7eb; margin-bottom: 12px;
                        box-shadow: 0 1px 2px rgba(15,23,42,0.05);">
              <div style="background:#003660; color:#ffffff;
                          padding:8px 12px; font-weight:600;
                          font-size:0.95rem;">
                {code}
              </div>
              <div style="padding:10px 12px; font-size:0.9rem;">
                <div style="font-weight:500; margin-bottom:6px;">{title}</div>
                <div style="margin-bottom:8px;">
                  <span class="pill">{units_label}</span>
                  <span class="pill" style="background:{status_bg};">
                    <span class="{status_class}">{status or "Status n/a"}</span>
                  </span>
                  <span class="pill">👥 {enrollment_info}</span>
                </div>
                {f"<div class='small muted' style='line-height:1.5;'>{info_html}</div>" if info_html else ""}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def academics_page():
    st.header("🎓 Academics — advising, classes & map")
    st.caption(
        "View live course data from UCSB, build your schedule, and locate buildings."
    )

    has_db = os.path.exists(DB_PATH)
    has_csv = os.path.exists(COURSES_CSV)
    
    if has_db:
        st.success("✅ Using live database with scraped UCSB course data")
    elif has_csv:
        st.info("📄 Using CSV file (consider running scraper for live data)")
    else:
        st.warning("⚠️ No course data found. Run the scraper or add CSV file.")

    major = st.selectbox(
        "Select a major",
        list(MAJOR_SHEETS.keys()),
        index=0,
        key="acad_major",
    )

    st.markdown("#### 📚 Major planning resources")
    st.link_button("Open official major sheet", MAJOR_SHEETS[major])

    st.divider()

    tab_classes, tab_search, tab_planner, tab_map, tab_analytics = st.tabs(
        ["Classes by quarter", "Course search", "My planner", "Building map", "Analytics"]
    )

    with tab_classes:
        st.subheader("Classes by quarter")

        quarter = st.selectbox(
            "Quarter",
            ["Winter 2025", "Spring 2025", "Fall 2024"],
            key="acad_quarter",
        )

        courses_df = load_courses_from_db(major, quarter) if has_db else load_courses_df()

        if courses_df is None or courses_df.empty:
            st.info(f"No course data available for **{major}** in **{quarter}**.")
        else:
            if 'major' in courses_df.columns:
                courses_df = courses_df[courses_df['major'] == major]
            
            if 'quarter' in courses_df.columns:
                courses_df = courses_df[courses_df['quarter'] == quarter]

            if courses_df.empty:
                st.info(f"No classes found for **{major}** in **{quarter}**")
            else:
                stats = get_course_stats(courses_df)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total courses", stats['total'])
                col2.metric("🟢 Open", stats['open'])
                col3.metric("🟡 Mixed", stats['mixed'])
                col4.metric("🔴 Full", stats['full'])

                st.markdown("---")

                with st.expander("🔍 Filter options"):
                    filter_col1, filter_col2 = st.columns(2)
                    with filter_col1:
                        status_filter = st.multiselect(
                            "Status",
                            ["Open", "Mixed", "Full"],
                            default=["Open", "Mixed", "Full"]
                        )
                    with filter_col2:
                        if 'instructor' in courses_df.columns:
                            instructors = courses_df['instructor'].dropna().unique()
                            instructor_filter = st.multiselect("Instructor", instructors)
                            if instructor_filter:
                                courses_df = courses_df[courses_df['instructor'].isin(instructor_filter)]
                
                if status_filter:
                    courses_df = courses_df[courses_df['status'].str.title().isin(status_filter)]

                for i in range(0, len(courses_df), 3):
                    cols = st.columns(3, gap="medium")
                    for j in range(3):
                        idx = i + j
                        if idx >= len(courses_df):
                            break
                        row = courses_df.iloc[idx]
                        display_course_card(row, cols[j])

    with tab_search:
        st.subheader("🔍 Search all courses")
        
        search_query = st.text_input("Search by course code or title", placeholder="e.g., PSTAT 120A or Probability")
        
        if search_query and has_db:
            conn = sqlite3.connect(DB_PATH)
            query = '''
                SELECT course_code, title, units, dept, description
                FROM courses
                WHERE course_code LIKE ? OR title LIKE ? OR description LIKE ?
                LIMIT 50
            '''
            search_pattern = f"%{search_query}%"
            results = pd.read_sql_query(query, conn, params=[search_pattern, search_pattern, search_pattern])
            conn.close()
            
            if not results.empty:
                st.success(f"Found {len(results)} courses matching '{search_query}'")
                
                for _, row in results.iterrows():
                    with st.expander(f"{row['course_code']} — {row['title']}"):
                        st.write(f"**Department:** {row['dept']}")
                        st.write(f"**Units:** {row['units']}")
                        if row['description']:
                            st.write(f"**Description:** {row['description']}")
            else:
                st.info("No courses found matching your search.")

    with tab_planner:
        st.subheader("📝 Build your quarter schedule")
        
        if 'planned_courses' not in st.session_state:
            st.session_state.planned_courses = []

        with st.form("add_course_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                new_course = st.text_input("Course code", placeholder="PSTAT 120A")
            with col2:
                new_units = st.number_input("Units", min_value=1, max_value=8, value=4)
            with col3:
                st.write("")
                st.write("")
                add_btn = st.form_submit_button("Add course", use_container_width=True)
            
            if add_btn and new_course:
                st.session_state.planned_courses.append({
                    'Course': new_course,
                    'Units': new_units
                })
                st.rerun()

        if st.session_state.planned_courses:
            df_plan = pd.DataFrame(st.session_state.planned_courses)
            st.dataframe(df_plan, use_container_width=True, hide_index=True)
            
            total_units = df_plan['Units'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("Total units", total_units)
            
            if total_units < 12:
                col2.warning("⚠️ Below minimum (12 units)")
            elif total_units <= 16:
                col2.success("✅ Typical load")
            else:
                col2.error("🔴 Heavy load (>16 units)")
            
            if st.button("Clear all", type="secondary"):
                st.session_state.planned_courses = []
                st.rerun()
        else:
            st.info("No courses planned yet. Add courses above!")

    with tab_map:
        st.subheader("🗺️ Campus building locator")

        bname = st.selectbox("Choose a building", list(BUILDINGS.keys()), key="acad_building")
        lat, lon = BUILDINGS[bname]

        if HAS_FOLIUM:
            m = folium.Map(location=[lat, lon], zoom_start=17, control_scale=True)
            folium.Marker([lat, lon], popup=bname, tooltip=bname).add_to(m)
            st_folium(m, width=900, height=500)
        else:
            st.info("Install folium for interactive map: `pip install folium streamlit-folium`")
            st.json({"building": bname, "latitude": lat, "longitude": lon})

    with tab_analytics:
        st.subheader("📊 Course analytics")
        
        if has_db:
            conn = sqlite3.connect(DB_PATH)
            
            popular_query = '''
                SELECT course_code, enrolled, capacity, 
                       ROUND(CAST(enrolled AS FLOAT) / capacity * 100, 1) as fill_rate
                FROM course_offerings
                WHERE capacity > 0
                ORDER BY fill_rate DESC
                LIMIT 10
            '''
            popular_df = pd.read_sql_query(popular_query, conn)
            
            if not popular_df.empty:
                st.markdown("#### Most in-demand courses")
                st.dataframe(popular_df, use_container_width=True, hide_index=True)
            
            dept_query = '''
                SELECT c.dept, AVG(o.enrolled) as avg_enrollment, COUNT(*) as num_courses
                FROM courses c
                JOIN course_offerings o ON c.course_code = o.course_code
                GROUP BY c.dept
                ORDER BY avg_enrollment DESC
            '''
            dept_df = pd.read_sql_query(dept_query, conn)
            
            if not dept_df.empty:
                st.markdown("#### Average enrollment by department")
                st.bar_chart(dept_df.set_index('dept')['avg_enrollment'])
            
            conn.close()
        else:
            st.info("Run the scraper to see analytics!")
