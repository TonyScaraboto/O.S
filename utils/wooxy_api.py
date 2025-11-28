import os
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class WooxyAPIError(Exception):
    """Erro de integração com a Wooxy."""


def _get_base_url() -> str:
    return os.environ.get('WOOXY_BASE_URL', 'https://api.wooxy.com/api/v1')


def _get_basic_token() -> str:
    token = os.environ.get('WOOXY_BASIC_TOKEN') or os.environ.get('WOOXY_TOKEN')
    if not token:
        raise WooxyAPIError('Token da Wooxy não configurado (WOOXY_BASIC_TOKEN).')
    return token.strip()


def _nested_get(data: Dict[str, Any], *paths: str) -> Optional[Any]:
    for path in paths:
        parts = path.split('.')
        node: Any = data
        for part in parts:
            if isinstance(node, dict):
                node = node.get(part)
            else:
                node = None
                break
        if node:
            return node
    return None


def _normalize_qr_image(raw_value: Optional[str]) -> Optional[str]:
    if not raw_value:
        return None
    value = raw_value.strip()
    if value.startswith('data:image'):
        return value
    return f'data:image/png;base64,{value}'


def create_charge(*, valor: float, plano: str, nome_cliente: str, email_cliente: str) -> Dict[str, Optional[str]]:
    """Cria uma cobrança Pix via Wooxy e retorna dados normalizados."""
    token = _get_basic_token()
    payload = {
        'amount': f'{valor:.2f}',
        'currency': 'BRL',
        'description': f'Assinatura {plano} - {nome_cliente}',
        'customer': {
            'name': nome_cliente,
            'email': email_cliente,
        },
        'metadata': {
            'plan': plano,
        },
        'payment_method': 'PIX'
    }
    headers = {
        'Authorization': f'Basic {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    timeout = float(os.environ.get('WOOXY_TIMEOUT', '20'))

    url = f"{_get_base_url().rstrip('/')}/charges"
    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.error('Wooxy retornou erro HTTP: %s | %s', exc, response.text)
        raise WooxyAPIError('Falha ao criar cobrança na Wooxy.') from exc

    data = response.json()
    charge_id = _nested_get(data, 'id', 'charge_id', 'data.id', 'payload.id')
    qr_image = _nested_get(
        data,
        'qr.image',
        'qr_image',
        'qrCodeImage',
        'data.qr_code.image',
        'payload.qr_code.image'
    )
    qr_text = _nested_get(
        data,
        'qr.text',
        'qr_payload',
        'qr_text',
        'qrCodeText',
        'pix.copia_cola',
        'payload.pixCopyAndPaste',
        'pix.copy_paste'
    )

    normalized_image = _normalize_qr_image(qr_image)

    return {
        'charge_id': charge_id,
        'qr_image': normalized_image,
        'qr_payload': qr_text,
        'qr_copia_cola': qr_text,
        'raw_response': data,
    }
*** End Patch