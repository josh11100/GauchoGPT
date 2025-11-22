-- Courses offered at UCSB (logical courses, not specific quarters)
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major TEXT NOT NULL,           -- e.g. 'Statistics & Data Science'
    course_code TEXT NOT NULL,     -- e.g. 'PSTAT 120A'
    title TEXT NOT NULL,           -- e.g. 'PROB & STATISTICS'
    units TEXT,                    -- '4.0', '1.0-4.0', etc
    level TEXT                     -- optional: 'Lower', 'Upper', 'Grad'
);

-- Specific offerings by quarter (like your CSV)
CREATE TABLE IF NOT EXISTS offerings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    quarter TEXT NOT NULL,         -- 'Winter'
    year TEXT,                     -- optional: '2026'
    status TEXT,                   -- 'Open', 'Mixed', 'Full'
    notes TEXT,                    -- seat counts, etc
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- User planner saved per login ID
CREATE TABLE IF NOT EXISTS user_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,         -- SSO user (NetID or email)
    quarter TEXT NOT NULL,         -- e.g. 'Winter 2026'
    course_code TEXT NOT NULL,     -- e.g. 'PSTAT 120A'
    units INTEGER,
    type TEXT                      -- Major / GE / Elective
);
