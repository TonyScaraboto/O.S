import sqlite3
from datetime import datetime
from flask import session, redirect, url_for, flash

def checar_trial_e_pagamento():
    # Admin nunca é bloqueado
    if session.get('role') == 'admin':
        return None
    email = session.get('user')
    if not email:
        return redirect(url_for('auth.login'))
    conn = sqlite3.connect('ordens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data_fim_trial, assinatura_ativa FROM clientes WHERE email=?', (email,))
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
