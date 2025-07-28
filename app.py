import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
from lead_manager import LeadManager

# Initialize the lead manager with error handling
if 'lead_manager' not in st.session_state:
    try:
        st.session_state.lead_manager = LeadManager()
        # Show a status message if existing data was loaded
        if st.session_state.lead_manager.has_data():
            st.sidebar.success("✅ Previous data loaded from database")
    except Exception as e:
        st.error(f"Error initializing application: {str(e)}")
        st.info("The application will continue to work, but data persistence may be limited.")
        # Create a basic lead manager without database functionality
        from lead_manager import LeadManager
        st.session_state.lead_manager = LeadManager()

def main():
    st.set_page_config(
        page_title="Lead Generation & Management System",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Lead Generation & Management System")
    st.markdown("Upload your Excel file to start managing leads, follow-ups, and daily tasks.")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Upload Data", "Lead Management", "Follow-ups & Reminders", "Daily To-Do List", "Analytics", "Database Management"]
    )
    
    if page == "Upload Data":
        upload_data_page()
    elif page == "Lead Management":
        lead_management_page()
    elif page == "Follow-ups & Reminders":
        followups_page()
    elif page == "Daily To-Do List":
        todo_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Database Management":
        database_management_page()

def upload_data_page():
    st.header("📁 Upload Lead Data")
    
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload your Excel file containing lead data. The system will automatically detect columns."
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} rows and {len(df.columns)} columns.")
            
            # Display file info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            
            # Show column information
            st.subheader("📋 Detected Columns")
            columns_info = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                non_null = df[col].notna().sum()
                columns_info.append({
                    "Column Name": col,
                    "Data Type": dtype,
                    "Non-null Values": f"{non_null}/{len(df)}"
                })
            
            st.dataframe(pd.DataFrame(columns_info), use_container_width=True)
            
            # Preview data
            st.subheader("📊 Data Preview")
            # Clean the dataframe for display to avoid Arrow conversion issues
            display_df = df.head(10).copy()
            for col in display_df.columns:
                if display_df[col].dtype == 'object':
                    display_df[col] = display_df[col].astype(str)
            st.dataframe(display_df, use_container_width=True)
            
            # Column mapping for lead management
            st.subheader("🔗 Column Mapping")
            st.markdown("Map your columns to standard lead fields (optional but recommended):")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name_col = st.selectbox("Name/Company Column", [""] + list(df.columns))
                email_col = st.selectbox("Email Column", [""] + list(df.columns))
                phone_col = st.selectbox("Phone Column", [""] + list(df.columns))
            
            with col2:
                company_col = st.selectbox("Company Column", [""] + list(df.columns))
                status_col = st.selectbox("Status Column", [""] + list(df.columns))
                source_col = st.selectbox("Source Column", [""] + list(df.columns))
            
            with col3:
                notes_col = st.selectbox("Notes Column", [""] + list(df.columns))
                date_col = st.selectbox("Date Column", [""] + list(df.columns))
                value_col = st.selectbox("Deal Value Column", [""] + list(df.columns))
                products_col = st.selectbox("Products Column", [""] + list(df.columns))
            
            if st.button("💾 Save Lead Data", type="primary"):
                # Store the data and mappings
                column_mapping = {
                    'name': name_col,
                    'email': email_col,
                    'phone': phone_col,
                    'company': company_col,
                    'status': status_col,
                    'source': source_col,
                    'notes': notes_col,
                    'date': date_col,
                    'value': value_col,
                    'products': products_col
                }
                
                st.session_state.lead_manager.load_data(df, column_mapping)
                st.success("🎉 Lead data saved successfully! Navigate to 'Lead Management' to start managing your leads.")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please ensure the file is a valid Excel file (.xlsx or .xls)")

