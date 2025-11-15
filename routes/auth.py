
from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Página de perfil do cliente
import os
from flask import current_app
@auth_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    nome_assistencia = session.get('nome_assistencia', "Assistência Técnica Exemplo")
    nome_usuario = session.get('nome_usuario', session.get('user', 'Usuário'))
    data_aquisicao = "2024-01-10"  # Substitua pela data real do cliente
    foto_perfil = None



    # Alterar nome da assistência técnica (modal)
    if request.method == 'POST':
        novo_nome = request.form.get('novo_nome_assistencia', '').strip()
        if novo_nome:
            session['nome_assistencia'] = novo_nome
            nome_assistencia = novo_nome

    # Alterar nome do usuário
    if request.method == 'POST' and request.form.get('acao') == 'alterar_usuario':
        novo_usuario = request.form.get('novo_nome_usuario', '').strip()
        if novo_usuario:
            session['nome_usuario'] = novo_usuario
        nome_usuario = session.get('nome_usuario', nome_usuario)

    # Salvar foto de perfil se enviada
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

    foto_perfil = session.get('foto_perfil')
    return render_template('perfil.html', nome_assistencia=nome_assistencia, nome_usuario=nome_usuario, data_aquisicao=data_aquisicao, foto_perfil=foto_perfil)

# 🔐 Rota de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        conn = sqlite3.connect('ordens.db')
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM usuarios WHERE username=? AND password=?', (user, pwd))
        result = cursor.fetchone()
        conn.close()

        if result:
            session['user'] = user
            session['role'] = result[0]
            return redirect(url_for('ordens.dashboard'))
        else:
            return render_template('login.html', error='Usuário ou senha inválidos', current_year=datetime.now().year)

    return render_template('login.html', current_year=datetime.now().year)

# 🚪 Rota de logout
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))