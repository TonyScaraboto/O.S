import io
import os
import hashlib
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app, Response, make_response
from models.database import get_connection
from datetime import datetime
from utils.pdf_utils import build_pdf_image_src
from utils.ordem_utils import build_pdf_context
from routes.ordens import _normalize_email, _usuario_pode_ver_ordem

pdf_api_bp = Blueprint('pdf_api', __name__)

PDFSHIFT_URL = os.environ.get('PDFSHIFT_URL', 'https://api.pdfshift.io/v3/convert/pdf')
PDFSHIFT_API_KEY = os.environ.get('PDFSHIFT_API_KEY')


def _get_pdfkit_renderer():
    """Tenta importar pdfkit_utils. Retorna None se não disponível."""
    try:
        from utils.pdfkit_utils import render_pdf_bytes_from_html
        return render_pdf_bytes_from_html
    except ImportError:
        return None


def _salvar_pdf_no_banco(ordem_id: int, pdf_bytes: bytes, nome_arquivo: str):
    """Salva ou atualiza o PDF no banco de dados."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        hash_conteudo = hashlib.sha256(pdf_bytes).hexdigest()
        data_geracao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar se já existe
        cursor.execute('SELECT id FROM pdfs_gerados WHERE ordem_id=?', (ordem_id,))
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute(
                'UPDATE pdfs_gerados SET pdf_data=?, nome_arquivo=?, data_geracao=?, hash_conteudo=? WHERE ordem_id=?',
                (pdf_bytes, nome_arquivo, data_geracao, hash_conteudo, ordem_id)
            )
        else:
            cursor.execute(
                'INSERT INTO pdfs_gerados (ordem_id, pdf_data, nome_arquivo, data_geracao, hash_conteudo) VALUES (?, ?, ?, ?, ?)',
                (ordem_id, pdf_bytes, nome_arquivo, data_geracao, hash_conteudo)
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        current_app.logger.warning('Erro ao salvar PDF no banco: %s', e)
        return False


def _buscar_pdf_do_banco(ordem_id: int):
    """Busca PDF armazenado no banco. Retorna (pdf_bytes, nome_arquivo) ou (None, None)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT pdf_data, nome_arquivo FROM pdfs_gerados WHERE ordem_id=?', (ordem_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return row[0], row[1]
    except Exception as e:
        current_app.logger.warning('Erro ao buscar PDF do banco: %s', e)
    return None, None


def _gerar_pdf_bytes(html: str, engine: str = None):
    """
    Tenta gerar PDF usando diferentes engines.
    Retorna (pdf_bytes, erro) - se erro, pdf_bytes é None.
    """
    # Se engine específico solicitado
    if engine == 'weasy':
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html, base_url=current_app.root_path).write_pdf()
            return pdf_bytes, None
        except Exception as e:
            return None, f'WeasyPrint: {e}'
    
    if engine == 'pdfkit':
        render_fn = _get_pdfkit_renderer()
        if render_fn:
            try:
                pdf_bytes = render_fn(html)
                return pdf_bytes, None
            except Exception as e:
                return None, f'pdfkit: {e}'
        return None, 'pdfkit não disponível'
    
    # Tentar PDFShift API
    api_key = os.environ.get('PDFSHIFT_API_KEY', PDFSHIFT_API_KEY)
    if api_key:
        try:
            payload = {
                'source': html,
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
            return response.content, None
        except requests.HTTPError as e:
            status = getattr(response, 'status_code', 'N/A')
            text = getattr(response, 'text', str(e))
            current_app.logger.error('PDFShift HTTPError %s: %s', status, text[:500])
            # Continuar para fallbacks
        except Exception as e:
            current_app.logger.warning('PDFShift falhou: %s', e)
            # Continuar para fallbacks
    
    # Fallback: tentar WeasyPrint
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html, base_url=current_app.root_path).write_pdf()
        return pdf_bytes, None
    except ImportError:
        pass
    except Exception as e:
        current_app.logger.warning('WeasyPrint fallback falhou: %s', e)
    
    # Fallback: tentar pdfkit
    render_fn = _get_pdfkit_renderer()
    if render_fn:
        try:
            pdf_bytes = render_fn(html)
            return pdf_bytes, None
        except Exception as e:
            current_app.logger.warning('pdfkit fallback falhou: %s', e)
    
    # Nenhum engine disponível
    return None, 'Nenhum gerador de PDF disponível. Configure PDFSHIFT_API_KEY ou instale WeasyPrint/pdfkit.'

