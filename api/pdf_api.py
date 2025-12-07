import io
import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app
from models.database import get_connection
from datetime import datetime
from utils.pdf_utils import build_pdf_image_src
from utils.pdfkit_utils import render_pdf_bytes_from_html
from utils.ordem_utils import build_pdf_context
from routes.ordens import _normalize_email, _usuario_pode_ver_ordem

pdf_api_bp = Blueprint('pdf_api', __name__)

PDFSHIFT_URL = os.environ.get('PDFSHIFT_URL', 'https://api.pdfshift.io/v3/convert/pdf')
PDFSHIFT_API_KEY = os.environ.get('PDFSHIFT_API_KEY')

@pdf_api_bp.route('/pdf_ordem_api/<int:id>')
def gerar_pdf_api(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    conn = get_connection()
    cursor = conn.cursor()
    user_email = session.get('user')
    user_email_norm = _normalize_email(user_email)
    is_admin = session.get('role') == 'admin'
    cursor.execute('SELECT * FROM ordens WHERE id=?', (id,))
    ordem = cursor.fetchone()
    # Fallback: buscar última ordem do usuário se id não encontrado
    if not ordem:
        try:
            if is_admin:
                cursor.execute('SELECT * FROM ordens ORDER BY id DESC LIMIT 1')
            else:
                cursor.execute('SELECT * FROM ordens WHERE LOWER(cliente)=? ORDER BY id DESC LIMIT 1', (user_email_norm,))
            ordem = cursor.fetchone()
        except Exception:
            ordem = None
    conn.close()

    if not ordem or not _usuario_pode_ver_ordem(ordem, user_email_norm, is_admin):
        return "Ordem não encontrada.", 404

    foto_nome = build_pdf_image_src(ordem[7] if len(ordem) > 7 else None)
    pdf_context = build_pdf_context(ordem)

    html = render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context)

    # Permite enviar uma URL como fonte, se passado via query string (?url=...)
    source_url = request.args.get('url')
    if source_url:
        source = source_url
    else:
        source = html

    # Fallback local com WeasyPrint quando sem chave ou forçado via query (?engine=weasy)
    engine = request.args.get('engine', '').lower()
    use_weasy = engine == 'weasy' or (not os.environ.get('PDFSHIFT_API_KEY', PDFSHIFT_API_KEY) and current_app.debug)
    use_pdfkit = engine == 'pdfkit'
    if use_weasy:
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html, base_url=current_app.root_path).write_pdf()
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'ordem_{id}.pdf'
            )
        except Exception as e:
            current_app.logger.exception('Falha na geração local com WeasyPrint: %s', e)
            flash(f'Falha na geração local de PDF: {e}', 'danger')
            return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context, erro_pdf=str(e))

    if use_pdfkit:
        try:
            pdf_bytes = render_pdf_bytes_from_html(html)
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'ordem_{id}.pdf'
            )
        except Exception as e:
            current_app.logger.exception('Falha na geração com pdfkit/wkhtmltopdf: %s', e)
            flash(f'Falha com pdfkit: {e}', 'danger')
            return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context, erro_pdf=str(e))

    api_key = os.environ.get('PDFSHIFT_API_KEY', PDFSHIFT_API_KEY)
    if not api_key:
        flash('API PDFShift não configurada.', 'danger')
        return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context, erro_pdf='Configuração ausente')

    try:
        payload = {
            'source': source,
            'landscape': False,
            'use_print': True,
        }
        response = requests.post(
            PDFSHIFT_URL,
            headers={'X-API-Key': api_key},
            json=payload,
            timeout=60
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
        status = getattr(response, 'status_code', 'N/A')
        text = getattr(response, 'text', str(e))
        current_app.logger.error('PDFShift HTTPError %s: %s', status, text[:500])
        flash(f"Erro ao gerar PDF: {status} - {text[:500]}", "danger")
        return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context, erro_pdf=text)
    except Exception as e:
        current_app.logger.exception('Falha na comunicação com a API PDFShift: %s', e)
        flash(f"Falha na comunicação com a API PDFShift: {str(e)}", "danger")
        return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context, erro_pdf=str(e))
