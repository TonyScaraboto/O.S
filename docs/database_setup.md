# Banco de dados compartilhado

## 1. Preparar o MySQL
- Crie um banco chamado `scartech_saas` no servidor desejado (pode ser localhost ou serviços como PlanetScale/Railway/Render).
- Libere o usuário que vai ser usado pela aplicação (ex.: `root`).
- Se o servidor estiver exposto, habilite SSL/TLS obrigatório.

## 2. Variáveis de ambiente
A aplicação lê automaticamente um arquivo `.env` (graças ao `python-dotenv`). Use o modelo `.env.example` e ajuste os valores reais.

> **Importante:** Em ambientes serverless (Vercel, Railway, etc.) a aplicação agora exige que `DATABASE_URL` esteja configurada. Sem ela, o app não sobe, evitando o antigo comportamento de criar um SQLite temporário em `/tmp` e perder os dados após cada deploy.

```
DATABASE_URL=mysql+mysqlconnector://root:SUA_SENHA@localhost:3306/scartech_saas
PGSSLMODE=require
```

Observações:
- Caracteres especiais precisam estar codificados na URL (`!` → `%21`, `@` → `%40`, etc.).
- Para o cenário informado (`root` e senha `jessicajasmim13!`), a URL fica:
  `mysql+mysqlconnector://root:jessicajasmim13%21@localhost:3306/scartech_saas`
- Em produção, defina a mesma variável diretamente no painel do provedor (Vercel, etc.).

## 3. Migração de dados do SQLite
1. Faça backup do arquivo atual `ordens.db`.
2. Gere um dump legível:
   ```bash
   sqlite3 ordens.db ".dump" > dump.sql
   ```
3. Edite o `dump.sql` removendo comandos específicos do SQLite (`PRAGMA`, `BEGIN TRANSACTION`, `COMMIT`) e ajuste tipos se necessário.
4. Importe no MySQL:
   ```bash
   mysql -u root -p scartech_saas < dump.sql
   ```
5. Suba a aplicação com a `DATABASE_URL` apontando para o MySQL e rode `python app.py` (ou o comando do servidor). O `init_db()` vai garantir colunas e usuários padrão.

## 4. Checklist rápido
- [ ] Instalar dependências: `pip install -r requirements.txt`.
- [ ] Criar/ajustar `.env` com `DATABASE_URL`.
- [ ] Em produção/Vercel, definir `DATABASE_URL` no painel do projeto.
- [ ] Garantir que o MySQL aceita conexões externas (quando necessário).
- [ ] Opcional: migrar dados antigos usando o passo 3.
- [ ] Iniciar a aplicação (`python app.py` ou o comando de deploy) e validar login em múltiplas máquinas.