def lead_management_page():
    st.header("👥 Lead Management")
    
    if not st.session_state.lead_manager.has_data():
        st.warning("⚠️ No lead data found. Please upload an Excel file first.")
        return
    
    # Search and filter section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search leads", placeholder="Enter name, email, or company...")
    
    with col2:
        status_filter = st.selectbox("📊 Filter by Status", 
                                   ["All"] + st.session_state.lead_manager.get_unique_statuses())
    
    with col3:
        priority_filter = st.selectbox("⭐ Filter by Priority", 
                                     ["All", "High", "Medium", "Low"])
    
    # Get filtered leads
    try:
        leads_df = st.session_state.lead_manager.get_filtered_leads(search_term, status_filter, priority_filter)
        
        if len(leads_df) == 0:
            st.info("No leads found matching your criteria.")
            return
    except Exception as e:
        st.error(f"Error retrieving leads: {str(e)}")
        return
    
    st.subheader(f"📋 Leads ({len(leads_df)} found)")
    
    # Clean the dataframe for display to avoid Arrow conversion issues
    display_leads = leads_df.copy()
    for col in display_leads.columns:
        if display_leads[col].dtype == 'object':
            display_leads[col] = display_leads[col].astype(str).replace('nan', 'N/A')
    
    # Display leads with action buttons
    for idx, lead in display_leads.iterrows():
        # Get display values safely
        name = str(lead.get('name', lead.get(st.session_state.lead_manager.column_mapping.get('name', ''), 'Unknown')))
        status = str(lead.get('status', lead.get(st.session_state.lead_manager.column_mapping.get('status', ''), 'No Status')))
        
        with st.expander(f"👤 {name} - {status}"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Handle multiple emails
                multiple_emails = st.session_state.lead_manager.get_multiple_emails(idx)
                if multiple_emails:
                    if len(multiple_emails) == 1:
                        st.write("📧 **Email:**", multiple_emails[0])
                    else:
                        st.write("📧 **Emails:**")
                        for i, email in enumerate(multiple_emails):
                            st.write(f"   • {email}")
                else:
                    email = str(lead.get('email', lead.get(st.session_state.lead_manager.column_mapping.get('email', ''), 'N/A')))
                    st.write("📧 **Email:**", email)
                
                phone = str(lead.get('phone', lead.get(st.session_state.lead_manager.column_mapping.get('phone', ''), 'N/A')))
                company = str(lead.get('company', lead.get(st.session_state.lead_manager.column_mapping.get('company', ''), 'N/A')))
                
                st.write("📞 **Phone:**", phone)
                st.write("🏢 **Company:**", company)
                st.write("📊 **Status:**", status)
            
            with col2:
                source = str(lead.get('source', lead.get(st.session_state.lead_manager.column_mapping.get('source', ''), 'N/A')))
                value = str(lead.get('value', lead.get(st.session_state.lead_manager.column_mapping.get('value', ''), 'N/A')))
                priority = str(lead.get('priority', 'Medium'))
                last_contact = str(lead.get('last_contact', 'Never'))
                
                st.write("🎯 **Source:**", source)
                st.write("💰 **Value:**", value)
                st.write("⭐ **Priority:**", priority)
                st.write("📅 **Last Contact:**", last_contact)
                
                # Handle multiple products
                multiple_products = st.session_state.lead_manager.get_multiple_products(idx)
                if multiple_products:
                    if len(multiple_products) == 1:
                        st.write("🛍️ **Product:**", multiple_products[0])
                    else:
                        st.write("🛍️ **Products:**")
                        for product in multiple_products:
                            st.write(f"   • {product}")
            
            notes = lead.get('notes', lead.get(st.session_state.lead_manager.column_mapping.get('notes', ''), ''))
            if notes and str(notes) != 'nan':
                st.write("📝 **Notes:**", str(notes))
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                new_status = st.selectbox(f"Update Status", 
                                        ["contacted", "interested", "not_interested", "follow_up", "qualified", "closed"],
                                        key=f"status_{idx}")
                if st.button("Update Status", key=f"update_status_{idx}"):
                    try:
                        st.session_state.lead_manager.update_lead_status(idx, new_status)
                        st.success("Status updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating status: {str(e)}")
            
            with col2:
                new_priority = st.selectbox(f"Update Priority", 
                                          ["High", "Medium", "Low"],
                                          key=f"priority_{idx}")
                if st.button("Update Priority", key=f"update_priority_{idx}"):
                    try:
                        st.session_state.lead_manager.update_lead_priority(idx, new_priority)
                        st.success("Priority updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating priority: {str(e)}")
            
            with col3:
                follow_up_date = st.date_input("Schedule Follow-up", key=f"followup_{idx}")
                if st.button("Schedule", key=f"schedule_{idx}"):
                    try:
                        st.session_state.lead_manager.schedule_followup(idx, follow_up_date)
                        st.success("Follow-up scheduled!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error scheduling follow-up: {str(e)}")
            
            with col4:
                new_notes = st.text_area("Add Notes", key=f"notes_{idx}", height=100)
                if st.button("Add Note", key=f"add_note_{idx}"):
                    try:
                        if new_notes.strip():
                            st.session_state.lead_manager.add_note(idx, new_notes)
                            st.success("Note added!")
                            st.rerun()
                        else:
                            st.warning("Please enter a note before adding.")
                    except Exception as e:
                        st.error(f"Error adding note: {str(e)}")

def followups_page():
    st.header("📅 Follow-ups & Reminders")
    
    if not st.session_state.lead_manager.has_data():
        st.warning("⚠️ No lead data found. Please upload an Excel file first.")
        return
    
    # Get upcoming follow-ups
    try:
        upcoming_followups = st.session_state.lead_manager.get_upcoming_followups()
        overdue_followups = st.session_state.lead_manager.get_overdue_followups()
    except Exception as e:
        st.error(f"Error retrieving follow-ups: {str(e)}")
        return
    
    # Overdue follow-ups
    if len(overdue_followups) > 0:
        st.subheader("🚨 Overdue Follow-ups")
        st.error(f"You have {len(overdue_followups)} overdue follow-ups!")
        
        for _, followup in overdue_followups.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    name = str(followup.get('name', followup.get(st.session_state.lead_manager.column_mapping.get('name', ''), 'Unknown')))
                    due_date = str(followup.get('follow_up_date', 'N/A'))
                    st.write(f"👤 **{name}**")
                    st.write(f"📅 Due: {due_date}")
                
                with col2:
                    status = str(followup.get('status', followup.get(st.session_state.lead_manager.column_mapping.get('status', ''), 'N/A')))
                    priority = str(followup.get('priority', 'Medium'))
                    st.write(f"📊 Status: {status}")
                    st.write(f"⭐ Priority: {priority}")
                
                with col3:
                    if st.button("Mark Complete", key=f"complete_overdue_{followup.name}"):
                        st.session_state.lead_manager.complete_followup(followup.name)
                        st.success("Follow-up marked as complete!")
                        st.rerun()
                
                st.divider()
    
    # Upcoming follow-ups
    st.subheader("📋 Upcoming Follow-ups")
    if len(upcoming_followups) == 0:
        st.info("🎉 No upcoming follow-ups scheduled!")
    else:
        for _, followup in upcoming_followups.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    name = str(followup.get('name', followup.get(st.session_state.lead_manager.column_mapping.get('name', ''), 'Unknown')))
                    due_date = str(followup.get('follow_up_date', 'N/A'))
                    st.write(f"👤 **{name}**")
                    st.write(f"📅 Due: {due_date}")
                
                with col2:
                    status = str(followup.get('status', followup.get(st.session_state.lead_manager.column_mapping.get('status', ''), 'N/A')))
                    priority = str(followup.get('priority', 'Medium'))
                    st.write(f"📊 Status: {status}")
                    st.write(f"⭐ Priority: {priority}")
                
                with col3:
                    if st.button("Mark Complete", key=f"complete_{followup.name}"):
                        st.session_state.lead_manager.complete_followup(followup.name)
                        st.success("Follow-up marked as complete!")
                        st.rerun()
                
                st.divider()

def todo_page():
    st.header("✅ Daily To-Do List")
    
    if not st.session_state.lead_manager.has_data():
        st.warning("⚠️ No lead data found. Please upload an Excel file first.")
        return
    
    # Date selector
    selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
    
    # Get tasks for the selected date
    try:
        daily_tasks = st.session_state.lead_manager.get_daily_tasks(selected_date)
    except Exception as e:
        st.error(f"Error retrieving daily tasks: {str(e)}")
        return
    
    if len(daily_tasks) == 0:
        st.info(f"🎉 No tasks scheduled for {selected_date}")
        return
    
    st.subheader(f"📋 Tasks for {selected_date} ({len(daily_tasks)} tasks)")
    
    # Group tasks by priority
    high_priority = daily_tasks[daily_tasks.get('priority', 'Medium') == 'High']
    medium_priority = daily_tasks[daily_tasks.get('priority', 'Medium') == 'Medium']
    low_priority = daily_tasks[daily_tasks.get('priority', 'Medium') == 'Low']
    
    # Display high priority tasks
    if len(high_priority) > 0:
        st.markdown("### 🔴 High Priority")
        for _, task in high_priority.iterrows():
            display_task(task)
    
    # Display medium priority tasks
    if len(medium_priority) > 0:
        st.markdown("### 🟡 Medium Priority")
        for _, task in medium_priority.iterrows():
            display_task(task)
    
    # Display low priority tasks
    if len(low_priority) > 0:
        st.markdown("### 🟢 Low Priority")
        for _, task in low_priority.iterrows():
            display_task(task)

def display_task(task):
    with st.container():
        col1, col2, col3 = st.columns([4, 2, 1])
        
        with col1:
            name = str(task.get('name', task.get(st.session_state.lead_manager.column_mapping.get('name', ''), 'Unknown')))
            phone = str(task.get('phone', task.get(st.session_state.lead_manager.column_mapping.get('phone', ''), 'N/A')))
            
            st.write(f"👤 **{name}**")
            st.write(f"📞 {phone}")
            
            # Handle multiple emails in tasks
            multiple_emails = st.session_state.lead_manager.get_multiple_emails(task.name)
            if multiple_emails:
                email_text = " | ".join(multiple_emails[:2])  # Show first 2 emails
                if len(multiple_emails) > 2:
                    email_text += f" (+{len(multiple_emails)-2} more)"
                st.write(f"📧 {email_text}")
            else:
                email = str(task.get('email', task.get(st.session_state.lead_manager.column_mapping.get('email', ''), 'N/A')))
                st.write(f"📧 {email}")
            
            notes = task.get('notes', task.get(st.session_state.lead_manager.column_mapping.get('notes', ''), ''))
            if notes and str(notes) != 'nan':
                st.write(f"📝 {str(notes)}")
                
            # Show products if available
            multiple_products = st.session_state.lead_manager.get_multiple_products(task.name)
            if multiple_products:
                product_text = " | ".join(multiple_products[:2])  # Show first 2 products
                if len(multiple_products) > 2:
                    product_text += f" (+{len(multiple_products)-2} more)"
                st.write(f"🛍️ {product_text}")
        
        with col2:
            status = str(task.get('status', task.get(st.session_state.lead_manager.column_mapping.get('status', ''), 'N/A')))
            company = str(task.get('company', task.get(st.session_state.lead_manager.column_mapping.get('company', ''), 'N/A')))
            
            st.write(f"📊 Status: {status}")
            st.write(f"🏢 Company: {company}")
        
        with col3:
            if st.button("✅ Complete", key=f"task_complete_{task.name}"):
                st.session_state.lead_manager.complete_followup(task.name)
                st.success("Task completed!")
                st.rerun()
        
        st.divider()

def analytics_page():
    st.header("📊 Analytics & Insights")
    
    if not st.session_state.lead_manager.has_data():
        st.warning("⚠️ No lead data found. Please upload an Excel file first.")
        return
    
    # Get analytics data
    try:
        analytics = st.session_state.lead_manager.get_analytics()
    except Exception as e:
        st.error(f"Error retrieving analytics: {str(e)}")
        return
    
    # Key metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", analytics['total_leads'])
    
    with col2:
        st.metric("Active Follow-ups", analytics['active_followups'])
    
    with col3:
        st.metric("Overdue Tasks", analytics['overdue_tasks'])
    
    with col4:
        conversion_rate = (analytics['qualified_leads'] / analytics['total_leads'] * 100) if analytics['total_leads'] > 0 else 0
        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    
    # Status distribution
    st.subheader("📊 Lead Status Distribution")
    if analytics['status_distribution']:
        status_df = pd.DataFrame(list(analytics['status_distribution'].items()), 
                               columns=['Status', 'Count'])
        st.bar_chart(status_df.set_index('Status'))
    
    # Priority distribution
    st.subheader("⭐ Priority Distribution")
    if analytics['priority_distribution']:
        priority_df = pd.DataFrame(list(analytics['priority_distribution'].items()), 
                                 columns=['Priority', 'Count'])
        st.bar_chart(priority_df.set_index('Priority'))

def database_management_page():
    st.header("🗄️ Database Management")
    
    if not st.session_state.lead_manager.has_data():
        st.info("📋 No lead data found. Upload an Excel file or check the Database Management page to reload existing data.")
        # Don't return here - still show database management options
        st.markdown("---")
    
    # Database Statistics
    st.subheader("📊 Database Statistics")
    try:
        stats = st.session_state.lead_manager.db.get_database_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Datasets Stored", stats.get('leads_datasets', 0))
        with col2:
            st.metric("Total Updates", stats.get('total_updates', 0))
        with col3:
            st.metric("Database Size", f"{stats.get('database_size_mb', 0)} MB")
        
        st.info(f"📁 Database Location: {stats.get('database_path', 'Unknown')}")
        
    except Exception as e:
        st.error(f"Error retrieving database statistics: {str(e)}")
    
    # Data Backup and Recovery
    st.subheader("💾 Data Backup & Recovery")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Create Backup**")
        backup_name = st.text_input("Backup filename (optional)", placeholder="my_backup.db")
        
        if st.button("📥 Create Backup", type="secondary"):
            try:
                backup_path = backup_name if backup_name.strip() else None
                success = st.session_state.lead_manager.backup_data(backup_path)
                if success:
                    st.success(f"✅ Backup created successfully!")
                    if backup_path:
                        st.info(f"Backup saved as: {backup_path}")
                else:
                    st.error("❌ Failed to create backup")
            except Exception as e:
                st.error(f"Error creating backup: {str(e)}")
    
    with col2:
        st.markdown("**Auto-Save Status**")
        st.success("🟢 Auto-save is ENABLED")
        st.info("All changes are automatically saved to the database to prevent data loss during connection issues.")
    
    # Data Recovery Information
    st.subheader("🔄 Data Recovery")
    st.markdown("""
    **Your data is protected:**
    - ✅ All changes are automatically saved to a local SQLite database
    - ✅ Data persists even if the connection is lost
    - ✅ Lead updates, follow-ups, and notes are tracked with timestamps  
    - ✅ Database is stored locally in the application directory
    - ✅ You can create manual backups anytime
    
    **In case of connection issues:**
    1. Your data remains safe in the local database
    2. Simply refresh the page to reload your data
    3. All your leads, follow-ups, and notes will be restored
    """)
    
    # Force Data Reload
    st.subheader("🔄 Force Data Reload")
    st.markdown("If you experience any data display issues, you can force reload from the database:")
    
    if st.button("🔄 Reload Data from Database", type="secondary"):
        try:
            st.session_state.lead_manager.load_from_database()
            st.success("✅ Data reloaded from database successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error reloading data: {str(e)}")

if __name__ == "__main__":
    main()
