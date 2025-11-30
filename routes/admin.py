
from flask import Blueprint, render_template, session, redirect, url_for, request
from models.database import get_connection
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/remover/<int:cliente_id>', methods=['POST'])
def remover_cliente(cliente_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    conn = get_db()
    cursor = conn.cursor()
    # Buscar o email do cliente para remover também da tabela usuarios
    cursor.execute('SELECT email FROM clientes WHERE id=?', (cliente_id,))
    row = cursor.fetchone()
    email = row[0] if row else None
    # Remover da tabela clientes
    cursor.execute('DELETE FROM clientes WHERE id=?', (cliente_id,))
    # Remover da tabela usuarios se existir
    if email:
        cursor.execute('DELETE FROM usuarios WHERE username=?', (email,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.painel_admin'))

def get_db():
    return get_connection()

import bcrypt

@admin_bp.route('/admin', methods=['GET', 'POST'])
def painel_admin():
    # Verifica se o usuário é admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    conn = get_db()
    cursor = conn.cursor()

    # Cadastro de novo usuário
    if request.method == 'POST' and request.form.get('criar_usuario') == '1':
        nome_assistencia = request.form.get('novo_nome_assistencia', '').strip()
        email = request.form.get('novo_email', '').strip()
        senha = request.form.get('nova_senha', '').strip()
        if nome_assistencia and email and senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
            data_cadastro = datetime.now().strftime('%Y-%m-%d')
            try:
                cursor.execute('''INSERT INTO clientes (nome_assistencia, email, senha, senha_pura, data_cadastro, trial_ativo, assinatura_ativa) VALUES (?, ?, ?, ?, ?, 1, 0)''',
                    (nome_assistencia, email, senha_hash, senha, data_cadastro))
                cursor.execute('''INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)''',
                    (email, senha_hash, 'cliente'))
                conn.commit()
            except Exception as e:
                conn.rollback()
                # Opcional: adicionar flash para erro

    # Liberação manual de acesso
    if request.method == 'POST' and request.form.get('liberar_id'):
        liberar_id = request.form.get('liberar_id')
        cursor.execute('UPDATE clientes SET assinatura_ativa=1 WHERE id=?', (liberar_id,))
        conn.commit()

    cursor.execute('SELECT id, nome_assistencia, email, senha_pura, data_cadastro, data_fim_trial, assinatura_ativa FROM clientes')
    clientes = cursor.fetchall()
    conn.close()
    clientes_info = []
    for c in clientes:
        dias_restantes = None
        if c[5]:
            dias_restantes = (datetime.strptime(c[5], '%Y-%m-%d') - datetime.now()).days
        clientes_info.append({
            'id': c[0],
            'nome_assistencia': c[1],
            'email': c[2],
            'senha_pura': c[3],
            'data_cadastro': c[4],
            'data_fim_trial': c[5],
            'assinatura_ativa': c[6],
            'dias_restantes': dias_restantes
        })
    return render_template('admin.html', clientes=clientes_info)
