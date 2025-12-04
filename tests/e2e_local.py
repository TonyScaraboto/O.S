from datetime import datetime
import bcrypt

from app import app
from models.database import get_connection


def ensure_user(email: str, nome: str, senha: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM usuarios WHERE username=?', (email,))
    c.execute('DELETE FROM clientes WHERE email=?', (email,))
    h = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute(
        'INSERT INTO clientes (nome_assistencia, nome_usuario, email, senha, senha_pura, data_cadastro, trial_ativo, assinatura_ativa) VALUES (?,?,?,?,?,?,1,1)',
        (nome, nome, email, h, senha, datetime.now().strftime('%Y-%m-%d')),
    )
    c.execute('INSERT INTO usuarios (username, password, role) VALUES (?,?,?)', (email, h, 'cliente'))
    conn.commit()
    conn.close()


def main():
    email = 'testmanual@example.com'
    senha = 'Senha12345'
    ensure_user(email, 'Assist Test Manual', senha)

    client = app.test_client()

    r = client.post('/login', data={'username': email, 'password': senha}, follow_redirects=True)
    print('login status', r.status_code)

    r2 = client.post(
        '/nova_ordem',
        data={
            'cliente': 'Cliente X',
            'telefone': '13999999999',
            'aparelho': 'Moto G',
            'defeito': 'Troca bateria',
            'valor': '199.90',
            'status': 'Recebido',
            'fornecedor': 'FornecedorY',
            'custo_peca': '80.50',
        },
        follow_redirects=True,
    )
    print('nova_ordem status', r2.status_code)

    r3 = client.post(
        '/salvar_acessorio',
        data={'nome': 'Capinha', 'quantidade': '3', 'preco': '25,00'},
        follow_redirects=True,
    )
    print('acessorio status', r3.status_code)

    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, cliente, aparelho, status FROM ordens WHERE LOWER(cliente)=? ORDER BY id DESC LIMIT 1', (email,))
    print('ultima_os', c.fetchone())
    c.execute('SELECT id, nome, quantidade, cliente FROM acessorios WHERE LOWER(cliente)=? ORDER BY id DESC LIMIT 1', (email,))
    print('ultimo_acess', c.fetchone())
    conn.close()


if __name__ == '__main__':
    main()
