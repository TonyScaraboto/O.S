import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, flash, current_app, send_file
from models.database import get_db_path
import sqlite3
import io
from datetime import datetime

pdf_api_bp = Blueprint('pdf_api', __name__)

PDFSHIFT_API_KEY = 'SUA_API_KEY_AQUI'  # Troque pela sua chave da PDFShift
PDFSHIFT_URL = 'https://api.pdfshift.io/v3/convert/pdf'

@pdf_api_bp.route('/pdf_ordem_api/<int:id>')
def gerar_pdf_api(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id=?', (id,))
    ordem = cursor.fetchone()
    conn.close()

    if not ordem:
        return "Ordem não encontrada.", 404

    foto_nome = None
    if len(ordem) > 7 and ordem[7]:
        foto_nome = os.path.join(current_app.root_path, 'static', 'imagens', ordem[7])
        foto_nome = 'file:///' + foto_nome.replace('\\', '/').replace(' ', '%20')

    html = render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now())

    # Envia o HTML para a API PDFShift
    response = requests.post(
        PDFSHIFT_URL,
        auth=(PDFSHIFT_API_KEY, ''),
        json={
            'source': html,
            'landscape': False,
            'use_print': True
        }
    )
    if response.status_code == 200:
        pdf_bytes = response.content
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ordem_{id}.pdf'
        )
    else:
        return f"Erro ao gerar PDF: {response.text}", 500
