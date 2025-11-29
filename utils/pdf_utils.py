import base64
import mimetypes
import os
from flask import current_app, url_for


def build_pdf_image_src(filename, prefer_data_uri=True):
    """Return a data URI or static URL for an image stored under static/imagens."""
    if not filename:
        return None

    imagem_path = os.path.join(current_app.root_path, 'static', 'imagens', filename)
    mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'

    if prefer_data_uri:
        try:
            with open(imagem_path, 'rb') as image_file:
                encoded = base64.b64encode(image_file.read()).decode('ascii')
            return f"data:{mime_type};base64,{encoded}"
        except OSError as exc:
            current_app.logger.warning('Não foi possível embutir a imagem %s: %s', filename, exc)

    try:
        return url_for('static', filename=f'imagens/{filename}', _external=False)
    except RuntimeError:
        return None
