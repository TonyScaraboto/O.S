

from flask import Blueprint, render_template, request, flash, url_for, current_app
from models.database import get_connection
from datetime import datetime
import bcrypt
import re

from utils import wooxy_api
from utils.pix_utils import criar_cobranca_pix_local
from utils.wooxy_api import WooxyAPIError
import os


PLANOS_WOOXY = {
    'mensal': {
        'titulo': 'Plano Mensal',
        'descricao': 'Perfeito para quem está começando',
        'valor': 45.00,
        'badge': 'Popular'
    },
    'trimestral': {
        'titulo': 'Plano Trimestral',
        'descricao': 'Economia extra por 90 dias',
        'valor': 90.00,
        'badge': 'Mais vendido'
    },
    'anual': {
        'titulo': 'Plano Anual',
        'descricao': 'Melhor custo-benefício por 12 meses',
        'valor': 250.00,
        'badge': 'Maior desconto'
    }
}

cadastro_bp = Blueprint('cadastro', __name__)

def get_db():
    return get_connection()


@cadastro_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    planos = [{**data, 'id': slug} for slug, data in PLANOS_WOOXY.items()]
    plano_escolhido = request.form.get('plano')
    if request.method == 'POST':
        if not plano_escolhido:
            plano_escolhido = 'mensal'
        nome_assistencia = request.form['nome_assistencia']
        email = request.form['email']
        senha = request.form['senha']
        plano_detalhes = PLANOS_WOOXY.get(plano_escolhido)
        if not plano_detalhes:
            flash('Selecione um plano válido.', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email,
                                   planos=planos, plano_escolhido='mensal')

        # Validação de e-mail
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not re.match(email_regex, email):
            flash('E-mail inválido.', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email,
                                   planos=planos, plano_escolhido=plano_escolhido)

        # Validação de senha forte
        senha_regex = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*()_+\-=]{8,}$'
        if not re.match(senha_regex, senha):
            flash('A senha deve ter pelo menos 8 caracteres, incluindo letras e números.', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email,
                                   planos=planos, plano_escolhido=plano_escolhido)

        # Criptografa a senha
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (
                    nome_assistencia,
                    nome_usuario,
                    email,
                    senha,
                    senha_pura,
                    data_cadastro,
                    trial_ativo,
                    assinatura_ativa,
                    pix_pagamento,
                    plano_nome,
                    plano_valor,
                    wooxy_charge_id,
                    wooxy_qr_code,
                    wooxy_copia_cola
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?, ?, ?)
            ''', (
                nome_assistencia,
                nome_assistencia,
                email,
                senha_hash.decode('utf-8'),
                senha,
                datetime.now().strftime('%Y-%m-%d'),
                'comicsultimate@gmail.com',
                plano_detalhes['titulo'],
                plano_detalhes['valor'],
                None,
                None,
                None
            ))
            cursor.execute('''
                INSERT INTO usuarios (username, password, role)
                VALUES (?, ?, ?)
            ''', (email, senha_hash, 'cliente'))
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Erro ao salvar cadastro: {e}', 'danger')
            return render_template('cadastro.html', nome_assistencia=nome_assistencia, email=email,
                                   planos=planos, plano_escolhido=plano_escolhido)
        finally:
            if conn:
                conn.close()

        qr_image = url_for('static', filename='imagens/qr_placeholder.svg')
        qr_payload = f"PLANO:{plano_detalhes['titulo']} | VALOR:R$ {plano_detalhes['valor']:.2f}"

        # Usar QR PIX local com chave real
        pix_chave_real = os.environ.get('PIX_CHAVE_REAL', 'comicsultimate@gmail.com')
        wooxy_details = criar_cobranca_pix_local(
            chave_pix=pix_chave_real,
            valor=plano_detalhes['valor'],
            nome_cliente=nome_assistencia,
            plano=plano_escolhido
        )

        # Para plano mensal de R$ 45,00, usar QR fixo fornecido
        if plano_detalhes['valor'] == 45.00:
            qr_fixo = '00020126750014br.gov.bcb.pix013680c46d80-056f-4d0d-8382-08282a0e3d9a0213sitema_de_O.S520400005303986540545.005802BR592340704840_ANTONY_ITALLO_6009Sao_Paulo6229052579ad0fa03a1942468822b1bb2630494E1'
            wooxy_details['qr_payload'] = qr_fixo
            wooxy_details['qr_copia_cola'] = qr_fixo
            # Regenerar QR image com payload fixo
            from utils.pix_utils import gerar_qr_pix_base64
            wooxy_details['qr_image'] = gerar_qr_pix_base64(qr_fixo)

        # Opcional: tentar Wooxy como backup se configurado
        if not wooxy_details and os.environ.get('WOOXY_BASIC_TOKEN'):
            try:
                wooxy_details = wooxy_api.create_charge(
                    valor=plano_detalhes['valor'],
                    plano=plano_escolhido,
                    nome_cliente=nome_assistencia,
                    email_cliente=email
                )
            except (WooxyAPIError, Exception) as exc:
                current_app.logger.warning('Wooxy falhou, usando local: %s', exc)
                wooxy_details = criar_cobranca_pix_local(
                    chave_pix=pix_chave_real,
                    valor=plano_detalhes['valor'],
                    nome_cliente=nome_assistencia,
                    plano=plano_escolhido
                )

        if wooxy_details:
            qr_image = wooxy_details.get('qr_image') or qr_image
            qr_payload = wooxy_details.get('qr_payload') or qr_payload
            copia_cola = wooxy_details.get('qr_copia_cola') or qr_payload
            update_conn = None
            try:
                update_conn = get_connection()
                cursor = update_conn.cursor()
                cursor.execute('''
                    UPDATE clientes
                    SET wooxy_charge_id=?, wooxy_qr_code=?, wooxy_copia_cola=?
                    WHERE email=?
                ''', (
                    wooxy_details.get('charge_id'),
                    qr_image,
                    copia_cola,
                    email
                ))
                update_conn.commit()
            except Exception as exc:
                current_app.logger.exception('Não foi possível salvar dados da cobrança', exc_info=exc)
            finally:
                if update_conn:
                    update_conn.close()

        flash('Cadastro salvo! Assim que o pagamento for confirmado, seu acesso será liberado automaticamente.', 'info')
        return render_template(
            'cadastro.html',
            nome_assistencia=nome_assistencia,
            email=email,
            senha=senha,
            planos=planos,
            plano_escolhido=plano_escolhido,
            mostrar_qr=True,
            qr_image=qr_image,
            qr_payload=qr_payload,
            plano_atual=plano_detalhes
        )
    nome_inicial = request.form.get('nome_assistencia', '')
    return render_template('cadastro.html', planos=planos, plano_escolhido=plano_escolhido,
                           nome_assistencia=nome_inicial)
