import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, flash, send_file
from models.database import get_connection
import io
from datetime import datetime
from utils.pdf_utils import build_pdf_image_src

pdf_api_bp = Blueprint('pdf_api', __name__)

PDFSHIFT_API_KEY = 'sk_1f707469f4cb0a5f4a0c6bfcce8aefdce86203f1'  # Chave real do usuário
PDFSHIFT_URL = 'https://api.pdfshift.io/v3/convert/pdf'

@pdf_api_bp.route('/pdf_ordem_api/<int:id>')
def gerar_pdf_api(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id=?', (id,))
    ordem = cursor.fetchone()
    conn.close()

    if not ordem:
        return "Ordem não encontrada.", 404

    foto_nome = build_pdf_image_src(ordem[7] if len(ordem) > 7 else None)

    html = render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now())

    # Permite enviar uma URL como fonte, se passado via query string (?url=...)
    source_url = request.args.get('url')
    if source_url:
        source = source_url
    else:
        source = html

    try:
        response = requests.post(
            PDFSHIFT_URL,
            headers={'X-API-Key': PDFSHIFT_API_KEY},
            json={
                'source': source,
                'landscape': False,
                'use_print': False
            },
            timeout=30
        )
        response.raise_for_status()
        pdf_bytes = response.content
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ordem_{id}.pdf'
        )
    except requests.HTTPError as e:
        flash(f"Erro ao gerar PDF: {response.status_code} - {response.text}", "danger")
        return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), erro_pdf=response.text)
    except Exception as e:
        flash(f"Falha na comunicação com a API PDFShift: {str(e)}", "danger")
        return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), erro_pdf=str(e))
