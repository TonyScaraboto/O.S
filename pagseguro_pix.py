<<<<<<< HEAD
import requests
import json

# Substitua pelos seus dados reais do PagSeguro
PAGSEGURO_CLIENT_ID = '63e7d657-d270-4a39-8167-7fe5ef74078272a5de0b4d63aead90b86a91df82395131a0-13fd-4b3a-a4bd-b2980a646530'
PAGSEGURO_CLIENT_SECRET = '63e7d657-d270-4a39-8167-7fe5ef74078272a5de0b4d63aead90b86a91df82395131a0-13fd-4b3a-a4bd-b2980a646530'
PAGSEGURO_PIX_RECEIVER = 'comicsultimate@gmail.com'  # Chave Pix
PAGSEGURO_API_BASE = 'https://pix.api.pagseguro.com'  # Produção

# Função para obter token OAuth2

def get_pagseguro_token():
    url = f'{PAGSEGURO_API_BASE}/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': PAGSEGURO_CLIENT_ID,
        'client_secret': PAGSEGURO_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

# Função para criar cobrança Pix

def criar_cobranca_pix(valor, nome_cliente, email_cliente):
    token = get_pagseguro_token()
    url = f'{PAGSEGURO_API_BASE}/instant-payments/cob'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'calendario': {'expiracao': 3600},
        'devedor': {
            'nome': nome_cliente,
            'cpf': '00000000000'  # Opcional, pode ser removido
        },
        'valor': {'original': f'{valor:.2f}'},
        'chave': PAGSEGURO_PIX_RECEIVER,
        'solicitacaoPagador': f'Cadastro SaaS para {email_cliente}'
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()

# Função para consultar status do pagamento

def consultar_status_pix(txid):
    token = get_pagseguro_token()
    url = f'{PAGSEGURO_API_BASE}/instant-payments/cob/{txid}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
=======
import requests
import json

# Substitua pelos seus dados reais do PagSeguro
PAGSEGURO_CLIENT_ID = 'SEU_CLIENT_ID'
PAGSEGURO_CLIENT_SECRET = 'SEU_CLIENT_SECRET'
PAGSEGURO_PIX_RECEIVER = 'comicsultimate@gmail.com'  # Chave Pix
PAGSEGURO_API_BASE = 'https://pix.sandbox.api.pagseguro.com'  # Use sandbox para testes

# Função para obter token OAuth2

def get_pagseguro_token():
    url = f'{PAGSEGURO_API_BASE}/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': PAGSEGURO_CLIENT_ID,
        'client_secret': PAGSEGURO_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

# Função para criar cobrança Pix

def criar_cobranca_pix(valor, nome_cliente, email_cliente):
    token = get_pagseguro_token()
    url = f'{PAGSEGURO_API_BASE}/instant-payments/cob'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'calendario': {'expiracao': 3600},
        'devedor': {
            'nome': nome_cliente,
            'cpf': '00000000000'  # Opcional, pode ser removido
        },
        'valor': {'original': f'{valor:.2f}'},
        'chave': PAGSEGURO_PIX_RECEIVER,
        'solicitacaoPagador': f'Cadastro SaaS para {email_cliente}'
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()

# Função para consultar status do pagamento

def consultar_status_pix(txid):
    token = get_pagseguro_token()
    url = f'{PAGSEGURO_API_BASE}/instant-payments/cob/{txid}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
>>>>>>> 01822b7 (Primeiro commit do sistema SaaS de ordens)
