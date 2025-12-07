CREATE DATABASE IF NOT EXISTS scartech_saas
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE scartech_saas;

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_assistencia VARCHAR(255) NOT NULL,
    nome_usuario VARCHAR(255),
    email VARCHAR(191) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    senha_pura VARCHAR(255),
    data_cadastro DATE NOT NULL,
    trial_ativo TINYINT(1) DEFAULT 1,
    data_fim_trial DATE,
    assinatura_ativa TINYINT(1) DEFAULT 0,
    data_ultimo_pagamento DATE,
    pix_pagamento VARCHAR(255) DEFAULT 'comicsultimate@gmail.com',
    foto_perfil TEXT,
    plano_nome VARCHAR(255),
    plano_valor DECIMAL(10,2),
    wooxy_charge_id VARCHAR(255),
    wooxy_qr_code TEXT,
    wooxy_copia_cola TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(191) UNIQUE,
    password VARCHAR(255),
    role VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS ordens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente TEXT NOT NULL,
    telefone TEXT NOT NULL,
    aparelho TEXT NOT NULL,
    defeito TEXT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    status VARCHAR(100) NOT NULL,
    imagem TEXT,
    data_criacao DATETIME NOT NULL,
    nome_cliente TEXT,
    fornecedor TEXT,
    custo_peca DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS acessorios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome TEXT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    receita_total DECIMAL(10,2) NOT NULL,
    data_venda DATETIME NOT NULL,
    cliente TEXT NOT NULL,
    imagem TEXT
);

INSERT IGNORE INTO clientes (
    nome_assistencia, nome_usuario, email, senha, senha_pura, data_cadastro,
    trial_ativo, assinatura_ativa, pix_pagamento
) VALUES (
    'ADMIN', 'ADMIN', 'admin@saas.com', 'admin123', 'admin123', '2024-01-01',
    0, 1, 'comicsultimate@gmail.com'
);

UPDATE clientes
   SET nome_usuario = nome_assistencia
 WHERE nome_usuario IS NULL
    OR nome_usuario = '';

INSERT IGNORE INTO usuarios (username, password, role)
VALUES
    ('admin', 'admin123', 'admin'),
    ('tecnico', 'tecnico123', 'tecnico');