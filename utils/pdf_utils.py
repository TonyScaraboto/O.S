import base64
import mimetypes
import os
from flask import current_app, url_for


def _candidate_paths(filename):
    """Generate possible filesystem paths for an image reference."""
    if not filename:
        return []
    root = current_app.root_path
    normalized = filename.replace('\', '/').lstrip('/')
    candidates = []
    if os.path.isabs(filename):
        candidates.append(filename)
    candidates.append(os.path.join(root, normalized))
    search_dirs = [
        os.path.join('static', 'imagens'),
        os.path.join('static', 'fotos_ordens'),
        os.path.join('static', 'ordens'),
        'static',
    ]
    for folder in search_dirs:
        candidates.append(os.path.join(root, folder, normalized))
    return candidates


def _resolve_image_path(filename):
    for path in _candidate_paths(filename):
        if os.path.exists(path):
            return path
    return None


def build_pdf_image_src(filename, prefer_data_uri=True):
    """Return a data URI or static URL for an image stored on disk or embedded."""
    if not filename:
        return None
    if isinstance(filename, str) and filename.startswith('data:'):
        return filename

    imagem_path = _resolve_image_path(filename)
    mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'

    if prefer_data_uri and imagem_path:
        try:
            with open(imagem_path, 'rb') as image_file:
                encoded = base64.b64encode(image_file.read()).decode('ascii')
            return f"data:{mime_type};base64,{encoded}"
        except OSError as exc:
            current_app.logger.warning('Não foi possível embutir a imagem %s: %s', filename, exc)

    try:
        suffix = filename if filename.startswith(('imagens/', 'fotos_ordens/', 'ordens/')) else f'imagens/{filename}'
        return url_for('static', filename=suffix, _external=False)
    except RuntimeError:
        return None
