from flask import Blueprint, render_template, session, redirect, url_for
import sqlite3
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def get_db():
    return sqlite3.connect('ordens.db')

@admin_bp.route('/admin')
def painel_admin():
    # Verifica se o usuário é admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome_assistencia, email, data_cadastro, data_fim_trial, assinatura_ativa FROM clientes')
    clientes = cursor.fetchall()
    conn.close()
    clientes_info = []
    for c in clientes:
        dias_restantes = None
        if c[4]:
            dias_restantes = (datetime.strptime(c[4], '%Y-%m-%d') - datetime.now()).days
        clientes_info.append({
            'id': c[0],
            'nome_assistencia': c[1],
            'email': c[2],
            'data_cadastro': c[3],
            'data_fim_trial': c[4],
            'assinatura_ativa': c[5],
            'dias_restantes': dias_restantes
        })
    return render_template('admin.html', clientes=clientes_info)
