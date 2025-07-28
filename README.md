# 📘 Detailed Documentation – Lead Manager Application

## Overview

The **Lead Manager App** is a modular and scalable lead tracking system developed in Python. It serves as a lightweight CRM backend focused on efficient lead data processing, activity tracking, and follow-up management. By integrating `pandas`, `sqlite3`, and optionally `streamlit`, it supports seamless data import, manipulation, and persistent storage.

This application is particularly useful for:
- Maintaining structured lead records
- Tracking engagement and contact history
- Prioritizing outreach efforts
- Analyzing lead health and pipeline performance

---

## 🔧 Core Components

### 1. `lead_manager.py`
Handles:
- Loading and cleaning raw lead data
- Mapping user-supplied columns
- Normalizing email/product fields
- Managing priority, follow-ups, and notes
- Filtering and analytics

### 2. `database.py`
SQLite persistence layer:
- Tables: `leads`, `lead_updates`, `app_state`
- Saves/loads data as JSON
- Tracks all field changes
- Supports database backup

### 3. `leads.db`
- Stores lead data, updates, and optional app state

### 4. `config.toml`
Deployment config:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

### 5. `requirements.txt`
Dependencies:
- `pandas`, `numpy`, `openpyxl`, `streamlit`

---

## ⚙️ Functional Flow

1. **Input**: Load leads with pandas DataFrame
2. **Normalization**: Clean nulls, mixed types, and multi-value fields
3. **Lead Management**:
   - Update status/priority
   - Schedule/complete follow-ups
   - Add timestamped notes
4. **Analytics**:
   - Total leads, follow-ups, qualified status
   - Priority and status distribution
5. **Persistence**:
   - Auto-save/load to `leads.db`
   - Change tracking and backup

---

## 📈 Use Cases

- Sales CRM for tracking pipelines
- Campaign response tracking
- Customer support task scheduling
- Lead qualification scoring

---

## 🧠 Why Use This?

- ✅ Fully local and lightweight
- ✅ No third-party CRM dependencies
- ✅ Easy to integrate into Streamlit dashboards
- ✅ Modular for automation or analytics

---
