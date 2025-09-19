#!/usr/bin/env python3
"""
WhatsApp Medical Reminder Bot
Ponto de entrada principal para deploy
"""

import os
import sys
import sqlite3

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def init_database():
    """Initialize SQLite database with required tables"""
    
    db_path = 'app.db'
    
    # Check if database already exists and has tables
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wa_campaigns'")
        if cursor.fetchone():
            conn.close()
            print("✅ Database already initialized")
            return
        conn.close()
    
    print("🚀 Initializing database...")
    
    # Create database and tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create tables
        tables = [
            '''CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone_e164 TEXT NOT NULL UNIQUE,
                tags TEXT,
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS wa_campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                template_name TEXT NOT NULL,
                lang_code TEXT NOT NULL DEFAULT 'pt_BR',
                params_mode TEXT NOT NULL DEFAULT 'fixed',
                fixed_params TEXT,
                tz TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
                start_at DATETIME NOT NULL,
                end_at DATETIME,
                frequency TEXT NOT NULL DEFAULT 'once',
                days_of_week TEXT,
                day_of_month INTEGER,
                send_time TEXT NOT NULL,
                cron_expr TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS wa_campaign_recipients (
                campaign_id TEXT NOT NULL,
                phone_e164 TEXT NOT NULL,
                per_params TEXT,
                PRIMARY KEY (campaign_id, phone_e164),
                FOREIGN KEY (campaign_id) REFERENCES wa_campaigns(id) ON DELETE CASCADE
            )''',
            
            '''CREATE TABLE IF NOT EXISTS wa_campaign_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                run_at DATETIME NOT NULL,
                phone_e164 TEXT NOT NULL,
                payload TEXT,
                wa_response TEXT,
                status TEXT NOT NULL DEFAULT 'ok',
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES wa_campaigns(id) ON DELETE CASCADE
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        # Create indexes
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone_e164)',
            'CREATE INDEX IF NOT EXISTS idx_patients_active ON patients(active)',
            'CREATE INDEX IF NOT EXISTS idx_campaigns_status ON wa_campaigns(status)',
            'CREATE INDEX IF NOT EXISTS idx_campaigns_frequency ON wa_campaigns(frequency)',
            'CREATE INDEX IF NOT EXISTS idx_campaigns_start_at ON wa_campaigns(start_at)',
            'CREATE INDEX IF NOT EXISTS idx_campaign_runs_campaign_id ON wa_campaign_runs(campaign_id)',
            'CREATE INDEX IF NOT EXISTS idx_campaign_runs_run_at ON wa_campaign_runs(run_at)',
            'CREATE INDEX IF NOT EXISTS idx_campaign_runs_status ON wa_campaign_runs(status)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

# Initialize database before importing the app
init_database()

from src.main import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

