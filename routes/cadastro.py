
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
from pagseguro_pix import criar_cobranca_pix, consultar_status_pix

cadastro_bp = Blueprint('cadastro', __name__)

def get_db():
    return sqlite3.connect('ordens.db')


@cadastro_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome_assistencia = request.form['nome_assistencia']
        email = request.form['email']
        senha = request.form['senha']
        # Gera cobrança Pix automática
        try:
            cobranca = criar_cobranca_pix(45.00, nome_assistencia, email)
            txid = cobranca.get('txid')
            location = cobranca.get('loc', {}).get('location')
            qr_code = cobranca.get('pixCopiaECola') or cobranca.get('pixCopiaECola', '')
        except Exception as e:
            flash(f'Erro ao gerar cobrança Pix: {e}', 'danger')
            return render_template('cadastro.html')

        # Exibe QR Code e botão para verificar pagamento
        if request.form.get('verificar_pagamento') == '1' and request.form.get('txid'):
            txid = request.form.get('txid')
            try:
                status = consultar_status_pix(txid)
                if status.get('status') == 'CONCLUIDA':
                    data_cadastro = datetime.now().strftime('%Y-%m-%d')
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO clientes (nome_assistencia, email, senha, data_cadastro, trial_ativo, assinatura_ativa, data_ultimo_pagamento) VALUES (?, ?, ?, ?, 0, 1, ?)''',
                        (nome_assistencia, email, senha, data_cadastro, data_cadastro))
                    conn.commit()
                    conn.close()
                    flash('Cadastro realizado com sucesso! Faça login para acessar o sistema.', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('Pagamento ainda não confirmado. Aguarde alguns instantes e tente novamente.', 'warning')
            except Exception as e:
                flash(f'Erro ao consultar status do pagamento: {e}', 'danger')
        return render_template('cadastro.html', qr_code=qr_code, txid=txid, location=location, nome_assistencia=nome_assistencia, email=email, senha=senha)
    return render_template('cadastro.html')
