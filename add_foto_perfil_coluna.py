import sqlite3

conn = sqlite3.connect('ordens.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE clientes ADD COLUMN foto_perfil TEXT;')
    print('Coluna foto_perfil adicionada com sucesso!')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('A coluna foto_perfil já existe.')
    else:
        print('Erro ao adicionar coluna:', e)

conn.commit()
conn.close()
