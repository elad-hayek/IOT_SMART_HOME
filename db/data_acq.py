# db/data_acq.py - Data acquisition and SQLite operations
import sqlite3
from sqlite3 import Error
from datetime import datetime
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DB_NAME, DB_PATH, DATA_TABLE

class DataAcquisition:
    """SQLite database operations for IoT data storage"""
    
    def __init__(self, db_file=None):
        if db_file is None:
            db_file = os.path.join(DB_PATH, DB_NAME)
        self.db_file = db_file
        self.conn = None
        self._ensure_db_dir()
        self.create_connection()
        self.create_table()
    
    def _ensure_db_dir(self):
        """Create database directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
    
    def create_connection(self):
        """Create database connection"""
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            print(f"[DB] Connected to {self.db_file}")
            return self.conn
        except Error as e:
            print(f"[DB ERROR] {e}")
            return None
    
    def create_table(self):
        """Create iot_data table if it doesn't exist"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {DATA_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            device_name TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value REAL,
            unit TEXT,
            severity TEXT DEFAULT 'normal'
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_sql)
            self.conn.commit()
            print(f"[DB] Table '{DATA_TABLE}' ready")
        except Error as e:
            print(f"[DB ERROR] Table creation failed: {e}")
    
    def add_iot_data(self, timestamp, device_name, sensor_type, value, unit='', severity='normal'):
        """Insert a new IoT data record"""
        insert_sql = f"""
        INSERT INTO {DATA_TABLE} (timestamp, device_name, sensor_type, value, unit, severity)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(insert_sql, (timestamp, device_name, sensor_type, value, unit, severity))
            self.conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"[DB ERROR] Insert failed: {e}")
            return None
    
    def fetch_latest_by_device(self, device_name, limit=1):
        """Get latest readings for a specific device"""
        query = f"""
        SELECT * FROM {DATA_TABLE}
        WHERE device_name = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        try:
            df = pd.read_sql_query(query, self.conn, params=[device_name, limit])
            return df
        except Error as e:
            print(f"[DB ERROR] Fetch failed: {e}")
            return pd.DataFrame()
    
    def fetch_range(self, device_name, sensor_type=None, limit=1000):
        """Get data range for a device (for charting)"""
        if sensor_type:
            query = f"""
            SELECT timestamp, value, unit FROM {DATA_TABLE}
            WHERE device_name = ? AND sensor_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            params = [device_name, sensor_type, limit]
        else:
            query = f"""
            SELECT timestamp, value, unit FROM {DATA_TABLE}
            WHERE device_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            params = [device_name, limit]
        
        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            return df.iloc[::-1]  # Reverse to get chronological order
        except Error as e:
            print(f"[DB ERROR] Fetch range failed: {e}")
            return pd.DataFrame()
    
    def get_alarm_count(self):
        """Get count of recent alerts"""
        query = f"""
        SELECT COUNT(*) as count FROM {DATA_TABLE}
        WHERE severity IN ('warning', 'alert')
        AND datetime(timestamp) > datetime('now', '-1 hour')
        """
        try:
            df = pd.read_sql_query(query, self.conn)
            return df.iloc[0]['count']
        except Error as e:
            print(f"[DB ERROR] Alarm count failed: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("[DB] Connection closed")

# Singleton instance
da = DataAcquisition()
