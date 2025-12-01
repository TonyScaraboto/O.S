from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, flash
from models.database import get_connection
from datetime import datetime
import bcrypt
import tempfile
import traceback
import os
from utils.image_storage import store_image

MAX_FOTO_BYTES = 2 * 1024 * 1024  # 2 MB
EXTENSOES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'webp'}

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    user_email = session.get('user')
    nome_assistencia = session.get('nome_assistencia', 'Assistência Técnica Exemplo')
    nome_usuario = session.get('nome_usuario', user_email or 'Usuário')
    foto_perfil = session.get('foto_perfil')
    dias_trial_restantes = None
    data_aquisicao = None
    data_fim_trial = None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nome_assistencia, foto_perfil, nome_usuario, data_cadastro, data_fim_trial FROM clientes WHERE email=?', (user_email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        nome_assistencia = row[0] or nome_assistencia
        foto_perfil = row[1] or foto_perfil
        nome_usuario = row[2] or nome_usuario
        data_aquisicao = row[3]
        data_fim_trial = row[4]
        session['nome_assistencia'] = nome_assistencia
        session['nome_usuario'] = nome_usuario
        session['foto_perfil'] = foto_perfil
        if data_fim_trial:
            dias_trial_restantes = (datetime.strptime(data_fim_trial, '%Y-%m-%d') - datetime.now()).days

    def _validar_imagem(foto_storage):
        nome_arquivo = (foto_storage.filename or '').lower()
        if '.' not in nome_arquivo or nome_arquivo.rsplit('.', 1)[-1] not in EXTENSOES_PERMITIDAS:
            return False, 'Apenas imagens PNG, JPG ou WEBP são aceitas.'
        foto_storage.stream.seek(0, os.SEEK_END)
        tamanho = foto_storage.stream.tell()
        foto_storage.stream.seek(0)
        if tamanho > MAX_FOTO_BYTES:
            return False, 'A foto precisa ter no máximo 2MB.'
        return True, None

    if request.method == 'POST':
        novo_nome_assistencia = request.form.get('novo_nome_assistencia', '').strip()
        novo_nome_usuario = request.form.get('novo_nome_usuario', '').strip()
        foto = request.files.get('foto_perfil')
        conn = get_connection()
        cursor = conn.cursor()
        updated = False
        if novo_nome_assistencia and novo_nome_assistencia != nome_assistencia:
            cursor.execute('UPDATE clientes SET nome_assistencia=? WHERE email=?', (novo_nome_assistencia, user_email))
            nome_assistencia = novo_nome_assistencia
            session['nome_assistencia'] = nome_assistencia
            updated = True
        if novo_nome_usuario and novo_nome_usuario != nome_usuario:
            cursor.execute('UPDATE clientes SET nome_usuario=? WHERE email=?', (novo_nome_usuario, user_email))
            nome_usuario = novo_nome_usuario
            session['nome_usuario'] = nome_usuario
            updated = True
        if foto and foto.filename:
            valida, erro_validacao = _validar_imagem(foto)
            if not valida:
                flash(erro_validacao, 'warning')
            else:
                prefixo = f"{(novo_nome_usuario or nome_usuario or 'usuario')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                nome_arquivo, erro_upload = store_image(foto, 'fotos_perfil', prefixo)
                if erro_upload:
                    flash(erro_upload, 'warning')
                elif nome_arquivo:
                    cursor.execute('UPDATE clientes SET foto_perfil=? WHERE email=?', (nome_arquivo, user_email))
                    session['foto_perfil'] = nome_arquivo
                    foto_perfil = nome_arquivo
                    updated = True
        if updated:
            conn.commit()
            flash('Perfil atualizado com sucesso!', 'success')
        else:
            flash('Nenhuma alteração detectada para salvar.', 'info')
        conn.close()
        return redirect(url_for('auth.perfil'))

    return render_template(
        'perfil.html',
        nome_assistencia=nome_assistencia,
        nome_usuario=nome_usuario,
        data_aquisicao=data_aquisicao,
        foto_perfil=foto_perfil,
        dias_trial_restantes=dias_trial_restantes,
        data_fim_trial=data_fim_trial
    )