@pdf_api_bp.route('/ver_pdf/<int:id>')
def ver_pdf(id):
    """Exibe o PDF armazenado no banco em uma nova aba (inline)."""
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user_email = session.get('user')
    user_email_norm = _normalize_email(user_email)
    is_admin = session.get('role') == 'admin'

    # Verificar permissão
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id=?', (id,))
    ordem = cursor.fetchone()
    conn.close()

    if not ordem or not _usuario_pode_ver_ordem(ordem, user_email_norm, is_admin):
        return "Ordem não encontrada.", 404

    # Buscar PDF do banco
    pdf_bytes, nome_arquivo = _buscar_pdf_do_banco(id)
    
    if not pdf_bytes:
        # PDF não existe, gerar agora
        return redirect(url_for('pdf_api.gerar_pdf_api', id=id, view='1'))

    # Retornar PDF inline (abre no navegador)
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'inline; filename="{nome_arquivo}"',
            'Content-Type': 'application/pdf'
        }
    )


@pdf_api_bp.route('/pdf_ordem_api/<int:id>')
def gerar_pdf_api(id):
    """Gera o PDF, salva no banco e exibe inline ou faz download."""
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

    ordem_id = ordem[0]
    nome_arquivo = f'ordem_{ordem_id}.pdf'
    
    # Verificar se deve apenas visualizar (view=1) ou forçar regeneração (force=1)
    view_mode = request.args.get('view', '0') == '1'
    force_regen = request.args.get('force', '0') == '1'
    
    # Se não forçar regeneração, tentar buscar do banco primeiro
    if not force_regen:
        pdf_bytes_cached, _ = _buscar_pdf_do_banco(ordem_id)
        if pdf_bytes_cached:
            if view_mode:
                return Response(
                    pdf_bytes_cached,
                    mimetype='application/pdf',
                    headers={
                        'Content-Disposition': f'inline; filename="{nome_arquivo}"',
                        'Content-Type': 'application/pdf'
                    }
                )
            else:
                return send_file(
                    io.BytesIO(pdf_bytes_cached),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=nome_arquivo
                )

    foto_nome = build_pdf_image_src(ordem[7] if len(ordem) > 7 else None)
    pdf_context = build_pdf_context(ordem)

    html = render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context)

    # Usar engine específico se solicitado via query string
    engine = request.args.get('engine', '').lower() or None
    
    # Gerar PDF usando a função robusta
    pdf_bytes, erro_pdf = _gerar_pdf_bytes(html, engine=engine)

    # Se houve erro, mostrar página HTML para impressão manual
    if erro_pdf or not pdf_bytes:
        flash(f'Erro ao gerar PDF: {erro_pdf or "PDF vazio"}. Use Ctrl+P para imprimir esta página.', 'warning')
        return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context, erro_pdf=erro_pdf)

    # Salvar PDF no banco
    _salvar_pdf_no_banco(ordem_id, pdf_bytes, nome_arquivo)

    # Retornar PDF
    if view_mode:
        # Exibir inline (nova aba do navegador)
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{nome_arquivo}"',
                'Content-Type': 'application/pdf'
            }
        )
    else:
        # Download
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nome_arquivo
        )


@pdf_api_bp.route('/pdf_html/<int:id>')
def ver_pdf_html(id):
    """Exibe a O.S em formato HTML para impressão (fallback quando PDF não disponível)."""
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    conn = get_connection()
    cursor = conn.cursor()
    user_email = session.get('user')
    user_email_norm = _normalize_email(user_email)
    is_admin = session.get('role') == 'admin'
    cursor.execute('SELECT * FROM ordens WHERE id=?', (id,))
    ordem = cursor.fetchone()
    conn.close()

    if not ordem or not _usuario_pode_ver_ordem(ordem, user_email_norm, is_admin):
        return "Ordem não encontrada.", 404

    foto_nome = build_pdf_image_src(ordem[7] if len(ordem) > 7 else None)
    pdf_context = build_pdf_context(ordem)

    return render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now(), pdf_context=pdf_context)
