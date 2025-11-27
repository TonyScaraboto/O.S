import sqlite3
import bcrypt
from models.database import get_db_path

# Caminho do banco
DB_PATH = get_db_path()

# Dados do novo admin
novo_admin = {
    'username': 'admin2',
    'email': 'admin2@saas.com',
    'password': 'admin456',
    'role': 'admin',
    'nome_assistencia': 'Assistência Admin2',
    'assinatura_ativa': 1,
    'foto_perfil': None
}

# Criptografa a senha
senha_hash = bcrypt.hashpw(novo_admin['password'].encode('utf-8'), bcrypt.gensalt())

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Cria usuário admin2 na tabela usuarios
cursor.execute('''
    INSERT OR IGNORE INTO usuarios (username, password, role)
    VALUES (?, ?, ?)
''', (novo_admin['username'], senha_hash, novo_admin['role']))

# Cria cliente admin2 na tabela clientes
cursor.execute('''
    INSERT OR IGNORE INTO clientes (email, nome_assistencia, assinatura_ativa, foto_perfil)
    VALUES (?, ?, ?, ?)
''', (novo_admin['email'], novo_admin['nome_assistencia'], novo_admin['assinatura_ativa'], novo_admin['foto_perfil']))

conn.commit()
conn.close()

print('Usuário admin2 criado com sucesso!')
