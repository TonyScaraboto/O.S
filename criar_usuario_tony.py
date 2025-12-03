import sqlite3
from datetime import datetime
from models.database import get_db_path


def main():
	conn = sqlite3.connect(get_db_path())
	cursor = conn.cursor()
	cursor.execute("DELETE FROM clientes WHERE email = ?", ('tony',))
	cursor.execute("DELETE FROM usuarios WHERE username = ?", ('tony',))
	cursor.execute(
		"INSERT INTO clientes (nome_assistencia, nome_usuario, email, senha, senha_pura, data_cadastro, trial_ativo, assinatura_ativa) VALUES (?, ?, ?, ?, ?, ?, 1, 1)",
		(
			'Tony Assistência',
			'Tony Assistência',
			'tony',
			'tony123',
			'tony123',
			datetime.now().strftime('%Y-%m-%d')
		)
	)
	cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)", ('tony', 'tony123', 'cliente'))
	conn.commit()
	conn.close()
	print('Usuário tony criado com sucesso!')


if __name__ == '__main__':
	main()
