from flask import Blueprint, jsonify
import os
import requests

from models.database import (
    get_connection,
    get_db_path,
    DATABASE_URL,
    BASE_SCHEME,
    IS_POSTGRES,
    IS_MYSQL,
    IS_SQLITE_URL,
    DB_CONFIG,
)


status_bp = Blueprint('status', __name__)


def _sqlite_file_path(conn):
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA database_list")
        rows = cur.fetchall() or []
        # row format: (seq, name, file)
        for r in rows:
            if len(r) >= 3 and (r[1] == 'main' or r[0] == 0):
                return r[2]
    except Exception:
        pass
    return get_db_path()


@status_bp.route('/__status/db')
def db_status():
    # This route is intended for development diagnostics only. Avoid secrets.
    serverless_env = {
        'VERCEL_ENV': os.environ.get('VERCEL_ENV'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
    }
    info = {
        'serverless_env': serverless_env,
        'database_url_scheme': BASE_SCHEME or None,
        'using_sqlite_url': bool(IS_SQLITE_URL),
        'is_postgres': bool(IS_POSTGRES),
        'is_mysql': bool(IS_MYSQL),
    }
    try:
        conn = get_connection()
        try:
            if IS_POSTGRES:
                engine = 'postgres'
                safe_target = {
                    'host': DB_CONFIG.get('host'),
                    'port': DB_CONFIG.get('port'),
                    'database': DB_CONFIG.get('database'),
                    'username_present': bool(DB_CONFIG.get('username')),
                }
                info.update({'engine': engine, 'target': safe_target})
            elif IS_MYSQL:
                engine = 'mysql'
                safe_target = {
                    'host': DB_CONFIG.get('host'),
                    'port': DB_CONFIG.get('port'),
                    'database': DB_CONFIG.get('database'),
                    'username_present': bool(DB_CONFIG.get('username')),
                }
                info.update({'engine': engine, 'target': safe_target})
            else:
                engine = 'sqlite'
                sqlite_file = _sqlite_file_path(conn)
                info.update({'engine': engine, 'sqlite_file': sqlite_file})
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        info.update({'engine': 'unknown', 'error': str(e)})

    # Never return the full DATABASE_URL to avoid leaking credentials
    return jsonify(info), 200


@status_bp.route('/__status/pdf')
def pdf_status():
    # Minimal diagnostics for PDF generation configuration
    pdfshift_url = os.environ.get('PDFSHIFT_URL', 'https://api.pdfshift.io/v3/convert/pdf')
    pdfshift_key_present = bool(os.environ.get('PDFSHIFT_API_KEY'))
    info = {
        'pdfshift_url': pdfshift_url,
        'pdfshift_key_present': pdfshift_key_present,
    }
    return jsonify(info), 200


@status_bp.route('/__status/pdf_test')
def pdf_status_test():
    url = os.environ.get('PDFSHIFT_URL', 'https://api.pdfshift.io/v3/convert/pdf')
    api_key = os.environ.get('PDFSHIFT_API_KEY')
    if not api_key:
        return jsonify({'ok': False, 'error': 'PDFSHIFT_API_KEY ausente'}), 400
    sample_html = '<html><head><title>Teste</title></head><body><h1>PDF OK</h1><p>Teste de conexão.</p></body></html>'
    try:
        resp = requests.post(
            url,
            headers={'X-API-Key': api_key},
            json={'source': sample_html, 'use_print': True},
            timeout=30,
        )
        ok = resp.status_code == 200 and resp.content and len(resp.content) > 500
        return jsonify({'ok': ok, 'status_code': resp.status_code, 'size': len(resp.content or b'')}), (200 if ok else 502)
    except requests.RequestException as e:
        return jsonify({'ok': False, 'error': str(e)}), 502
