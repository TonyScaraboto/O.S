import os
import pdfkit


def get_wkhtmltopdf_path():
    # Allow env override (accept both names for convenience)
    for env_var in ('WKHTMLTOPDF_BIN', 'WKHTMLTOPDF_PATH'):
        bin_path = os.environ.get(env_var)
        if bin_path:
            return bin_path
    # Common install paths (Windows/Linux)
    candidates = [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
        "/usr/local/bin/wkhtmltopdf",
        "/usr/bin/wkhtmltopdf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def render_pdf_bytes_from_html(html: str) -> bytes:
    options = {
        'enable-local-file-access': None,
        'encoding': 'UTF-8',
        'quiet': None,
        'print-media-type': None,
    }
    bin_path = get_wkhtmltopdf_path()
    if not bin_path:
        # Let pdfkit try system default; may fail if not installed
        config = None
    else:
        config = pdfkit.configuration(wkhtmltopdf=bin_path)
    return pdfkit.from_string(html, False, options=options, configuration=config)
