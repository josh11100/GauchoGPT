"""
ETL Pipeline for GauchoGPT
Extract, Transform, Load operations for housing and course data
"""
import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import requests

from db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL pipeline for scraping and processing housing/course data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # ===== EXTRACT =====
    
    def extract_housing_csv(self, csv_path: str) -> pd.DataFrame:
        """Extract housing data from CSV"""
        logger.info(f"Extracting housing data from {csv_path}")
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Extracted {len(df)} records from CSV")
            return df
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return pd.DataFrame()
    
    def extract_housing_web(self, url: str) -> List[Dict]:
        """Extract housing data from web scraping (placeholder)"""
        logger.info(f"Scraping housing data from {url}")
        # This would use BeautifulSoup to scrape actual websites
        # For now, return empty list
        return []
    
    def extract_courses_csv(self, csv_path: str) -> pd.DataFrame:
        """Extract course data from CSV"""
        logger.info(f"Extracting course data from {csv_path}")
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Extracted {len(df)} course records")
            return df
        except Exception as e:
            logger.error(f"Error reading course CSV: {e}")
            return pd.DataFrame()
    
    # ===== TRANSFORM =====
    
    def transform_housing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform housing data"""
        logger.info("Transforming housing data")
        
        if df.empty:
            return df
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Ensure required columns exist
        required_cols = {
            'street': str,
            'unit': str,
            'price': float,
            'bedrooms': float,
            'bathrooms': float,
            'max_residents': float,
            'status': str,
        }
        
        for col, dtype in required_cols.items():
            if col not in df.columns:
                if dtype == str:
                    df[col] = ''
                else:
                    df[col] = np.nan
        
        # Clean price - remove $ and commas
        if 'price' in df.columns:
            df['price'] = df['price'].astype(str).str.replace('$', '').str.replace(',', '')
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Clean bedrooms/bathrooms
        for col in ['bedrooms', 'bathrooms', 'max_residents']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Identify studios (0 bedrooms or "studio" in description)
        df['is_studio'] = df['bedrooms'].fillna(0).eq(0)
        if 'unit' in df.columns:
            df['is_studio'] = df['is_studio'] | df['unit'].str.lower().str.contains('studio', na=False)
        
        # Clean status
        if 'status' not in df.columns:
            df['status'] = 'available'
        df['status'] = df['status'].fillna('available').str.lower()
        
        # Pet friendly boolean
        if 'pet_friendly' not in df.columns and 'pet_policy' in df.columns:
            df['pet_friendly'] = df['pet_policy'].str.lower().str.contains('friendly|allowed', na=False)
        elif 'pet_friendly' not in df.columns:
            df['pet_friendly'] = False
        
        # Calculate price per person
        df['price_per_person'] = df['price'] / df['max_residents']
        df.loc[df['max_residents'].isna() | (df['max_residents'] == 0), 'price_per_person'] = np.nan
        
        # Drop duplicates
        if 'street' in df.columns and 'unit' in df.columns:
            df = df.drop_duplicates(subset=['street', 'unit'], keep='last')
        
        # Handle missing dates
        for col in ['avail_start', 'avail_end']:
            if col not in df.columns:
                df[col] = ''
        
        logger.info(f"Transformed {len(df)} housing records")
        return df
    
    def transform_course_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform course data"""
        logger.info("Transforming course data")
        
        if df.empty:
            return df
        
        df = df.copy()
        
        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Required columns
        required_cols = ['major', 'course_code', 'title']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return pd.DataFrame()
        
        # Clean course codes (uppercase, remove extra spaces)
        df['course_code'] = df['course_code'].str.upper().str.strip()
        
        # Clean major names
        df['major'] = df['major'].str.strip()
        
        # Standardize quarter names
        if 'quarter' in df.columns:
            df['quarter'] = df['quarter'].str.strip().str.title()
        
        # Clean status
        if 'status' in df.columns:
            df['status'] = df['status'].str.lower().str.strip()
        
        # Drop duplicates
        df = df.drop_duplicates(subset=['major', 'course_code'], keep='last')
        
        logger.info(f"Transformed {len(df)} course records")
        return df
    
    # ===== LOAD =====
    
    def load_housing_data(self, df: pd.DataFrame):
        """Load housing data into database"""
        logger.info("Loading housing data into database")
        
        if df.empty:
            logger.warning("No housing data to load")
            return
        
        # Prepare DataFrame for database insertion
        db_columns = [
            'street', 'unit', 'price', 'bedrooms', 'bathrooms', 'max_residents',
            'status', 'avail_start', 'avail_end', 'utilities', 'pet_policy',
            'pet_friendly', 'is_studio', 'latitude', 'longitude'
        ]
        
        # Ensure all columns exist
        for col in db_columns:
            if col not in df.columns:
                df[col] = None if col not in ['pet_friendly', 'is_studio'] else False
        
        # Select only needed columns
        df_load = df[db_columns].copy()
        
        # Insert into database
        self.db.bulk_insert_housing(df_load)
        logger.info(f"Loaded {len(df_load)} housing records")
    
    def load_course_data(self, df: pd.DataFrame):
        """Load course data into database"""
        logger.info("Loading course data into database")
        
        if df.empty:
            logger.warning("No course data to load")
            return
        
        # Insert courses
        for _, row in df.iterrows():
            course_data = {
                'major': row['major'],
                'course_code': row['course_code'],
                'title': row['title'],
                'units': row.get('units'),
                'level': row.get('level'),
                'description': row.get('description')
            }
            course_id = self.db.insert_course(course_data)
            
            # If quarter info exists, create offering
            if 'quarter' in row and pd.notna(row['quarter']):
                offering_data = {
                    'course_id': course_id,
                    'quarter': row['quarter'],
                    'year': row.get('year'),
                    'status': row.get('status'),
                    'instructor': row.get('instructor'),
                    'seats_available': row.get('seats_available'),
                    'notes': row.get('notes')
                }
                self.load_course_offering(offering_data)
        
        logger.info(f"Loaded {len(df)} course records")
    
    def load_course_offering(self, data: Dict[str, Any]):
        """Load a course offering"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO offerings (
                    course_id, quarter, year, status, instructor,
                    seats_available, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data['course_id'], data['quarter'], data.get('year'),
                data.get('status'), data.get('instructor'),
                data.get('seats_available'), data.get('notes')
            ))
    
    # ===== FULL ETL PIPELINES =====
    
    def run_housing_pipeline(self, csv_path: str):
        """Run full ETL pipeline for housing data"""
        logger.info("=== Starting Housing ETL Pipeline ===")
        
        # Extract
        df = self.extract_housing_csv(csv_path)
        if df.empty:
            logger.error("No data extracted")
            return
        
        # Transform
        df = self.transform_housing_data(df)
        if df.empty:
            logger.error("Transformation failed")
            return
        
        # Load
        self.load_housing_data(df)
        
        logger.info("=== Housing ETL Pipeline Complete ===")
    
    def run_course_pipeline(self, csv_path: str):
        """Run full ETL pipeline for course data"""
        logger.info("=== Starting Course ETL Pipeline ===")
        
        # Extract
        df = self.extract_courses_csv(csv_path)
        if df.empty:
            logger.error("No data extracted")
            return
        
        # Transform
        df = self.transform_course_data(df)
        if df.empty:
            logger.error("Transformation failed")
            return
        
        # Load
        self.load_course_data(df)
        
        logger.info("=== Course ETL Pipeline Complete ===")
    
    # ===== DATA QUALITY CHECKS =====
    
    def validate_housing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run data quality checks on housing data"""
        report = {
            'total_records': len(df),
            'missing_values': {},
            'invalid_values': {},
            'warnings': []
        }
        
        # Check for missing critical fields
        critical_fields = ['street', 'price', 'bedrooms']
        for field in critical_fields:
            if field in df.columns:
                missing = df[field].isna().sum()
                if missing > 0:
                    report['missing_values'][field] = missing
        
        # Check for invalid prices
        if 'price' in df.columns:
            invalid_prices = (df['price'] < 0) | (df['price'] > 10000)
            if invalid_prices.any():
                report['invalid_values']['price'] = invalid_prices.sum()
        
        # Check for invalid bedrooms
        if 'bedrooms' in df.columns:
            invalid_beds = (df['bedrooms'] < 0) | (df['bedrooms'] > 10)
            if invalid_beds.any():
                report['invalid_values']['bedrooms'] = invalid_beds.sum()
        
        return report
