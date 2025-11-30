import json
import os
import requests

PAGSEGURO_API_BASE = os.environ.get('PAGSEGURO_API_BASE', 'https://pix.api.pagseguro.com')


def _get_client_id():
    value = os.environ.get('PAGSEGURO_CLIENT_ID')
    if not value:
        raise RuntimeError('PAGSEGURO_CLIENT_ID não configurado.')
    return value


def _get_client_secret():
    value = os.environ.get('PAGSEGURO_CLIENT_SECRET')
    if not value:
        raise RuntimeError('PAGSEGURO_CLIENT_SECRET não configurado.')
    return value


def _get_pix_receiver():
    value = os.environ.get('PAGSEGURO_PIX_RECEIVER')
    if not value:
        raise RuntimeError('PAGSEGURO_PIX_RECEIVER não configurado.')
    return value


def get_pagseguro_token():
    url = f'{PAGSEGURO_API_BASE}/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': _get_client_id(),
        'client_secret': _get_client_secret()
    }
    response = requests.post(url, headers=headers, data=data, timeout=20)
    response.raise_for_status()
    return response.json()['access_token']


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
            'cpf': '00000000000'
        },
        'valor': {'original': f'{valor:.2f}'},
        'chave': _get_pix_receiver(),
        'solicitacaoPagador': f'Cadastro SaaS para {email_cliente}'
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    response.raise_for_status()
    return response.json()


def consultar_status_pix(txid):
    token = get_pagseguro_token()
    url = f'{PAGSEGURO_API_BASE}/instant-payments/cob/{txid}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()
