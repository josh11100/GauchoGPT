-- db.sql
-- Schema for GauchoGPT academics data
-- -----------------------------------
-- PRAGMA for safety
PRAGMA foreign_keys = ON;

-- ===================================
-- 1) Catalog-level courses
--    (one row per course: PSTAT 5A, PSTAT 120A, etc.)
-- ===================================
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major TEXT NOT NULL,            -- e.g. 'Statistics & Data Science'
    course_code TEXT NOT NULL,      -- e.g. 'PSTAT 120A'
    title TEXT NOT NULL,            -- e.g. 'PROB & STATISTICS'
    units TEXT,                     -- '4.0', '1.0-4.0', etc
    level TEXT,                     -- optional: 'Lower', 'Upper', 'Grad'

    -- New fields you can fill from ucsbplat.com (catalog-style info)
    description TEXT,               -- full catalog description / "instructions"
    prerequisites TEXT,             -- plain-text prereq info
    additional_info TEXT,           -- anything extra (GE areas, notes, etc.)
    catalog_url TEXT                -- source URL from PLAT / catalog (optional)
);

-- Make sure we don't accidentally duplicate a course for a major
CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_major_code
ON courses (major, course_code);

-- ===================================
-- 2) Quarter-specific offerings
--    (one row per quarter that a course is actually offered)
-- ===================================
CREATE TABLE IF NOT EXISTS offerings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,     -- FK → courses.id

    quarter TEXT NOT NULL,          -- e.g. 'Winter'
    year TEXT,                      -- e.g. '2026'

    status TEXT,                    -- 'Open', 'Mixed', 'Full'
    notes TEXT,                     -- seat counts, GOLD notes, etc.

    -- New: instructor info for each offering
    instructor_name TEXT,           -- e.g. 'Palaniappan, Porter'
    instructor_email TEXT,          -- optional: UCSB email
    meeting_pattern TEXT,           -- 'TR 12:30–1:45 HFH 1104', etc.

    FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_offerings_course_qtr
ON offerings (course_id, year, quarter);

-- ===================================
-- 3) User-specific quarter planner
--    (optional for later when you want per-student plans)
-- ===================================
CREATE TABLE IF NOT EXISTS user_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,          -- SSO user (NetID or email, or just email later)
    quarter TEXT NOT NULL,          -- e.g. 'Winter'
    year TEXT,                      -- e.g. '2026'

    course_code TEXT NOT NULL,      -- e.g. 'PSTAT 120A' (denormalized for convenience)
    units INTEGER,                  -- numeric units for planning
    type TEXT,                      -- 'Major', 'GE', 'Elective', etc.

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_plans_user_term
ON user_plans (user_id, year, quarter);
