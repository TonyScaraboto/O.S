from datetime import datetime
from flask import session, redirect, url_for, flash
from models.database import get_connection
from utils.ordem_utils import normalize_email

def checar_trial_e_pagamento():
    # Admin nunca é bloqueado
    if session.get('role') == 'admin':
        return None
    email = session.get('user')
    if not email:
        return redirect(url_for('auth.login'))
    email_norm = normalize_email(email)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT data_fim_trial, assinatura_ativa FROM clientes WHERE LOWER(email)=?', (email_norm,))
    row = cursor.fetchone()
    if not row:
        # Fallback para cadastros manuais sem domínio
        user_no_domain = (email_norm.split('@')[0]) if email_norm else None
        if user_no_domain:
            cursor.execute('SELECT data_fim_trial, assinatura_ativa FROM clientes WHERE LOWER(email)=?', (user_no_domain,))
            row = cursor.fetchone()
    conn.close()
    if not row:
        flash('Conta não encontrada.','danger')
        return redirect(url_for('auth.login'))
    data_fim_trial, assinatura_ativa = row
    if assinatura_ativa:
        return None
    if data_fim_trial:
        dias_restantes = (datetime.strptime(data_fim_trial, '%Y-%m-%d') - datetime.now()).days
        if dias_restantes < 0:
            flash('Seu período gratuito expirou. Realize o pagamento para continuar usando o sistema.','warning')
            return redirect(url_for('auth.perfil'))
    return None
