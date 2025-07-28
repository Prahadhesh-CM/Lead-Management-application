import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database import LeadDatabase

class LeadManager:
    def __init__(self):
        self.leads_df = None
        self.column_mapping = {}
        self.original_columns = []
        self.db = LeadDatabase()
        
        # Try to load existing data from database
        self.load_from_database()
    
    def load_data(self, df: pd.DataFrame, column_mapping: Dict[str, str]):
        """Load lead data from DataFrame with column mapping"""
        self.leads_df = df.copy()
        self.column_mapping = {k: v for k, v in column_mapping.items() if v}
        self.original_columns = list(df.columns)
        
        # Clean and standardize data types for problematic columns
        self._clean_data_types()
        
        # Add management columns if they don't exist
        if 'priority' not in self.leads_df.columns:
            self.leads_df['priority'] = 'Medium'
        
        if 'follow_up_date' not in self.leads_df.columns:
            self.leads_df['follow_up_date'] = None
        
        if 'last_contact' not in self.leads_df.columns:
            self.leads_df['last_contact'] = None
        
        if 'follow_up_completed' not in self.leads_df.columns:
            self.leads_df['follow_up_completed'] = False
        
        # Standardize column names for internal use
        self._standardize_columns()
        
        # Save to database
        self.save_to_database()
    
    def _clean_data_types(self):
        """Clean and standardize data types to prevent Arrow conversion issues"""
        for col in self.leads_df.columns:
            if self.leads_df[col].dtype == 'object':
                # Convert to string and handle NaN values
                self.leads_df[col] = self.leads_df[col].astype(str)
                # Replace various representations of null/empty values
                null_values = ['nan', 'None', 'NULL', 'null', '<NA>', '']
                for null_val in null_values:
                    self.leads_df[col] = self.leads_df[col].replace(null_val, None)
                
                # Handle multiple values in email and product columns
                self._process_multiple_values(col)
                    
            elif self.leads_df[col].dtype in ['int64', 'float64']:
                # Keep numeric columns as they are but ensure no mixed types
                try:
                    # Try to convert to numeric, if it fails, convert to string
                    pd.to_numeric(self.leads_df[col], errors='raise')
                except (ValueError, TypeError):
                    self.leads_df[col] = self.leads_df[col].astype(str).replace('nan', None)
    
    def _process_multiple_values(self, col):
        """Process columns that might contain multiple values (emails, products, etc.)"""
        # Check if this column likely contains emails or products
        column_name_lower = col.lower()
        is_email_column = any(keyword in column_name_lower for keyword in ['email', 'mail', 'e-mail'])
        is_product_column = any(keyword in column_name_lower for keyword in ['product', 'item', 'service', 'offering'])
        
        if is_email_column or is_product_column:
            # Process each cell to handle multiple values
            for idx in self.leads_df.index:
                cell_value = self.leads_df.loc[idx, col]
                if cell_value and cell_value != 'None':
                    # Split on common separators and clean up
                    separators = [';', ',', '|', '\n', '\r\n']
                    processed_values = [cell_value]
                    
                    for sep in separators:
                        new_values = []
                        for val in processed_values:
                            new_values.extend([v.strip() for v in val.split(sep) if v.strip()])
                        processed_values = new_values
                    
                    # Remove duplicates and join back
                    unique_values = list(dict.fromkeys(processed_values))  # Preserve order
                    if len(unique_values) > 1:
                        # Store as comma-separated for display
                        self.leads_df.loc[idx, col] = ', '.join(unique_values)
    
    def get_multiple_emails(self, lead_idx: int) -> List[str]:
        """Extract multiple email addresses from a lead"""
        email_col = self.column_mapping.get('email', 'email')
        if email_col not in self.leads_df.columns:
            return []
        
        email_value = self.leads_df.loc[lead_idx, email_col]
        if not email_value or email_value == 'None':
            return []
        
        # Split on common separators
        separators = [',', ';', '|', '\n', '\r\n']
        emails = [email_value]
        
        for sep in separators:
            new_emails = []
            for email in emails:
                new_emails.extend([e.strip() for e in email.split(sep) if e.strip()])
            emails = new_emails
        
        # Basic email validation and deduplication
        valid_emails = []
        for email in emails:
            if '@' in email and '.' in email.split('@')[-1]:
                valid_emails.append(email)
        
        return list(dict.fromkeys(valid_emails))  # Remove duplicates while preserving order
    
    def get_multiple_products(self, lead_idx: int) -> List[str]:
        """Extract multiple products from a lead"""
        # Look for product columns
        product_cols = []
        for col in self.leads_df.columns:
            if any(keyword in col.lower() for keyword in ['product', 'item', 'service', 'offering']):
                product_cols.append(col)
        
        # Also check mapped columns
        if self.column_mapping.get('products'):
            product_cols.append(self.column_mapping['products'])
        
        all_products = []
        for col in product_cols:
            if col in self.leads_df.columns:
                product_value = self.leads_df.loc[lead_idx, col]
                if product_value and product_value != 'None':
                    # Split on common separators
                    separators = [',', ';', '|', '\n', '\r\n']
                    products = [product_value]
                    
                    for sep in separators:
                        new_products = []
                        for product in products:
                            new_products.extend([p.strip() for p in product.split(sep) if p.strip()])
                        products = new_products
                    
                    all_products.extend(products)
        
        return list(dict.fromkeys(all_products))  # Remove duplicates while preserving order
    
    def load_from_database(self):
        """Load existing data from database on initialization"""
        try:
            data = self.db.load_leads_data()
            if data:
                df, column_mapping, original_columns = data
                self.leads_df = df
                self.column_mapping = column_mapping
                self.original_columns = original_columns
                print("Loaded existing data from database")
            else:
                print("No existing data found in database")
        except Exception as e:
            print(f"Error loading from database: {e}")
    
    def save_to_database(self):
        """Save current data to database"""
        try:
            if self.has_data():
                success = self.db.save_leads_data(self.leads_df, self.column_mapping, self.original_columns)
                if success:
                    print("Data saved to database successfully")
                else:
                    print("Failed to save data to database")
        except Exception as e:
            print(f"Error saving to database: {e}")
    
    def backup_data(self, backup_path: str = None) -> bool:
        """Create a backup of the current data"""
        try:
            return self.db.backup_database(backup_path)
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _standardize_columns(self):
        """Create standardized column references"""
        for standard_name, mapped_column in self.column_mapping.items():
            if mapped_column and mapped_column in self.leads_df.columns:
                # Create alias for easier access
                if standard_name not in self.leads_df.columns:
                    self.leads_df[standard_name] = self.leads_df[mapped_column]
    
    def has_data(self) -> bool:
        """Check if lead data is loaded"""
        return self.leads_df is not None and not self.leads_df.empty
    
    def get_filtered_leads(self, search_term: str = "", status_filter: str = "All", 
                          priority_filter: str = "All") -> pd.DataFrame:
        """Get filtered leads based on search and filter criteria"""
        if not self.has_data():
            return pd.DataFrame()
        
        try:
            df = self.leads_df.copy()
            
            # Apply search filter
            if search_term:
                search_columns = []
                for col in ['name', 'email', 'company']:
                    if col in df.columns:
                        search_columns.append(col)
                    elif self.column_mapping.get(col) and self.column_mapping[col] in df.columns:
                        search_columns.append(self.column_mapping[col])
                
                if search_columns:
                    search_mask = pd.Series([False] * len(df))
                    for col in search_columns:
                        if col in df.columns:
                            search_mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
                    df = df[search_mask]
            
            # Apply status filter
            if status_filter != "All":
                status_col = self.column_mapping.get('status', 'status')
                if status_col in df.columns:
                    df = df[df[status_col].astype(str).str.contains(status_filter, case=False, na=False)]
            
            # Apply priority filter
            if priority_filter != "All" and 'priority' in df.columns:
                df = df[df['priority'] == priority_filter]
            
            return df
        except Exception as e:
            print(f"Error in get_filtered_leads: {e}")
            return pd.DataFrame()
    
    def get_unique_statuses(self) -> List[str]:
        """Get unique status values from the data"""
        if not self.has_data():
            return []
        
        try:
            status_col = self.column_mapping.get('status', 'status')
            if status_col in self.leads_df.columns:
                unique_statuses = self.leads_df[status_col].dropna().astype(str).unique().tolist()
                return sorted([status for status in unique_statuses if status and status != 'nan'])
            return []
        except Exception as e:
            print(f"Error in get_unique_statuses: {e}")
            return []
    
    def update_lead_status(self, lead_idx: int, new_status: str):
        """Update the status of a specific lead"""
        if not self.has_data():
            return
        
        status_col = self.column_mapping.get('status', 'status')
        if status_col not in self.leads_df.columns:
            self.leads_df['status'] = None
            status_col = 'status'
        
        # Track the change
        old_status = self.leads_df.loc[lead_idx, status_col] if lead_idx in self.leads_df.index else None
        self.db.update_lead_field(lead_idx, 'status', old_status, new_status)
        
        self.leads_df.loc[lead_idx, status_col] = new_status
        self.leads_df.loc[lead_idx, 'last_contact'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save to database
        self.save_to_database()
    
    def update_lead_priority(self, lead_idx: int, new_priority: str):
        """Update the priority of a specific lead"""
        if not self.has_data():
            return
        
        # Track the change
        old_priority = self.leads_df.loc[lead_idx, 'priority'] if lead_idx in self.leads_df.index else None
        self.db.update_lead_field(lead_idx, 'priority', old_priority, new_priority)
        
        self.leads_df.loc[lead_idx, 'priority'] = new_priority
        
        # Save to database
        self.save_to_database()
    
    def schedule_followup(self, lead_idx: int, follow_up_date):
        """Schedule a follow-up for a specific lead"""
        if not self.has_data():
            return
        
        if isinstance(follow_up_date, str):
            follow_up_date = pd.Timestamp(follow_up_date)
        else:
            follow_up_date = pd.Timestamp(follow_up_date)
        
        # Track the change
        old_date = self.leads_df.loc[lead_idx, 'follow_up_date'] if lead_idx in self.leads_df.index else None
        self.db.update_lead_field(lead_idx, 'follow_up_date', old_date, follow_up_date)
        
        self.leads_df.loc[lead_idx, 'follow_up_date'] = follow_up_date
        self.leads_df.loc[lead_idx, 'follow_up_completed'] = False
        
        # Save to database
        self.save_to_database()
    
    def add_note(self, lead_idx: int, note: str):
        """Add a note to a specific lead"""
        if not self.has_data() or not note.strip():
            return
        
        notes_col = self.column_mapping.get('notes', 'notes')
        if notes_col not in self.leads_df.columns:
            self.leads_df['notes'] = ''
            notes_col = 'notes'
        
        current_note = self.leads_df.loc[lead_idx, notes_col]
        if pd.isna(current_note) or current_note == '':
            new_note = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}"
        else:
            new_note = f"{current_note}\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}"
        
        # Track the change
        self.db.update_lead_field(lead_idx, 'notes', current_note, new_note)
        
        self.leads_df.loc[lead_idx, notes_col] = new_note
        
        # Save to database
        self.save_to_database()
    
    def get_upcoming_followups(self, days_ahead: int = 7) -> pd.DataFrame:
        """Get follow-ups scheduled for the next specified days"""
        if not self.has_data():
            return pd.DataFrame()
        
        today = pd.Timestamp.now().normalize()
        end_date = today + pd.Timedelta(days=days_ahead)
        
        # Convert follow_up_date to datetime if it's not already
        follow_up_dates = pd.to_datetime(self.leads_df['follow_up_date'], errors='coerce')
        
        # Filter for upcoming follow-ups
        mask = (
            (self.leads_df['follow_up_date'].notna()) &
            (self.leads_df['follow_up_completed'] == False) &
            (follow_up_dates >= today) &
            (follow_up_dates <= end_date)
        )
        
        upcoming = self.leads_df[mask].copy()
        if not upcoming.empty:
            upcoming = upcoming.sort_values('follow_up_date')
        
        return upcoming
    
    def get_overdue_followups(self) -> pd.DataFrame:
        """Get overdue follow-ups"""
        if not self.has_data():
            return pd.DataFrame()
        
        today = pd.Timestamp.now().normalize()
        
        # Convert follow_up_date to datetime if it's not already
        follow_up_dates = pd.to_datetime(self.leads_df['follow_up_date'], errors='coerce')
        
        # Filter for overdue follow-ups
        mask = (
            (self.leads_df['follow_up_date'].notna()) &
            (self.leads_df['follow_up_completed'] == False) &
            (follow_up_dates < today)
        )
        
        overdue = self.leads_df[mask].copy()
        if not overdue.empty:
            overdue = overdue.sort_values('follow_up_date')
        
        return overdue
    
    def get_daily_tasks(self, date) -> pd.DataFrame:
        """Get tasks scheduled for a specific date"""
        if not self.has_data():
            return pd.DataFrame()
        
        if isinstance(date, str):
            target_date = pd.Timestamp(date).normalize()
        else:
            target_date = pd.Timestamp(date).normalize()
        
        # Convert follow_up_date to datetime if it's not already
        follow_up_dates = pd.to_datetime(self.leads_df['follow_up_date'], errors='coerce')
        
        # Filter for tasks on the specified date
        mask = (
            (self.leads_df['follow_up_date'].notna()) &
            (self.leads_df['follow_up_completed'] == False) &
            (follow_up_dates.dt.normalize() == target_date)
        )
        
        daily_tasks = self.leads_df[mask].copy()
        if not daily_tasks.empty:
            # Sort by priority (High, Medium, Low) and then by follow_up_date
            priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
            daily_tasks['priority_order'] = daily_tasks['priority'].map(priority_order).fillna(2)
            daily_tasks = daily_tasks.sort_values(['priority_order', 'follow_up_date'], 
                                                ascending=[False, True])
            daily_tasks = daily_tasks.drop('priority_order', axis=1)
        
        return daily_tasks
    
    def complete_followup(self, lead_idx: int):
        """Mark a follow-up as completed"""
        if not self.has_data():
            return
        
        # Track the change
        self.db.update_lead_field(lead_idx, 'follow_up_completed', False, True)
        
        self.leads_df.loc[lead_idx, 'follow_up_completed'] = True
        self.leads_df.loc[lead_idx, 'last_contact'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save to database
        self.save_to_database()
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and insights from the lead data"""
        if not self.has_data():
            return {
                'total_leads': 0,
                'active_followups': 0,
                'overdue_tasks': 0,
                'qualified_leads': 0,
                'status_distribution': {},
                'priority_distribution': {}
            }
        
        today = pd.Timestamp.now().normalize()
        
        # Basic metrics
        total_leads = len(self.leads_df)
        active_followups = len(self.leads_df[
            (self.leads_df['follow_up_date'].notna()) & 
            (self.leads_df['follow_up_completed'] == False)
        ])
        
        # Convert follow_up_date to datetime for comparison
        follow_up_dates = pd.to_datetime(self.leads_df['follow_up_date'], errors='coerce')
        
        overdue_tasks = len(self.leads_df[
            (self.leads_df['follow_up_date'].notna()) & 
            (self.leads_df['follow_up_completed'] == False) &
            (follow_up_dates < today)
        ])
        
        # Status distribution
        status_col = self.column_mapping.get('status', 'status')
        status_distribution = {}
        if status_col in self.leads_df.columns:
            status_distribution = self.leads_df[status_col].dropna().value_counts().to_dict()
        
        # Priority distribution
        priority_distribution = self.leads_df['priority'].dropna().value_counts().to_dict()
        
        # Qualified leads (assuming 'qualified' or 'closed' status means qualified)
        qualified_leads = 0
        if status_col in self.leads_df.columns:
            qualified_statuses = ['qualified', 'closed', 'won']
            for status in qualified_statuses:
                qualified_leads += self.leads_df[status_col].astype(str).str.lower().str.contains(status, na=False).sum()
        
        return {
            'total_leads': total_leads,
            'active_followups': active_followups,
            'overdue_tasks': overdue_tasks,
            'qualified_leads': qualified_leads,
            'status_distribution': status_distribution,
            'priority_distribution': priority_distribution
        }
