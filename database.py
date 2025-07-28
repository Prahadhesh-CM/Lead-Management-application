import sqlite3
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class LeadDatabase:
    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create leads table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_json TEXT NOT NULL,
            column_mapping_json TEXT NOT NULL,
            original_columns_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create lead_updates table for tracking changes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lead_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_row_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create app_state table for storing session state
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY,
            state_key TEXT UNIQUE NOT NULL,
            state_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_leads_data(self, df: pd.DataFrame, column_mapping: Dict[str, str], original_columns: List[str]) -> bool:
        """Save leads data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert DataFrame to JSON
            data_json = df.to_json(orient='records', date_format='iso')
            column_mapping_json = json.dumps(column_mapping)
            original_columns_json = json.dumps(original_columns)
            
            # Clear existing data and insert new data
            cursor.execute('DELETE FROM leads')
            cursor.execute('''
            INSERT INTO leads (data_json, column_mapping_json, original_columns_json, updated_at)
            VALUES (?, ?, ?, ?)
            ''', (data_json, column_mapping_json, original_columns_json, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving leads data: {e}")
            return False
    
    def load_leads_data(self) -> Optional[tuple]:
        """Load leads data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT data_json, column_mapping_json, original_columns_json FROM leads ORDER BY updated_at DESC LIMIT 1')
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                data_json, column_mapping_json, original_columns_json = result
                df = pd.read_json(data_json, orient='records')
                column_mapping = json.loads(column_mapping_json)
                original_columns = json.loads(original_columns_json)
                return df, column_mapping, original_columns
            
            return None
        except Exception as e:
            print(f"Error loading leads data: {e}")
            return None
    
    def update_lead_field(self, lead_row_id: int, field_name: str, old_value: Any, new_value: Any):
        """Track lead field updates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO lead_updates (lead_row_id, field_name, old_value, new_value)
            VALUES (?, ?, ?, ?)
            ''', (lead_row_id, field_name, str(old_value), str(new_value)))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error tracking lead update: {e}")
    
    def save_app_state(self, state_key: str, state_value: Any):
        """Save application state"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            state_json = json.dumps(state_value) if not isinstance(state_value, str) else state_value
            
            cursor.execute('''
            INSERT OR REPLACE INTO app_state (state_key, state_value, updated_at)
            VALUES (?, ?, ?)
            ''', (state_key, state_json, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving app state: {e}")
    
    def load_app_state(self, state_key: str) -> Optional[Any]:
        """Load application state"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT state_value FROM app_state WHERE state_key = ?', (state_key,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return result[0]
            
            return None
        except Exception as e:
            print(f"Error loading app state: {e}")
            return None
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Create a backup of the database"""
        try:
            if backup_path is None:
                backup_path = f"leads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get leads count
            cursor.execute('SELECT COUNT(*) FROM leads')
            leads_count = cursor.fetchone()[0]
            
            # Get updates count
            cursor.execute('SELECT COUNT(*) FROM lead_updates')
            updates_count = cursor.fetchone()[0]
            
            # Get database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            conn.close()
            
            return {
                'leads_datasets': leads_count,
                'total_updates': updates_count,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'database_path': self.db_path
            }
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}