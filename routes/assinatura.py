from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.database import get_connection
from datetime import datetime

assinatura_bp = Blueprint('assinatura', __name__)

def get_db():
    return get_connection()

@assinatura_bp.route('/assinatura')
def status_assinatura():
    email = session.get('user')
    if not email:
        return redirect(url_for('auth.login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nome_assistencia, data_fim_trial, assinatura_ativa, pix_pagamento FROM clientes WHERE email=?', (email,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        flash('Conta não encontrada.','danger')
        return redirect(url_for('auth.login'))
    nome_assistencia, data_fim_trial, assinatura_ativa, pix_pagamento = row
    dias_restantes = None
    if data_fim_trial:
        dias_restantes = (datetime.strptime(data_fim_trial, '%Y-%m-%d') - datetime.now()).days
    return render_template('assinatura.html', nome_assistencia=nome_assistencia, assinatura_ativa=assinatura_ativa, dias_restantes=dias_restantes, pix_pagamento=pix_pagamento)
   