# Configuração de PDF (PDFShift)

Este projeto suporta geração de PDF via API PDFShift.

## Variáveis de ambiente

- `PDFSHIFT_API_KEY`: sua chave da API PDFShift (obrigatória para baixar PDF).
- `PDFSHIFT_URL`: opcional, endpoint da API. Padrão: `https://api.pdfshift.io/v3/convert/pdf`.
- `ENABLE_STATUS_ROUTES=1`: opcional para habilitar rotas de diagnóstico em produção temporariamente.

## Verificação rápida

Com as rotas de status habilitadas (`ENABLE_STATUS_ROUTES=1`), acesse:

- `/__status/pdf` para checar se a chave da API está presente e o URL utilizado.
- `/__status/db` para checar o banco de dados ativo.

## Uso das rotas

- Visualizar PDF no navegador: `GET /pdf_ordem/<id>`
- Baixar PDF com PDFShift: `GET /pdf_ordem_api/<id>`
  - Aceita `?url=https://...` para gerar diretamente a partir de uma URL pública.

## Requisitos

- `requests` já está no `requirements.txt`.
- O template `templates/pdf_ordem.html` renderiza o HTML da O.S.

## Notas

- Em ambientes serverless, evite SQLite; configure `DATABASE_URL` para Postgres/MySQL conforme `docs/database_setup.md`.
- Não exponha sua `PDFSHIFT_API_KEY` publicamente. As rotas de status nunca retornam o valor da chave, apenas se ela está presente.
