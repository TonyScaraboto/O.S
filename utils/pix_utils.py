import qrcode
import base64
import io
from typing import Optional

def gerar_payload_pix(chave_pix: str, valor: float, nome_recebedor: str = "Assistência Técnica", cidade: str = "SAO PAULO") -> str:
    """Gera o payload do PIX conforme especificação do Banco Central."""
    # ID do Payload Format Indicator
    payload = "000201"

    # ID do Point of Initiation Method (estático)
    payload += "010211"

    # ID do Merchant Account Information
    # GUI
    payload += "26460014BR.GOV.BCB.PIX"

    # Chave
    chave_len = f"{len(chave_pix):02d}"
    payload += f"01{chave_len}{chave_pix}"

    # ID do Merchant Category Code
    payload += "52040000"

    # ID do Transaction Currency
    payload += "5303986"

    # ID do Transaction Amount
    if valor > 0:
        valor_str = f"{valor:.2f}".replace('.', '')
        payload += f"54{len(valor_str):02d}{valor_str}"

    # ID do Country Code
    payload += "5802BR"

    # ID do Merchant Name
    nome_len = f"{len(nome_recebedor):02d}"
    payload += f"59{nome_len}{nome_recebedor}"

    # ID do Merchant City
    cidade_len = f"{len(cidade):02d}"
    payload += f"60{cidade_len}{cidade}"

    # ID do Additional Data Field
    payload += "62070503***"

    # ID do CRC16
    payload += "6304"

    # Calcular CRC16
    crc = crc16_ccitt(payload.encode('utf-8'))
    payload += crc

    return payload

def crc16_ccitt(data: bytes) -> str:
    """Calcula CRC16-CCITT."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def gerar_qr_pix_base64(payload: str) -> str:
    """Gera QR code em base64 a partir do payload PIX."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"

def criar_cobranca_pix_local(chave_pix: str, valor: float, nome_cliente: str, plano: str) -> dict:
    """Cria cobrança PIX localmente."""
    payload = gerar_payload_pix(chave_pix, valor, "Assistência Técnica")
    qr_base64 = gerar_qr_pix_base64(payload)

    return {
        'charge_id': f"local_{nome_cliente}_{plano}_{valor}",
        'qr_image': qr_base64,
        'qr_payload': payload,
        'qr_copia_cola': payload,
    }