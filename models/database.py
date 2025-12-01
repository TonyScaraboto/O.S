import os
import sqlite3
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
PARSED_DB_URL = urlparse(DATABASE_URL) if DATABASE_URL else None


def _extract_scheme():
    if not PARSED_DB_URL or not PARSED_DB_URL.scheme:
        return ''
    return PARSED_DB_URL.scheme.split('+')[0].lower()


BASE_SCHEME = _extract_scheme()
IS_POSTGRES = BASE_SCHEME in ('postgresql', 'postgres')
IS_MYSQL = BASE_SCHEME == 'mysql'
IS_SQLITE_URL = BASE_SCHEME == 'sqlite'
DB_NAME = PARSED_DB_URL.path.lstrip('/') if PARSED_DB_URL and PARSED_DB_URL.path else None

try:
    import psycopg2  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None

try:
    import mysql.connector as mysql_connector  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    mysql_connector = None


def _parse_db_url():
    if not PARSED_DB_URL:
        return {}
    options = {key: values[-1] for key, values in parse_qs(PARSED_DB_URL.query).items()}
    return {
        'username': unquote(PARSED_DB_URL.username) if PARSED_DB_URL.username else None,
        'password': unquote(PARSED_DB_URL.password) if PARSED_DB_URL.password else None,
        'host': PARSED_DB_URL.hostname or '127.0.0.1',
        'port': PARSED_DB_URL.port,
        'database': DB_NAME,
        'options': options,
    }


DB_CONFIG = _parse_db_url()


def get_db_path():
    if os.environ.get('VERCEL_ENV'):
        return '/tmp/ordens.db'
    return 'ordens.db'


class _ParamCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    @staticmethod
    def _translate(query: str) -> str:
        return query.replace('?', '%s')

    def execute(self, query, params=None):
        self._cursor.execute(self._translate(query), params)
        return self

    def executemany(self, query, param_list):
        self._cursor.executemany(self._translate(query), param_list)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description


class PostgresConnection:
    def __init__(self):
        if psycopg2 is None:
            raise RuntimeError('psycopg2-binary não está instalado. Verifique requirements.txt')
        sslmode = os.environ.get('PGSSLMODE') or DB_CONFIG.get('options', {}).get('sslmode') or 'require'
        self._conn = psycopg2.connect(DATABASE_URL, sslmode=sslmode)

    def cursor(self):
        return _ParamCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


class MySQLConnection:
    def __init__(self):
        if mysql_connector is None:
            raise RuntimeError('mysql-connector-python não está instalado. Verifique requirements.txt')
        if not DB_CONFIG.get('database'):
            raise RuntimeError('DATABASE_URL precisa informar o nome do banco para conexões MySQL.')
        options = DB_CONFIG.get('options', {})
        conn_kwargs = {
            'user': DB_CONFIG.get('username') or 'root',
            'password': DB_CONFIG.get('password'),
            'host': DB_CONFIG.get('host') or '127.0.0.1',
            'port': DB_CONFIG.get('port') or 3306,
            'database': DB_CONFIG.get('database'),
            'autocommit': False,
            'charset': options.get('charset', 'utf8mb4'),
        }
        if options.get('ssl-mode'):
            conn_kwargs['ssl_disabled'] = options['ssl-mode'].lower() == 'disabled'
        self._conn = mysql_connector.connect(**conn_kwargs)

    def cursor(self):
        return _ParamCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def _sqlite_path_from_url():
    if not PARSED_DB_URL:
        return get_db_path()
    path = PARSED_DB_URL.path or ''
    if os.name == 'nt':
        path = path.lstrip('/')
    return path or get_db_path()


def get_connection():
    if IS_POSTGRES:
        return PostgresConnection()
    if IS_MYSQL:
        return MySQLConnection()
    if IS_SQLITE_URL:
        return sqlite3.connect(_sqlite_path_from_url())
    return sqlite3.connect(get_db_path())


def _auto_increment_pk():
    if IS_POSTGRES:
        return 'SERIAL PRIMARY KEY'
    if IS_MYSQL:
        return 'INT AUTO_INCREMENT PRIMARY KEY'
    return 'INTEGER PRIMARY KEY AUTOINCREMENT'


def _ensure_column(cursor, table, column_name, column_def, default_value=None):
    if IS_POSTGRES:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {column_def}")
        if default_value is not None:
            cursor.execute(
                f"UPDATE {table} SET {column_name}=? WHERE {column_name} IS NULL",
                (default_value,)
            )
    elif IS_MYSQL:
        cursor.execute(
            '''
            SELECT 1 FROM information_schema.columns
            WHERE table_schema=? AND table_name=? AND column_name=?
            ''',
            (DB_CONFIG.get('database'), table, column_name)
        )
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
            if default_value is not None:
                cursor.execute(
                    f"UPDATE {table} SET {column_name}=? WHERE {column_name} IS NULL",
                    (default_value,)
                )
    else:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            return
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
            if default_value is not None:
                cursor.execute(f"UPDATE {table} SET {column_name}=?", (default_value,))


