<<<<<<< HEAD
# Sistema SaaS de Ordens de Serviço

Este é um sistema SaaS (Software como Serviço) para gestão de ordens de serviço, multi-tenant, com controle de período gratuito, cobrança automática via Pix (PagSeguro), painel administrativo e interface moderna.

## Funcionalidades

## Instalação
1. Clone o repositório:
   ```sh
   git clone https://github.com/TonyScaraboto/ordem-servico-saas.git
   cd ordem-servico-saas
   ```
2. Crie e ative um ambiente virtual:
   ```sh
   python -m venv venv
   venv\Scripts\activate  # Windows
   # ou
   source venv/bin/activate  # Linux/Mac
   ```
3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
4. Execute o sistema:
   ```sh
   python app.py
   ```
5. Acesse no navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Configuração PagSeguro Pix

## Estrutura de Pastas

## Observações

Desenvolvido por Scartech Solution.
=======
# Sistema SaaS de Ordens de Serviço

Este é um sistema SaaS (Software como Serviço) para gestão de ordens de serviço, multi-tenant, com controle de período gratuito, cobrança automática via Pix (PagSeguro), painel administrativo e interface moderna.

## Funcionalidades
- Cadastro multi-tenant de assistências técnicas
- Período gratuito de 15 dias para novos clientes
- Cobrança mensal automática via Pix (PagSeguro)
- Bloqueio automático após o período gratuito se não houver pagamento
- Painel do cliente com status da assinatura
- Dashboard com gráficos e indicadores
- Cadastro e gerenciamento de ordens, acessórios e clientes
- Interface moderna (login/cadastro com fundo tecnológico)

## Instalação
1. Clone o repositório:
   ```sh
   git clone https://github.com/TonyScaraboto/ordem-servico-saas.git
   cd ordem-servico-saas
   ```
2. Crie e ative um ambiente virtual:
   ```sh
   python -m venv venv
   venv\Scripts\activate  # Windows
   # ou
   source venv/bin/activate  # Linux/Mac
   ```
3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
4. Execute o sistema:
   ```sh
   python app.py
   ```
5. Acesse no navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Configuração PagSeguro Pix
- Configure suas credenciais PagSeguro no arquivo `pagseguro_pix.py`.
- O sistema gera QR Code Pix automaticamente no cadastro.

## Estrutura de Pastas
- `app.py` — Arquivo principal Flask
- `models/` — Banco de dados e modelos
- `routes/` — Rotas do sistema (login, cadastro, admin, ordens, etc)
- `templates/` — Templates HTML (Jinja2)
- `static/` — Arquivos estáticos (CSS, imagens)
- `requirements.txt` — Dependências Python

## Observações
- Use apenas para fins educacionais ou como base para projetos comerciais.
- Para produção, utilize um servidor WSGI (ex: gunicorn) e configure variáveis de ambiente seguras.

---
Desenvolvido por Scartech Solution.
>>>>>>> 1b805bc (Multi-tenant: cada assistência vê apenas seus dados, correções de acesso, painel e faturamento anual isolados por empresa)
