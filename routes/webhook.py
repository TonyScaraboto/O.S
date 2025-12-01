from flask import Blueprint, request, jsonify, current_app
from models.database import get_connection
import hmac
import hashlib
import os

webhook_bp = Blueprint('webhook', __name__)

def get_db():
    return get_connection()

@webhook_bp.route('/api/webhook/wooxy', methods=['POST'])
def wooxy_webhook():
    """Webhook para confirmação de pagamentos via Wooxy."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    # Verificar assinatura se Wooxy enviar
    # Assumindo que Wooxy envia um header com assinatura
    signature = request.headers.get('X-Wooxy-Signature')
    if signature:
        secret = os.environ.get('WOOXY_WEBHOOK_SECRET')
        if secret:
            payload = request.get_data()
            expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                current_app.logger.warning('Assinatura inválida no webhook Wooxy')
                return jsonify({'error': 'Invalid signature'}), 403

    # Processar o evento
    event_type = data.get('event_type') or data.get('type')
    if event_type in ('payment.succeeded', 'charge.succeeded', 'pix.paid'):
        charge_id = data.get('charge_id') or data.get('id') or data.get('data', {}).get('charge_id')
        if charge_id:
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE clientes
                    SET assinatura_ativa = 1, data_ultimo_pagamento = datetime('now')
                    WHERE wooxy_charge_id = ?
                ''', (charge_id,))
                if cursor.rowcount > 0:
                    conn.commit()
                    current_app.logger.info('Assinatura ativada para charge_id: %s', charge_id)
                    # Opcional: enviar email de confirmação
                else:
                    current_app.logger.warning('Charge ID não encontrado: %s', charge_id)
            except Exception as e:
                current_app.logger.exception('Erro ao processar webhook Wooxy', exc_info=e)
                if conn:
                    conn.rollback()
                return jsonify({'error': 'Internal error'}), 500
            finally:
                if conn:
                    conn.close()

    return jsonify({'status': 'ok'}), 200