def _insert_default_client(cursor):
    if IS_POSTGRES:
        cursor.execute(
            '''
            INSERT INTO clientes (nome_assistencia, nome_usuario, email, senha, senha_pura, data_cadastro, trial_ativo, data_fim_trial, assinatura_ativa)
            VALUES ('ADMIN', 'ADMIN', 'admin@saas.com', 'admin123', 'admin123', '2024-01-01', 0, NULL, 1)
            ON CONFLICT (email) DO NOTHING
            '''
        )
    elif IS_MYSQL:
        cursor.execute(
            '''
            INSERT IGNORE INTO clientes (nome_assistencia, nome_usuario, email, senha, senha_pura, data_cadastro, trial_ativo, data_fim_trial, assinatura_ativa)
            VALUES ('ADMIN', 'ADMIN', 'admin@saas.com', 'admin123', 'admin123', '2024-01-01', 0, NULL, 1)
            '''
        )
    else:
        cursor.execute(
            '''
            INSERT OR IGNORE INTO clientes (nome_assistencia, nome_usuario, email, senha, senha_pura, data_cadastro, trial_ativo, data_fim_trial, assinatura_ativa)
            VALUES ('ADMIN', 'ADMIN', 'admin@saas.com', 'admin123', 'admin123', '2024-01-01', 0, NULL, 1)
            '''
        )


def _insert_default_users(cursor):
    if IS_POSTGRES:
        cursor.execute(
            '''
            INSERT INTO usuarios (username, password, role)
            VALUES ('admin','admin123','admin')
            ON CONFLICT (username) DO NOTHING
            '''
        )
        cursor.execute(
            '''
            INSERT INTO usuarios (username, password, role)
            VALUES ('tecnico','tecnico123','tecnico')
            ON CONFLICT (username) DO NOTHING
            '''
        )
    elif IS_MYSQL:
        cursor.execute(
            '''
            INSERT IGNORE INTO usuarios (username, password, role)
            VALUES ('admin','admin123','admin')
            '''
        )
        cursor.execute(
            '''
            INSERT IGNORE INTO usuarios (username, password, role)
            VALUES ('tecnico','tecnico123','tecnico')
            '''
        )
    else:
        cursor.execute(
            '''
            INSERT OR IGNORE INTO usuarios (username, password, role)
            VALUES 
                ('admin', 'admin123', 'admin'),
                ('tecnico', 'tecnico123', 'tecnico')
            '''
        )


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    clientes_pk = _auto_increment_pk()
    cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS clientes (
            id {clientes_pk},
            nome_assistencia TEXT NOT NULL,
            nome_usuario TEXT,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_cadastro TEXT NOT NULL,
            trial_ativo INTEGER DEFAULT 1,
            data_fim_trial TEXT,
            assinatura_ativa INTEGER DEFAULT 0,
            data_ultimo_pagamento TEXT,
            pix_pagamento TEXT DEFAULT 'comicsultimate@gmail.com'
        )
        '''
    )

    _ensure_column(cursor, 'clientes', 'foto_perfil', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'senha_pura', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'pix_pagamento', "TEXT DEFAULT 'comicsultimate@gmail.com'", 'comicsultimate@gmail.com')
    _ensure_column(cursor, 'clientes', 'assinatura_ativa', 'INTEGER DEFAULT 0', 0)
    _ensure_column(cursor, 'clientes', 'trial_ativo', 'INTEGER DEFAULT 1', 1)
    _ensure_column(cursor, 'clientes', 'data_cadastro', 'TEXT', datetime.now().strftime('%Y-%m-%d'))
    _ensure_column(cursor, 'clientes', 'data_fim_trial', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'plano_nome', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'plano_valor', 'REAL', None)
    _ensure_column(cursor, 'clientes', 'wooxy_charge_id', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'wooxy_qr_code', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'wooxy_copia_cola', 'TEXT', None)
    _ensure_column(cursor, 'clientes', 'nome_usuario', 'TEXT', None)
    cursor.execute('UPDATE clientes SET nome_usuario = nome_assistencia WHERE nome_usuario IS NULL OR nome_usuario = ?', ('',))
    _insert_default_client(cursor)

    usuarios_pk = _auto_increment_pk()
    cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS usuarios (
            id {usuarios_pk},
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        '''
    )

    ordens_pk = _auto_increment_pk()
    cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS ordens (
            id {ordens_pk},
            cliente TEXT NOT NULL,
            telefone TEXT NOT NULL,
            aparelho TEXT NOT NULL,
            defeito TEXT NOT NULL,
            valor REAL NOT NULL,
            status TEXT NOT NULL,
            imagem TEXT,
            data_criacao TEXT NOT NULL
        )
        '''
    )
    _ensure_column(cursor, 'ordens', 'nome_cliente', 'TEXT', None)
    _ensure_column(cursor, 'ordens', 'fornecedor', 'TEXT', None)
    _ensure_column(cursor, 'ordens', 'custo_peca', 'REAL DEFAULT 0', 0)

    acessorios_pk = _auto_increment_pk()
    cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS acessorios (
            id {acessorios_pk},
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            receita_total REAL NOT NULL,
            data_venda TEXT NOT NULL,
            cliente TEXT NOT NULL,
            imagem TEXT
        )
        '''
    )
    _ensure_column(cursor, 'acessorios', 'imagem', 'TEXT', None)

    _insert_default_users(cursor)
    conn.commit()
    conn.close()