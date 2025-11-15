import sqlite3

def init_db():
    conn = sqlite3.connect('ordens.db')
    cursor = conn.cursor()
    # Tabela de clientes (multi-tenant)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_assistencia TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            senha_pura TEXT,
            data_cadastro TEXT NOT NULL,
            trial_ativo INTEGER DEFAULT 1,
            data_fim_trial TEXT,
            assinatura_ativa INTEGER DEFAULT 0,
            data_ultimo_pagamento TEXT,
            pix_pagamento TEXT DEFAULT 'comicsultimate@gmail.com'
        )
    ''')
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