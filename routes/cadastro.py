

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from models.database import get_db_path
from datetime import datetime
import bcrypt
import re
from utils.email_utils import enviar_email

cadastro_bp = Blueprint('cadastro', __name__)

def get_db():
    return sqlite3.connect(get_db_path())


@cadastro_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome_assistencia = request.form['nome_assistencia']
        email = request.form['email']
        senha = request.form['senha']

        # Validação de e-mail
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not re.match(email_regex, email):
            flash('E-mail inválido.', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email)

        # Validação de senha forte
        senha_regex = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*()_+\-=]{8,}$'
        if not re.match(senha_regex, senha):
            flash('A senha deve ter pelo menos 8 caracteres, incluindo letras e números.', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email)

        # Criptografa a senha
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        # Salva cadastro como pendente
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (nome_assistencia, email, senha, senha_pura, data_cadastro, trial_ativo, assinatura_ativa, pix_pagamento)
                VALUES (?, ?, ?, ?, ?, 1, 0, ?)
            ''', (
                nome_assistencia,
                email,
                senha_hash.decode('utf-8'),
                senha,
                datetime.now().strftime('%Y-%m-%d'),
                'comicsultimate@gmail.com'
            ))
            cursor.execute('''
                INSERT INTO usuarios (username, password, role)
                VALUES (?, ?, ?)
            ''', (email, senha_hash, 'cliente'))
            conn.commit()
            conn.close()
        except Exception as e:
            flash(f'Erro ao salvar cadastro: {e}', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email)

        # Exibe instruções de pagamento Pix simples
        pix_chave = 'comicsultimate@gmail.com'
        valor = 45.00
        flash(f'Cadastro salvo! Para ativar, faça um Pix de R$ {valor:.2f} para a chave <b>{pix_chave}</b> e envie o comprovante para comicsultimate@gmail.com. Seu acesso será liberado manualmente.', 'info')
        return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email, senha=senha, pix_chave=pix_chave, valor=valor)
    return render_template('cadastro.html')
