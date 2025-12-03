import sqlite3
from models.database import get_db_path

conn = sqlite3.connect(get_db_path())
cursor = conn.cursor()

# Adiciona a coluna senha_pura se não existir
try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN senha_pura TEXT")
    print('Coluna senha_pura adicionada com sucesso!')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('Coluna senha_pura já existe.')
    else:
        print('Erro:', e)

conn.commit()
conn.close()
