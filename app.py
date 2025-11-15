<<<<<<< HEAD
from flask import Flask
from routes.auth import auth_bp
from routes.ordens import ordens_bp
from routes.cadastro import cadastro_bp
from routes.admin import admin_bp
from routes.assinatura import assinatura_bp
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

 
@app.cli.command("create-user")
@click.argument("name")
def create_user(name):
    print(f"Usuário '{name}' criado com sucesso!")

# Executa o servidor Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
=======
from flask import Flask
from routes.auth import auth_bp
from routes.ordens import ordens_bp
from routes.cadastro import cadastro_bp
from routes.admin import admin_bp
from routes.assinatura import assinatura_bp
from models.database import init_db
import click

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Inicializa o banco de dados
init_db()

# Registra os blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(ordens_bp)
app.register_blueprint(cadastro_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(assinatura_bp)

# Comando customizado via CLI
@app.cli.command("create-user")
@click.argument("name")
def create_user(name):
    print(f"Usuário '{name}' criado com sucesso!")

# Executa o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> 01822b7 (Primeiro commit do sistema SaaS de ordens)
