from flask import Flask, render_template, send_from_directory
from routes.auth import auth_bp
from routes.ordens import ordens_bp
from routes.cadastro import cadastro_bp
from routes.admin import admin_bp
from routes.assinatura import assinatura_bp
from api.pdf_api import pdf_api_bp
from dotenv import load_dotenv
import os

load_dotenv()
os.environ['ORDENS_DB_PATH'] = '/tmp/ordens.db'
from models.database import init_db
import click


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

init_db()


# Registra os blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(ordens_bp)
app.register_blueprint(cadastro_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(assinatura_bp)
app.register_blueprint(pdf_api_bp)


# Rota principal para Vercel
@app.route('/')
def home():
    return render_template('login.html')


@app.route('/favicon.ico')
def favicon():
    static_dir = os.path.join(app.root_path, 'static')
    ico_file = os.path.join(static_dir, 'favicon.ico')
    if os.path.exists(ico_file):
        return send_from_directory(static_dir, 'favicon.ico', mimetype='image/x-icon')
    return send_from_directory(static_dir, 'favicon.svg', mimetype='image/svg+xml')

