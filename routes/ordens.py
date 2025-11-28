import sqlite3
from models.database import get_db_path
"""import pdfkit"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response, flash, send_from_directory, abort, current_app
from datetime import datetime, timedelta
from routes.saas_guard import checar_trial_e_pagamento

ordens_bp = Blueprint('ordens', __name__)

# Rota para exibir ordens agrupadas por mês usando o template ordens_por_mes.html
@ordens_bp.route('/ordens_por_mes')
def ordens_por_mes():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    user_email = session.get('user')
    is_admin = session.get('role') == 'admin'
    if is_admin:
        cursor.execute('SELECT * FROM ordens ORDER BY data_criacao DESC')
        todas_ordens = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM ordens WHERE cliente=? ORDER BY data_criacao DESC', (user_email,))
        todas_ordens = cursor.fetchall()
    conn.close()

    ordens_por_mes = {}
    for ordem in todas_ordens:
        if not ordem or ordem[8] is None:
            continue
        data = ordem[8][:7]  # yyyy-mm
        if data not in ordens_por_mes:
            ordens_por_mes[data] = []
        ordens_por_mes[data].append(ordem)

    return render_template('ordens_por_mes.html', ordens_por_mes=ordens_por_mes)

ordens_bp = Blueprint('ordens', __name__)

# Geração de PDF da ordem
@ordens_bp.route('/pdf_ordem/<int:id>')
def gerar_pdf(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id=?', (id,))
    ordem = cursor.fetchone()
    conn.close()

    if not ordem:
        return "Ordem não encontrada.", 404

    
    foto_nome = None
    if len(ordem) > 7 and ordem[7]:
        
        foto_nome = os.path.join(current_app.root_path, 'static', 'imagens', ordem[7])
        
        foto_nome = 'file:///' + foto_nome.replace('\\', '/').replace(' ', '%20')
    # PDF desativado para ambiente serverless
    html = render_template('pdf_ordem.html', ordem=ordem, foto_nome=foto_nome, now=datetime.now())
    return html

 
@ordens_bp.route('/dashboard')

def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Buscar dias restantes do trial para o usuário logado
    dias_trial_restantes = None
    data_fim_trial = None
    if 'user' in session and session.get('role') != 'admin':
        user_email = session.get('user')
        cursor.execute('SELECT data_fim_trial FROM clientes WHERE email=?', (user_email,))
        row = cursor.fetchone()
        if row and row[0]:
            data_fim_trial = row[0]
            dias_trial_restantes = (datetime.strptime(data_fim_trial, '%Y-%m-%d') - datetime.now()).days

    mes_atual = datetime.now().strftime('%Y-%m')
    user_email = session.get('user')
    is_admin = session.get('role') == 'admin'
    # Para ordens, admin vê tudo; para acessórios, todos só veem os próprios
    if is_admin:
        cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y-%m", data_criacao) = ?', (mes_atual,))
        total_ordens_mes = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y-%m", data_venda) = ? AND cliente=?', (mes_atual, user_email))
        total_acessorios_mes = cursor.fetchone()[0] or 0
    else:
        cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y-%m", data_criacao) = ? AND cliente=?', (mes_atual, user_email))
        total_ordens_mes = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y-%m", data_venda) = ? AND cliente=?', (mes_atual, user_email))
        total_acessorios_mes = cursor.fetchone()[0] or 0

    faturamento_mensal = total_ordens_mes + total_acessorios_mes

    historico_mensal = []
    meses = []
    valores = []
    for i in range(5, -1, -1):
        data_ref = datetime.now() - timedelta(days=30 * i)
        mes_ref = data_ref.strftime('%Y-%m')
        meses.append(mes_ref)
        if is_admin:
            cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y-%m", data_criacao) = ?', (mes_ref,))
            val_ordens = cursor.fetchone()[0] or 0
            cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y-%m", data_venda) = ? AND cliente=?', (mes_ref, user_email))
            val_acess = cursor.fetchone()[0] or 0
        else:
            cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y-%m", data_criacao) = ? AND cliente=?', (mes_ref, user_email))
            val_ordens = cursor.fetchone()[0] or 0
            cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y-%m", data_venda) = ? AND cliente=?', (mes_ref, user_email))
            val_acess = cursor.fetchone()[0] or 0
        valores.append(val_ordens + val_acess)
        historico_mensal.append({'mes': mes_ref, 'valor': val_ordens + val_acess})

    # Garantir todos os status possíveis
    status_possiveis = ['Recebido', 'Em análise', 'Concluído', 'Entregue']
    if is_admin:
        cursor.execute('SELECT status, COUNT(*) FROM ordens GROUP BY status')
        status_data = dict(cursor.fetchall())
    else:
        cursor.execute('SELECT status, COUNT(*) FROM ordens WHERE cliente=? GROUP BY status', (user_email,))
        status_data = dict(cursor.fetchall())
    status_labels = status_possiveis
    status_counts = [status_data.get(s, 0) for s in status_possiveis]

    conn.close()

    return render_template(
        'dashboard.html',
        faturamento_mensal=f"{faturamento_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        historico_mensal=historico_mensal,
        meses=meses,
        valores=valores,
        status_labels=status_labels,
        status_counts=status_counts,
        dias_trial_restantes=dias_trial_restantes,
        data_fim_trial=data_fim_trial
    )

# Cadastro de nova ordem
@ordens_bp.route('/nova_ordem', methods=['GET', 'POST'])

def nova_ordem():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    erro = None


    if request.method == 'POST':
        # O nome do cliente final é o campo preenchido pelo usuário,
        # enquanto o campo "cliente" na tabela representa o dono (email da assistência)
        nome_cliente = request.form.get('cliente', '').strip()
        telefone = request.form.get('telefone', '').strip()
        aparelho = request.form.get('aparelho', '').strip()
        defeito = request.form.get('defeito', '').strip()
        valor = request.form.get('valor', '').strip()
        status = request.form.get('status', 'Recebido')
        data_criacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        imagem_nome = None
        dono_email = session.get('user')

        if 'foto_ordem' in request.files:
            foto = request.files['foto_ordem']
            if foto and foto.filename:
                ext = os.path.splitext(foto.filename)[1]
                imagem_nome = f"{aparelho}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                pasta_imagens = os.path.join(current_app.root_path, 'static', 'imagens')
                try:
                    os.makedirs(pasta_imagens, exist_ok=True)
                    caminho = os.path.join(pasta_imagens, imagem_nome)
                    foto.save(caminho)
                except OSError as exc:
                    current_app.logger.warning('Não foi possível salvar a imagem da ordem: %s', exc)
                    flash('Não foi possível salvar a foto no ambiente atual. A ordem será registrada sem imagem.', 'warning')
                    imagem_nome = None

        if not nome_cliente or not telefone or not aparelho or not defeito or not valor:
            erro = "Preencha todos os campos obrigatórios."
        else:
            try:
                valor = float(valor.replace(",", "."))
                conn = sqlite3.connect(get_db_path())
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO ordens (cliente, telefone, aparelho, defeito, valor, status, imagem, data_criacao, nome_cliente) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (dono_email, telefone, aparelho, defeito, valor, status, imagem_nome, data_criacao, nome_cliente)
                )
                conn.commit()
                # Log para depuração
                print(f"Ordem criada: assistencia={dono_email}, cliente_final={nome_cliente}, aparelho={aparelho}, valor={valor}, data={data_criacao}")
                conn.close()
                return redirect(url_for('ordens.listar_ordens'))
            except Exception as e:
                print(f"Erro ao salvar ordem: {e}")
                erro = f"Erro ao salvar ordem: {e}"

    return render_template('nova_ordem.html', erro=erro)

# Listagem de ordens por mês
@ordens_bp.route('/listar_ordens')

def listar_ordens():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    user_email = session.get('user')
    is_admin = session.get('role') == 'admin'
    if is_admin:
        cursor.execute('SELECT * FROM ordens ORDER BY data_criacao DESC')
        todas_ordens = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM ordens WHERE cliente=? ORDER BY data_criacao DESC', (user_email,))
        todas_ordens = cursor.fetchall()
    conn.close()

    ordens_por_mes = {}
    for ordem in todas_ordens:
        # ordem[8] = data_criacao
        if not ordem or not ordem[8]:
            continue
        try:
            data = ordem[8][:7]  # yyyy-mm
        except Exception:
            data = 'Data inválida'
        if data not in ordens_por_mes:
            ordens_por_mes[data] = []
        ordens_por_mes[data].append(ordem)

    # Garante que pelo menos um mês apareça se não houver ordens
    if not ordens_por_mes:
        mes_atual = datetime.now().strftime('%Y-%m')
        ordens_por_mes[mes_atual] = []

    return render_template('ordens.html', ordens_por_mes=ordens_por_mes)

# Faturamento anual
@ordens_bp.route('/faturamento')

def faturamento():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    ano = datetime.now().strftime('%Y')
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    user_email = session.get('user')
    is_admin = session.get('role') == 'admin'

    if is_admin:
        cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y", data_criacao) = ?', (ano,))
        total_ordens = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y", data_venda) = ? AND cliente=?', (ano, user_email))
        total_acessorios = cursor.fetchone()[0] or 0
    else:
        cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y", data_criacao) = ? AND cliente=?', (ano, user_email))
        total_ordens = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y", data_venda) = ? AND cliente=?', (ano, user_email))
        total_acessorios = cursor.fetchone()[0] or 0

    # Histórico dos últimos 6 meses
    historico_mensal = []
    for i in range(5, -1, -1):
        data_ref = datetime.now() - timedelta(days=30 * i)
        mes_ref = data_ref.strftime('%Y-%m')
        if is_admin:
            cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y-%m", data_criacao) = ?', (mes_ref,))
            val_ordens = cursor.fetchone()[0] or 0
            cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y-%m", data_venda) = ? AND cliente=?', (mes_ref, user_email))
            val_acess = cursor.fetchone()[0] or 0
        else:
            cursor.execute('SELECT SUM(valor) FROM ordens WHERE strftime("%Y-%m", data_criacao) = ? AND cliente=?', (mes_ref, user_email))
            val_ordens = cursor.fetchone()[0] or 0
            cursor.execute('SELECT SUM(receita_total) FROM acessorios WHERE strftime("%Y-%m", data_venda) = ? AND cliente=?', (mes_ref, user_email))
            val_acess = cursor.fetchone()[0] or 0
        historico_mensal.append((mes_ref, f"{(val_ordens + val_acess):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")))

    conn.close()
    faturamento_total = total_ordens + total_acessorios

    return render_template('faturamento.html', faturamento=faturamento_total, historico_mensal=historico_mensal)

# Acessórios - listagem
@ordens_bp.route('/acessorios')

def listar_acessorios():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    user_email = session.get('user')
    # O admin agora só vê suas próprias vendas, igual aos outros usuários
    cursor.execute('SELECT * FROM acessorios WHERE cliente=? ORDER BY data_venda DESC', (user_email,))
    vendas = cursor.fetchall()
    cursor.execute('SELECT strftime("%Y-%m", data_venda) as mes, SUM(receita_total) FROM acessorios WHERE cliente=? GROUP BY mes ORDER BY mes DESC', (user_email,))
    historico_vendas = cursor.fetchall()
    conn.close()

    return render_template('acessorios.html', vendas=vendas, historico_vendas=historico_vendas)

# Acessórios - salvar
@ordens_bp.route('/salvar_acessorio', methods=['POST'])

def salvar_acessorio():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    nome = request.form.get('nome', '').strip()
    quantidade_raw = request.form.get('quantidade', '').strip()
    preco_raw = request.form.get('preco', '').strip()
    try:
        quantidade = int(quantidade_raw)
        preco_unitario = float(preco_raw.replace(',', '.'))
    except Exception:
        flash("Quantidade e preço devem ser números válidos.")
        return redirect(url_for('ordens.listar_acessorios'))
    receita_total = quantidade * preco_unitario
    data_venda = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cliente = session.get('user')

    # Se houver imagem de acessório, salvar corretamente
    imagem_nome = None
    if 'foto_acessorio' in request.files:
        foto = request.files['foto_acessorio']
        if foto and foto.filename:
            ext = os.path.splitext(foto.filename)[1]
            imagem_nome = f"{nome}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            pasta_imagens = os.path.join(current_app.root_path, 'static', 'imagens')
            if not os.path.exists(pasta_imagens):
                os.makedirs(pasta_imagens)
            caminho = os.path.join(pasta_imagens, imagem_nome)
            foto.save(caminho)

    if not nome or quantidade <= 0 or preco_unitario <= 0:
        flash("Preencha todos os campos corretamente.")
        return redirect(url_for('ordens.listar_acessorios'))

    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Adiciona imagem se existir
        if imagem_nome:
            cursor.execute('''
                INSERT INTO acessorios (nome, quantidade, preco_unitario, receita_total, data_venda, cliente, imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, quantidade, preco_unitario, receita_total, data_venda, cliente, imagem_nome))
        else:
            cursor.execute('''
                INSERT INTO acessorios (nome, quantidade, preco_unitario, receita_total, data_venda, cliente)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, quantidade, preco_unitario, receita_total, data_venda, cliente))
        conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Erro ao registrar venda: {e}")
        return redirect(url_for('ordens.listar_acessorios'))

    return redirect(url_for('ordens.listar_acessorios'))

# Acessórios - remover
@ordens_bp.route('/remover_acessorio/<int:id>', methods=['POST'])

def remover_acessorio(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    user_email = session.get('user')
    is_admin = session.get('role') == 'admin'
    if is_admin:
        cursor.execute('DELETE FROM acessorios WHERE id = ?', (id,))
    else:
        cursor.execute('DELETE FROM acessorios WHERE id = ? AND cliente = ?', (id, user_email))
    conn.commit()
    conn.close()

    return redirect(url_for('ordens.listar_acessorios'))

 
@ordens_bp.route('/atualizar_status/<int:id>', methods=['POST'])
def atualizar_status(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio
    novo_status = request.form.get('status', 'Pendente')
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('UPDATE ordens SET status=? WHERE id=?', (novo_status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('ordens.listar_ordens'))

import urllib.parse

# Listagem de PDFs agrupados por mês

# Download de PDF específico

@ordens_bp.route('/download_ordens')
def download_ordens():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio

    mes = request.args.get('mes')
    arquivo = request.args.get('arquivo')
    if not mes or not arquivo:
        abort(404)

    pasta = os.path.join(current_app.root_path, 'static', 'pdfs')
    arquivo_path = os.path.join(pasta, arquivo)
    if not os.path.exists(arquivo_path):
        abort(404)

    # Forçar download
    return send_from_directory(pasta, arquivo, as_attachment=True)

@ordens_bp.route('/excluir_os/<int:id>', methods=['POST'])
def excluir_os(id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    bloqueio = checar_trial_e_pagamento()
    if bloqueio:
        return bloqueio
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ordens WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('ordens.listar_ordens'))