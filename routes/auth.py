

from flask import Blueprint, render_template, request, redirect, url_for, session, make_response
import sqlite3
from models.database import get_db_path
from datetime import datetime
import bcrypt

auth_bp = Blueprint('auth', __name__)

 
import os
from flask import current_app
@auth_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    nome_assistencia = session.get('nome_assistencia', "Assistência Técnica Exemplo")
    nome_usuario = session.get('nome_usuario', session.get('user', 'Usuário'))
    foto_perfil = None
    dias_trial_restantes = None
    data_aquisicao = None
    data_fim_trial = None
    # Buscar data de aquisição e fim do trial do banco
    user_email = session.get('user')
    if user_email:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('SELECT data_cadastro, data_fim_trial FROM clientes WHERE email=?', (user_email,))
        row = cursor.fetchone()
        if row:
            data_aquisicao = row[0]
            data_fim_trial = row[1]
            if data_fim_trial:
                from datetime import datetime
                dias_trial_restantes = (datetime.strptime(data_fim_trial, '%Y-%m-%d') - datetime.now()).days
        conn.close()




    
    if request.method == 'POST':
        novo_nome = request.form.get('novo_nome_assistencia', '').strip()
        if novo_nome:
            session['nome_assistencia'] = novo_nome
            nome_assistencia = novo_nome
            # Persistir no banco
            user_email = session.get('user')
            if user_email:
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                cursor.execute('UPDATE clientes SET nome_assistencia=? WHERE email=?', (novo_nome, user_email))
                conn.commit()
                conn.close()


    # Alterar nome do usuário
    if request.method == 'POST' and request.form.get('acao') == 'alterar_usuario':
        novo_usuario = request.form.get('novo_nome_usuario', '').strip()
        if novo_usuario:
            session['nome_usuario'] = novo_usuario
            nome_usuario = novo_usuario
            # Persistir no banco
            user_email = session.get('user')
            if user_email:
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                cursor.execute('UPDATE clientes SET nome_assistencia=? WHERE email=?', (novo_usuario, user_email))
                conn.commit()
                conn.close()
        nome_usuario = session.get('nome_usuario', nome_usuario)

    
    if request.method == 'POST' and 'foto_perfil' in request.files:
        foto = request.files['foto_perfil']
        if foto and foto.filename:
            ext = os.path.splitext(foto.filename)[1]
            nome_arquivo = f"{nome_usuario}_perfil{ext}"
            pasta_fotos = os.path.join(current_app.root_path, 'static', 'fotos_perfil')
            if not os.path.exists(pasta_fotos):
                os.makedirs(pasta_fotos)
            caminho = os.path.join(pasta_fotos, nome_arquivo)
            foto.save(caminho)
            session['foto_perfil'] = nome_arquivo
            # Persistir no banco
            user_email = session.get('user')
            if user_email:
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                cursor.execute('UPDATE clientes SET foto_perfil=? WHERE email=?', (nome_arquivo, user_email))
                conn.commit()
                conn.close()

    foto_perfil = session.get('foto_perfil')
    return render_template('perfil.html', nome_assistencia=nome_assistencia, nome_usuario=nome_usuario, data_aquisicao=data_aquisicao, foto_perfil=foto_perfil, dias_trial_restantes=dias_trial_restantes, data_fim_trial=data_fim_trial)

# 🔐 Rota de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    last_user = request.cookies.get('last_user', '')

    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']


        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Busca o hash da senha do usuário
        cursor.execute('SELECT password, role FROM usuarios WHERE username=?', (user,))
        row = cursor.fetchone()

        if row:
            senha_hash = row[0]
            role = row[1]
            # Permite login do admin com senha em texto puro
            if user == 'admin' and pwd == 'admin123':
                session['user'] = user
                session['role'] = role
                cursor.execute('SELECT nome_assistencia, foto_perfil FROM clientes WHERE email=?', (user + '@saas.com',))
                cliente = cursor.fetchone()
                if cliente:
                    session['nome_assistencia'] = cliente[0]
                    session['foto_perfil'] = cliente[1] if cliente[1] else None
                conn.close()
                resp = make_response(redirect(url_for('ordens.dashboard')))
                resp.set_cookie('last_user', user, max_age=60*60*24*30)
                return resp
            # Garante que senha_hash está em bytes
            if isinstance(senha_hash, str):
                senha_hash_bytes = senha_hash.encode('utf-8')
            else:
                senha_hash_bytes = senha_hash
            if senha_hash and bcrypt.checkpw(pwd.encode('utf-8'), senha_hash_bytes):
                # Verifica se assinatura está ativa (liberada)
                cursor.execute('SELECT assinatura_ativa, nome_assistencia, foto_perfil FROM clientes WHERE email=?', (user,))
                cliente = cursor.fetchone()
                if cliente:
                    assinatura_ativa = cliente[0]
                    if not assinatura_ativa:
                        conn.close()
                        return render_template('login.html', error='Acesso ainda não liberado pelo administrador.', current_year=datetime.now().year, last_user=user)
                    session['nome_assistencia'] = cliente[1]
                    session['foto_perfil'] = cliente[2] if cliente[2] else None
                session['user'] = user
                session['role'] = role
                conn.close()
                resp = make_response(redirect(url_for('ordens.dashboard')))
                resp.set_cookie('last_user', user, max_age=60*60*24*30)
                return resp
        conn.close()
        return render_template('login.html', error='Usuário ou senha inválidos', current_year=datetime.now().year, last_user=user)

    return render_template('login.html', current_year=datetime.now().year, last_user=last_user)

# 🚪 Rota de logout
@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    last_user = session.get('user')
    session.clear()
    resp = make_response(redirect(url_for('auth.login')))
    if last_user:
        resp.set_cookie('last_user', last_user, max_age=60*60*24*30)
    return resp