from datetime import datetime
from typing import Any, Dict, Iterable, Optional

ORDER_COLUMNS = [
    'id',
    'cliente',
    'telefone',
    'aparelho',
    'defeito',
    'valor',
    'status',
    'imagem',
    'data_criacao',
    'nome_cliente',
    'fornecedor',
    'custo_peca',
]


def row_to_ordem_dict(row: Optional[Iterable[Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = {}
    for idx, column in enumerate(ORDER_COLUMNS):
        if idx >= len(row):
            break
        data[column] = row[idx]
    return data


def format_currency(value: Any) -> str:
    try:
        numeric = float(value or 0)
    except (TypeError, ValueError):
        numeric = 0.0
    return f"{numeric:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def format_ordem_date(value: Optional[str]) -> str:
    if not value:
        return datetime.now().strftime('%d/%m/%Y')
    for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(value, pattern).strftime('%d/%m/%Y')
        except ValueError:
            continue
    return value


def cliente_display(ordem: Optional[Dict[str, Any]]) -> str:
    if not ordem:
        return ''
    return (ordem.get('nome_cliente') or ordem.get('cliente') or '').strip()


def normalize_email(value: Optional[str]) -> str:
    return (value or '').strip().lower()


def _cliente_from_row(row: Optional[Iterable[Any]]) -> str:
    if not row:
        return ''
    if len(row) > 9 and row[9]:
        return str(row[9]).strip()
    if len(row) > 1 and row[1]:
        return str(row[1]).strip()
    return ''


def build_pdf_context(row: Optional[Iterable[Any]]) -> Dict[str, Any]:
    ordem_dict = row_to_ordem_dict(row)
    cliente = cliente_display(ordem_dict) or _cliente_from_row(row)
    valor = format_currency(ordem_dict.get('valor') if ordem_dict else None)
    custo_raw = ordem_dict.get('custo_peca') if ordem_dict else None
    custo = format_currency(custo_raw) if custo_raw not in (None, '', 0) else None
    data = format_ordem_date(ordem_dict.get('data_criacao') if ordem_dict else None)
    status = (ordem_dict.get('status') if ordem_dict else None) or 'Recebido'
    telefone = None
    aparelho = None
    defeito = None
    if ordem_dict:
        telefone = ordem_dict.get('telefone')
        aparelho = ordem_dict.get('aparelho')
        defeito = ordem_dict.get('defeito')
    elif row:
        telefone = row[2] if len(row) > 2 else None
        aparelho = row[3] if len(row) > 3 else None
        defeito = row[4] if len(row) > 4 else None
    return {
        'ordem_dict': ordem_dict,
        'cliente': cliente,
        'valor_formatado': valor,
        'custo_formatado': custo,
        'data_formatada': data,
        'status': status,
        'telefone': telefone,
        'aparelho': aparelho,
        'defeito': defeito,
    }
