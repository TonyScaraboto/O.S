

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

        # Exibe instruções de pagamento Pix simples
        pix_chave = 'comicsultimate@gmail.com'
        valor = 45.00
        flash(f'Para ativar seu cadastro, faça um Pix de R$ {valor:.2f} para a chave <b>{pix_chave}</b> e envie o comprovante para comicsultimate@gmail.com.', 'info')
        return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email, senha=senha, pix_chave=pix_chave, valor=valor)
    return render_template('cadastro.html')
