# ucsb_course_scraper.py
"""
Scrapes UCSB public course catalog and stores in SQL database.
Run this periodically to keep your course data fresh.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime
import time
import re

class UCSBCourseScraper:
    def __init__(self, db_path="gauchoGPT.db"):
        self.db_path = db_path
        self.base_url = "https://my.sa.ucsb.edu/public/curriculum/coursesearch.aspx"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_department_courses(self, dept_code):
        """
        Scrape courses for a specific department
        dept_code examples: 'PSTAT', 'CMPSC', 'ECON', 'MATH'
        """
        print(f"Scraping {dept_code} courses...")
        
        try:
            # This is a simplified example - you'll need to inspect the actual UCSB page
            # to get the correct form parameters and parsing logic
            
            params = {
                'dept': dept_code,
                'quarter': '20251'  # Winter 2025 (format: YYYYQ where Q: 1=Winter, 2=Spring, 3=Summer, 4=Fall)
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            courses = []
            
            # NOTE: You'll need to inspect the actual HTML structure of the UCSB page
            # This is a template - adjust selectors based on actual page structure
            course_rows = soup.find_all('tr', class_='course-row')  # Adjust selector
            
            for row in course_rows:
                try:
                    course_data = {
                        'dept': dept_code,
                        'course_code': self._extract_text(row, '.course-code'),
                        'title': self._extract_text(row, '.course-title'),
                        'units': self._extract_units(row),
                        'description': self._extract_text(row, '.course-description'),
                        'prerequisites': self._extract_text(row, '.prerequisites'),
                        'instructor': self._extract_text(row, '.instructor'),
                        'days': self._extract_text(row, '.days'),
                        'time': self._extract_text(row, '.time'),
                        'location': self._extract_text(row, '.location'),
                        'enrollment': self._extract_enrollment(row),
                        'status': self._determine_status(row),
                        'scraped_at': datetime.now().isoformat()
                    }
                    courses.append(course_data)
                except Exception as e:
                    print(f"Error parsing course row: {e}")
                    continue
            
            time.sleep(1)  # Be respectful to the server
            return courses
            
        except Exception as e:
            print(f"Error scraping {dept_code}: {e}")
            return []
    
    def _extract_text(self, element, selector):
        """Helper to safely extract text from element"""
        found = element.select_one(selector)
        return found.get_text(strip=True) if found else ""
    
    def _extract_units(self, row):
        """Extract unit count from course row"""
        units_text = self._extract_text(row, '.units')
        match = re.search(r'(\d+)', units_text)
        return int(match.group(1)) if match else None
    
    def _extract_enrollment(self, row):
        """Extract enrollment numbers (enrolled/capacity)"""
        enroll_text = self._extract_text(row, '.enrollment')
        # Example: "45/50" -> returns dict
        match = re.search(r'(\d+)/(\d+)', enroll_text)
        if match:
            return {
                'enrolled': int(match.group(1)),
                'capacity': int(match.group(2))
            }
        return {'enrolled': 0, 'capacity': 0}
    
    def _determine_status(self, row):
        """Determine if course is Open, Full, or Waitlist"""
        enroll = self._extract_enrollment(row)
        if enroll['enrolled'] >= enroll['capacity']:
            return "Full"
        elif enroll['enrolled'] >= enroll['capacity'] * 0.9:
            return "Mixed"
        else:
            return "Open"
    
    def scrape_all_departments(self):
        """Scrape courses from all major departments"""
        departments = [
            'PSTAT',  # Statistics
            'CMPSC',  # Computer Science
            'ECON',   # Economics
            'MATH',   # Mathematics
            'MCDB',   # Bio
            'PSY',    # Psychology
            'CHEM',   # Chemistry
            'PHYS',   # Physics
            'PHIL',   # Philosophy
            'ENGL',   # English
        ]
        
        all_courses = []
        for dept in departments:
            courses = self.scrape_department_courses(dept)
            all_courses.extend(courses)
            print(f"Found {len(courses)} courses in {dept}")
        
        return pd.DataFrame(all_courses)
    
    def create_database_schema(self):
        """Create SQL database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept TEXT,
                course_code TEXT UNIQUE,
                title TEXT,
                units INTEGER,
                description TEXT,
                prerequisites TEXT,
                quarter TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Course offerings table (for specific quarters/sections)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_offerings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT,
                quarter TEXT,
                section TEXT,
                instructor TEXT,
                days TEXT,
                time TEXT,
                location TEXT,
                enrolled INTEGER,
                capacity INTEGER,
                status TEXT,
                scraped_at TIMESTAMP,
                FOREIGN KEY (course_code) REFERENCES courses(course_code)
            )
        ''')
        
        # Professors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                department TEXT,
                rating REAL,
                difficulty REAL,
                num_ratings INTEGER,
                office_location TEXT,
                email TEXT
            )
        ''')
        
        # User query log (for analytics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT,
                query_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_feedback INTEGER
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_course_dept ON courses(dept)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offering_quarter ON course_offerings(quarter)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offering_status ON course_offerings(status)')
        
        conn.commit()
        conn.close()
        print("Database schema created successfully!")
    
    def save_to_database(self, df):
        """Save scraped data to SQL database"""
        conn = sqlite3.connect(self.db_path)
        
        # Save to courses table
        courses_df = df[['dept', 'course_code', 'title', 'units', 'description', 'prerequisites']].copy()
        courses_df['quarter'] = 'Winter 2025'
        courses_df = courses_df.drop_duplicates(subset=['course_code'])
        
        courses_df.to_sql('courses', conn, if_exists='append', index=False)
        
        # Save to course_offerings table
        offerings_df = df[['course_code', 'instructor', 'days', 'time', 'location', 
                          'enrollment', 'status', 'scraped_at']].copy()
        offerings_df['quarter'] = 'Winter 2025'
        offerings_df['section'] = '01'  # Default section
        
        # Flatten enrollment dict
        if 'enrollment' in offerings_df.columns:
            offerings_df['enrolled'] = offerings_df['enrollment'].apply(lambda x: x.get('enrolled', 0) if isinstance(x, dict) else 0)
            offerings_df['capacity'] = offerings_df['enrollment'].apply(lambda x: x.get('capacity', 0) if isinstance(x, dict) else 0)
            offerings_df = offerings_df.drop('enrollment', axis=1)
        
        offerings_df.to_sql('course_offerings', conn, if_exists='append', index=False)
        
        conn.close()
        print(f"Saved {len(df)} courses to database!")
    
    def query_courses(self, dept=None, status=None, quarter=None):
        """Query courses from database with filters"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT c.course_code, c.title, c.units, c.dept,
                   o.instructor, o.days, o.time, o.location, 
                   o.enrolled, o.capacity, o.status, o.quarter
            FROM courses c
            LEFT JOIN course_offerings o ON c.course_code = o.course_code
            WHERE 1=1
        '''
        
        params = []
        if dept:
            query += " AND c.dept = ?"
            params.append(dept)
        if status:
            query += " AND o.status = ?"
            params.append(status)
        if quarter:
            query += " AND o.quarter = ?"
            params.append(quarter)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df


def main():
    """Main execution function"""
    scraper = UCSBCourseScraper()
    
    # Step 1: Create database
    print("Creating database schema...")
    scraper.create_database_schema()
    
    # Step 2: Scrape courses
    print("\nScraping UCSB courses...")
    courses_df = scraper.scrape_all_departments()
    
    if not courses_df.empty:
        print(f"\nScraped {len(courses_df)} total courses")
        print(courses_df.head())
        
        # Step 3: Save to database
        print("\nSaving to database...")
        scraper.save_to_database(courses_df)
        
        # Step 4: Test query
        print("\nQuerying PSTAT courses...")
        pstat_courses = scraper.query_courses(dept='PSTAT')
        print(pstat_courses)
    else:
        print("No courses scraped. Check the scraper configuration.")


if __name__ == "__main__":
    main()
