import sqlite3

conn = sqlite3.connect('ordens.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE ordens ADD COLUMN descricao TEXT")
    print("✅ Coluna 'descricao' adicionada com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erro: {e}")

conn.commit()
conn.close()
