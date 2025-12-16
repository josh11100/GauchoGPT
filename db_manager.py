"""
Database Manager for GauchoGPT
Handles all SQLite database operations with proper connection pooling
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database manager with connection pooling"""
    
    def __init__(self, db_path: str = "gauchoGPT.db"):
        self.db_path = db_path
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def initialize_database(self):
        """Create all necessary tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Housing table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS housing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    street TEXT NOT NULL,
                    unit TEXT,
                    price REAL,
                    bedrooms INTEGER,
                    bathrooms REAL,
                    max_residents INTEGER,
                    status TEXT DEFAULT 'available',
                    avail_start TEXT,
                    avail_end TEXT,
                    utilities TEXT,
                    pet_policy TEXT,
                    pet_friendly BOOLEAN DEFAULT 0,
                    is_studio BOOLEAN DEFAULT 0,
                    latitude REAL,
                    longitude REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Courses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    major TEXT NOT NULL,
                    course_code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    units TEXT,
                    level TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(major, course_code)
                )
            """)
            
            # Course offerings by quarter
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offerings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    quarter TEXT NOT NULL,
                    year TEXT,
                    status TEXT,
                    instructor TEXT,
                    seats_available INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(id)
                )
            """)
            
            # Professor reviews (for ML analysis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS professor_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_name TEXT NOT NULL,
                    department TEXT,
                    course_code TEXT,
                    rating REAL,
                    difficulty REAL,
                    review_text TEXT,
                    review_date TEXT,
                    sentiment_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User planner
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    quarter TEXT NOT NULL,
                    course_code TEXT NOT NULL,
                    units INTEGER,
                    type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Housing clusters (for K-Means)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS housing_clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    housing_id INTEGER NOT NULL,
                    cluster_id INTEGER NOT NULL,
                    cluster_label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (housing_id) REFERENCES housing(id)
                )
            """)
            
            logger.info("Database initialized successfully")
    
    # ===== HOUSING OPERATIONS =====
    
    def insert_housing(self, data: Dict[str, Any]) -> int:
        """Insert a single housing listing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO housing (
                    street, unit, price, bedrooms, bathrooms, max_residents,
                    status, avail_start, avail_end, utilities, pet_policy,
                    pet_friendly, is_studio, latitude, longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('street'), data.get('unit'), data.get('price'),
                data.get('bedrooms'), data.get('bathrooms'), data.get('max_residents'),
                data.get('status', 'available'), data.get('avail_start'),
                data.get('avail_end'), data.get('utilities'), data.get('pet_policy'),
                data.get('pet_friendly', False), data.get('is_studio', False),
                data.get('latitude'), data.get('longitude')
            ))
            return cursor.lastrowid
    
    def get_housing_listings(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Get housing listings with optional filters"""
        with self.get_connection() as conn:
            query = "SELECT * FROM housing WHERE 1=1"
            params = []
            
            if filters:
                if 'max_price' in filters:
                    query += " AND (price IS NULL OR price <= ?)"
                    params.append(filters['max_price'])
                
                if 'bedrooms' in filters:
                    query += " AND bedrooms = ?"
                    params.append(filters['bedrooms'])
                
                if 'status' in filters:
                    query += " AND status = ?"
                    params.append(filters['status'])
                
                if 'pet_friendly' in filters:
                    query += " AND pet_friendly = ?"
                    params.append(filters['pet_friendly'])
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
    
    def bulk_insert_housing(self, df: pd.DataFrame):
        """Bulk insert housing data from DataFrame"""
        with self.get_connection() as conn:
            df.to_sql('housing', conn, if_exists='append', index=False)
            logger.info(f"Inserted {len(df)} housing records")
    
    # ===== COURSE OPERATIONS =====
    
    def insert_course(self, data: Dict[str, Any]) -> int:
        """Insert or update a course"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO courses (major, course_code, title, units, level, description)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(major, course_code) DO UPDATE SET
                    title = excluded.title,
                    units = excluded.units,
                    level = excluded.level,
                    description = excluded.description
            """, (
                data['major'], data['course_code'], data['title'],
                data.get('units'), data.get('level'), data.get('description')
            ))
            return cursor.lastrowid
    
    def get_courses_by_major(self, major: str) -> pd.DataFrame:
        """Get all courses for a major"""
        with self.get_connection() as conn:
            query = """
                SELECT c.*, o.quarter, o.year, o.status, o.instructor
                FROM courses c
                LEFT JOIN offerings o ON c.id = o.course_id
                WHERE c.major = ?
                ORDER BY c.course_code
            """
            return pd.read_sql_query(query, conn, params=[major])
    
    def get_courses_by_quarter(self, major: str, quarter: str) -> pd.DataFrame:
        """Get courses offered in a specific quarter"""
        with self.get_connection() as conn:
            query = """
                SELECT c.*, o.quarter, o.year, o.status, o.seats_available, o.instructor
                FROM courses c
                INNER JOIN offerings o ON c.id = o.course_id
                WHERE c.major = ? AND o.quarter = ?
                ORDER BY c.course_code
            """
            return pd.read_sql_query(query, conn, params=[major, quarter])
    
    # ===== PROFESSOR REVIEW OPERATIONS =====
    
    def insert_review(self, data: Dict[str, Any]) -> int:
        """Insert a professor review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO professor_reviews (
                    professor_name, department, course_code, rating,
                    difficulty, review_text, review_date, sentiment_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['professor_name'], data.get('department'), data.get('course_code'),
                data.get('rating'), data.get('difficulty'), data['review_text'],
                data.get('review_date'), data.get('sentiment_score')
            ))
            return cursor.lastrowid
    
    def get_professor_reviews(self, professor_name: str) -> pd.DataFrame:
        """Get all reviews for a professor"""
        with self.get_connection() as conn:
            query = "SELECT * FROM professor_reviews WHERE professor_name = ?"
            return pd.read_sql_query(query, conn, params=[professor_name])
    
    # ===== CLUSTERING OPERATIONS =====
    
    def save_housing_clusters(self, housing_ids: List[int], cluster_ids: List[int], 
                               cluster_labels: List[str]):
        """Save K-Means clustering results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Clear old clusters
            cursor.execute("DELETE FROM housing_clusters")
            
            # Insert new clusters
            data = list(zip(housing_ids, cluster_ids, cluster_labels))
            cursor.executemany("""
                INSERT INTO housing_clusters (housing_id, cluster_id, cluster_label)
                VALUES (?, ?, ?)
            """, data)
            logger.info(f"Saved {len(data)} housing cluster assignments")
    
    def get_housing_with_clusters(self) -> pd.DataFrame:
        """Get housing data with cluster assignments"""
        with self.get_connection() as conn:
            query = """
                SELECT h.*, hc.cluster_id, hc.cluster_label
                FROM housing h
                LEFT JOIN housing_clusters hc ON h.id = hc.housing_id
            """
            return pd.read_sql_query(query, conn)
    
    # ===== ANALYTICS =====
    
    def get_housing_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for housing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total listings
            cursor.execute("SELECT COUNT(*) FROM housing")
            stats['total_listings'] = cursor.fetchone()[0]
            
            # Available listings
            cursor.execute("SELECT COUNT(*) FROM housing WHERE status = 'available'")
            stats['available_listings'] = cursor.fetchone()[0]
            
            # Average price
            cursor.execute("SELECT AVG(price) FROM housing WHERE price IS NOT NULL")
            stats['avg_price'] = cursor.fetchone()[0]
            
            # Price range
            cursor.execute("SELECT MIN(price), MAX(price) FROM housing WHERE price IS NOT NULL")
            min_price, max_price = cursor.fetchone()
            stats['price_range'] = (min_price, max_price)
            
            return stats
