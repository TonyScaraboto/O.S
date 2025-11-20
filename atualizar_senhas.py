<<<<<<< HEAD

import sqlite3
import bcrypt

def hash_if_needed(senha):
    if senha is None:
        return None
    # Se já for hash bcrypt, não altera
    if senha.startswith('$2b$') or senha.startswith('$2a$'):
        return senha
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def atualizar_senhas():
    conn = sqlite3.connect('ordens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM usuarios')
    usuarios = cursor.fetchall()
    for uid, senha in usuarios:
        nova = hash_if_needed(senha)
        if nova != senha:
            cursor.execute('UPDATE usuarios SET password=? WHERE id=?', (nova, uid))
    cursor.execute('SELECT id, senha FROM clientes')
    clientes = cursor.fetchall()
    for cid, senha in clientes:
        nova = hash_if_needed(senha)
        if nova != senha:
            cursor.execute('UPDATE clientes SET senha=? WHERE id=?', (nova, cid))
    conn.commit()
    conn.close()
    print('Senhas atualizadas com sucesso!')

if __name__ == '__main__':
    atualizar_senhas()
=======
import sqlite3
import bcrypt

 

def hash_if_needed(senha):
    if senha is None:
        return None
    # Se já for hash bcrypt, não altera
    if senha.startswith('$2b$') or senha.startswith('$2a$'):
        return senha
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def atualizar_senhas():
    conn = sqlite3.connect('ordens.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, password FROM usuarios')
    usuarios = cursor.fetchall()
    for uid, senha in usuarios:
        nova = hash_if_needed(senha)
        if nova != senha:
            cursor.execute('UPDATE usuarios SET password=? WHERE id=?', (nova, uid))
    
    cursor.execute('SELECT id, senha FROM clientes')
    clientes = cursor.fetchall()
    for cid, senha in clientes:
        nova = hash_if_needed(senha)
        if nova != senha:
            cursor.execute('UPDATE clientes SET senha=? WHERE id=?', (nova, cid))
    conn.commit()
    conn.close()
    print('Senhas atualizadas com sucesso!')

if __name__ == '__main__':
    atualizar_senhas()
>>>>>>> 1b805bc (Multi-tenant: cada assistência vê apenas seus dados, correções de acesso, painel e faturamento anual isolados por empresa)
