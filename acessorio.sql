CREATE TABLE IF NOT EXISTS acessorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL,
    receita_total REAL NOT NULL,
    data_venda TEXT NOT NULL
);