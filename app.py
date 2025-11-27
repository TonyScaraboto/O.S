from flask import Flask, render_template
from routes.auth import auth_bp
from routes.ordens import ordens_bp
from routes.cadastro import cadastro_bp
from routes.admin import admin_bp
from routes.assinatura import assinatura_bp
from api.pdf_api import pdf_api_bp
import os
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
import os
from flask import Flask, render_template
from routes.auth import auth_bp
from routes.ordens import ordens_bp
from routes.cadastro import cadastro_bp
from routes.admin import admin_bp
from routes.assinatura import assinatura_bp
from api.pdf_api import pdf_api_bp
import click

os.environ['ORDENS_DB_PATH'] = '/tmp/ordens.db'
from models.database import get_db_path, init_db

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
    # Inicializa o banco de dados e garante registros padrão
init_db()

