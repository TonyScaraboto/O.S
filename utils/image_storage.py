import base64
import mimetypes
import os
from flask import current_app


def _sanitize_prefix(value, fallback='imagem'):
    cleaned = ''.join(ch if ch.isalnum() else '_' for ch in (value or '').lower()).strip('_')
    return cleaned or fallback


def _default_extension(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext if ext else '.jpg'


def _data_uri(file_storage, mime_type):
    file_storage.stream.seek(0)
    encoded = base64.b64encode(file_storage.read()).decode('ascii')
    return f"data:{mime_type};base64,{encoded}"


def store_image(file_storage, subdir, prefix):
    """Store image either as data URI (Vercel) or static file. Returns (reference, error)."""
    if not file_storage or not file_storage.filename:
        return None, None

    mime_type = file_storage.mimetype or mimetypes.guess_type(file_storage.filename)[0] or 'image/jpeg'
    filename = f"{_sanitize_prefix(prefix)}{_default_extension(file_storage.filename)}"

    if os.environ.get('VERCEL_ENV'):
        try:
            return _data_uri(file_storage, mime_type), None
        except Exception as exc:
            current_app.logger.warning('Falha ao embutir imagem %s: %s', file_storage.filename, exc)
            return None, 'Não foi possível processar a imagem no ambiente atual.'

    pasta_destino = os.path.join(current_app.root_path, 'static', subdir)
    try:
        os.makedirs(pasta_destino, exist_ok=True)
        caminho = os.path.join(pasta_destino, filename)
        file_storage.save(caminho)
        return filename, None
    except OSError as exc:
        current_app.logger.warning('Falha ao salvar imagem %s: %s', filename, exc)
        return None, 'Não foi possível salvar a imagem no ambiente atual.'
```}