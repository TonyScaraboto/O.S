import sqlite3
import os
from datetime import datetime

def get_db_path():
    if os.environ.get('VERCEL_ENV'):
        return '/tmp/ordens.db'
    return 'ordens.db'

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def ensure_column(table, column_name, column_def, default_value=None):
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
            if default_value is not None:
                cursor.execute(f"UPDATE {table} SET {column_name}=?", (default_value,))
    # Tabela de clientes (multi-tenant)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_assistencia TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_cadastro TEXT NOT NULL,
            trial_ativo INTEGER DEFAULT 1,
            data_fim_trial TEXT,
            assinatura_ativa INTEGER DEFAULT 0,
            data_ultimo_pagamento TEXT,
            pix_pagamento TEXT DEFAULT 'comicsultimate@gmail.com'
        )
    ''')

    # Ajusta colunas que podem faltar em bancos antigos
    ensure_column('clientes', 'foto_perfil', 'TEXT')
    ensure_column('clientes', 'senha_pura', 'TEXT')
    ensure_column('clientes', 'pix_pagamento', "TEXT DEFAULT 'comicsultimate@gmail.com'", 'comicsultimate@gmail.com')
    ensure_column('clientes', 'assinatura_ativa', 'INTEGER DEFAULT 0', 0)
    ensure_column('clientes', 'trial_ativo', 'INTEGER DEFAULT 1', 1)
    ensure_column('clientes', 'data_cadastro', 'TEXT', datetime.now().strftime('%Y-%m-%d'))
    ensure_column('clientes', 'data_fim_trial', 'TEXT')
    # Inserção de admin padrão na tabela clientes
    cursor.execute('''
        INSERT OR IGNORE INTO clientes (nome_assistencia, email, senha, senha_pura, data_cadastro, trial_ativo, data_fim_trial, assinatura_ativa)
        VALUES ('ADMIN', 'admin@saas.com', 'admin123', 'admin123', '2024-01-01', 0, NULL, 1)
    ''')

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            telefone TEXT NOT NULL,
            aparelho TEXT NOT NULL,
            defeito TEXT NOT NULL,
            valor REAL NOT NULL,
            status TEXT NOT NULL,
            imagem TEXT,
            data_criacao TEXT NOT NULL
        )
    ''')

    # Tabela de vendas de acessórios (multi-tenant)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acessorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            receita_total REAL NOT NULL,
            data_venda TEXT NOT NULL,
            cliente TEXT NOT NULL
        )
    ''')

    # Inserção de usuários padrão
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (username, password, role)
        VALUES 
            ('admin', 'admin123', 'admin'),
            ('tecnico', 'tecnico123', 'tecnico')
    ''')

    conn.commit()
    conn.close()