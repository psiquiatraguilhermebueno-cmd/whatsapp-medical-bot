#!/usr/bin/env python3
"""
Script para inicializar o banco de dados SQLite com as tabelas necessárias
"""

import os
import sys
import sqlite3
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_tables():
    """Criar as tabelas necessárias no banco SQLite"""
    
    # Caminho do banco de dados
    db_path = 'app.db'
    
    print(f"Criando banco de dados em: {db_path}")
    
    # Conectar ao banco SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Criar tabela patients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone_e164 TEXT NOT NULL UNIQUE,
                tags TEXT,
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela wa_campaigns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wa_campaigns (
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
            )
        ''')
        
        # Criar tabela wa_campaign_recipients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wa_campaign_recipients (
                campaign_id TEXT NOT NULL,
                phone_e164 TEXT NOT NULL,
                per_params TEXT,
                PRIMARY KEY (campaign_id, phone_e164),
                FOREIGN KEY (campaign_id) REFERENCES wa_campaigns(id) ON DELETE CASCADE
            )
        ''')
        
        # Criar tabela wa_campaign_runs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wa_campaign_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                run_at DATETIME NOT NULL,
                phone_e164 TEXT NOT NULL,
                payload TEXT,
                wa_response TEXT,
                status TEXT NOT NULL DEFAULT 'ok',
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES wa_campaigns(id) ON DELETE CASCADE
            )
        ''')
        
        # Criar índices
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
        
        # Commit das mudanças
        conn.commit()
        
        print("✅ Tabelas criadas com sucesso!")
        
        # Verificar se as tabelas foram criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\n📋 Tabelas criadas:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()
    
    return True

if __name__ == '__main__':
    print("🚀 Inicializando banco de dados...")
    
    if create_tables():
        print("\n✅ Banco de dados inicializado com sucesso!")
        print("🎯 Agora você pode usar a interface admin sem erros.")
    else:
        print("\n❌ Falha ao inicializar o banco de dados.")
        sys.exit(1)