# 🔐 Rota de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    last_user = request.cookies.get('last_user', '')

    if request.method == 'POST':
        try:
            user = request.form['username']
            user_email = user if '@' in user else f"{user}@saas.com"
            pwd = request.form['password']
            print(f"Tentando login para usuário: {user}")

            conn = get_connection()
            cursor = conn.cursor()

            # Tenta login por username
            cursor.execute('SELECT password, role FROM usuarios WHERE username=?', (user,))
            row = cursor.fetchone()
            print(f"Resultado busca por username: {row}")
            # Se não encontrar, tenta por email
            if not row:
                cursor.execute('SELECT password, role FROM usuarios WHERE username=?', (user.replace('@saas.com',''),))
                row = cursor.fetchone()
                print(f"Resultado busca por email: {row}")

            if row:
                senha_hash = row[0]
                role = row[1]
                print(f"Senha hash: {senha_hash}, Role: {role}")
                # Permite login do admin e tecnico com senha em texto puro
                if (user == 'admin' and pwd == 'admin123') or (user == 'tecnico' and pwd == 'tecnico123') or (user == 'admin@saas.com' and pwd == 'admin123'):
                    print("Login texto puro permitido")
                    session['user'] = user_email
                    session['role'] = role
                    cursor.execute('SELECT nome_assistencia, foto_perfil, nome_usuario FROM clientes WHERE email=?', (user_email,))
                    cliente = cursor.fetchone()
                    print(f"Cliente encontrado: {cliente}")
                    if cliente:
                        session['nome_assistencia'] = cliente[0]
                        session['foto_perfil'] = cliente[1] if cliente[1] else None
                        session['nome_usuario'] = cliente[2] or user_email
                    else:
                        session['nome_assistencia'] = 'Admin'
                        session['nome_usuario'] = user_email
                        session['foto_perfil'] = None
                    conn.close()
                    resp = make_response(redirect(url_for('ordens.dashboard')))
                    resp.set_cookie('last_user', user, max_age=60*60*24*30)
                    return resp
                # Garante que senha_hash está em bytes
                if isinstance(senha_hash, str):
                    senha_hash_bytes = senha_hash.encode('utf-8')
                else:
                    senha_hash_bytes = senha_hash
                print(f"Senha hash bytes: {senha_hash_bytes}")
                if senha_hash and bcrypt.checkpw(pwd.encode('utf-8'), senha_hash_bytes):
                    print("Senha hash válida")
                    # Verifica se assinatura está ativa (liberada)
                    cursor.execute('SELECT assinatura_ativa, nome_assistencia, foto_perfil, nome_usuario FROM clientes WHERE email=?', (user_email,))
                    cliente = cursor.fetchone()
                    print(f"Cliente encontrado: {cliente}")
                    if cliente:
                        assinatura_ativa = cliente[0]
                        if not assinatura_ativa and role != 'admin':
                            print("Assinatura não ativa e não é admin")
                            conn.close()
                            return render_template('login.html', error='Acesso ainda não liberado pelo administrador.', current_year=datetime.now().year, last_user=user)
                        session['nome_assistencia'] = cliente[1]
                        session['foto_perfil'] = cliente[2] if cliente[2] else None
                        session['nome_usuario'] = cliente[3] or user_email
                    else:
                        session['nome_assistencia'] = user_email
                        session['nome_usuario'] = user_email
                        session['foto_perfil'] = None
                    session['user'] = user_email
                    session['role'] = role
                    conn.close()
                    resp = make_response(redirect(url_for('ordens.dashboard')))
                    resp.set_cookie('last_user', user, max_age=60*60*24*30)
                    return resp
            conn.close()
            print("Login falhou: Usuário ou senha inválidos")
            return render_template('login.html', error='Usuário ou senha inválidos', current_year=datetime.now().year, last_user=user)
        except Exception as e:
            log_path = os.path.join(tempfile.gettempdir(), 'error.log')
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n--- Erro login ---\n{traceback.format_exc()}\n")
            except Exception as log_err:
                print(f"Falha ao gravar log em {log_path}: {log_err}")
            print(f"Erro inesperado no login: {e}")
            return render_template('login.html', error='Erro interno no login. Consulte o administrador.', current_year=datetime.now().year)

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