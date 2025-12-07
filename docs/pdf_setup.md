# Configuração de PDF (PDFShift)

Este projeto suporta geração de PDF via API PDFShift.

## Variáveis de ambiente

- `PDFSHIFT_API_KEY`: sua chave da API PDFShift (obrigatória para baixar PDF).
- `PDFSHIFT_URL`: opcional, endpoint da API. Padrão: `https://api.pdfshift.io/v3/convert/pdf`.
- `ENABLE_STATUS_ROUTES=1`: opcional para habilitar rotas de diagnóstico em produção temporariamente.
- `USE_WEASYPRINT=1` (apenas local): opcional para forçar o motor local WeasyPrint via query `?engine=weasy` ou em modo debug caso não exista chave PDFShift.
- `WKHTMLTOPDF_BIN` ou `WKHTMLTOPDF_PATH`: caminho do binário `wkhtmltopdf` para uso com `pdfkit` (Windows/Linux). Se não definido, tentamos caminhos padrões.

## Verificação rápida

Com as rotas de status habilitadas (`ENABLE_STATUS_ROUTES=1`), acesse:

- `/__status/pdf` para checar se a chave da API está presente e o URL utilizado.
- `/__status/db` para checar o banco de dados ativo.

## Uso das rotas

- Visualizar PDF no navegador: `GET /pdf_ordem/<id>`
- Baixar PDF com PDFShift: `GET /pdf_ordem_api/<id>`
  - Aceita `?url=https://...` para gerar diretamente a partir de uma URL pública.
  - Fallback local: `GET /pdf_ordem_api/<id>?engine=weasy` (requer dependências do WeasyPrint instaladas localmente).
  - Alternativa local (pdfkit/wkhtmltopdf): `GET /pdf_ordem_api/<id>?engine=pdfkit` (requer `wkhtmltopdf` instalado e acessível; opcionalmente configure `WKHTMLTOPDF_BIN` ou `WKHTMLTOPDF_PATH`).

## Requisitos

- `requests` já está no `requirements.txt`.
- O template `templates/pdf_ordem.html` renderiza o HTML da O.S.

## Notas

- Em ambientes serverless, evite SQLite; configure `DATABASE_URL` para Postgres/MySQL conforme `docs/database_setup.md`.
- Não exponha sua `PDFSHIFT_API_KEY` publicamente. As rotas de status nunca retornam o valor da chave, apenas se ela está presente.
- Se o PDF ficar sem estilo, é esperado: o template embute CSS mínimo; CDNs externos (Bootstrap) podem ser bloqueados ou não carregados.
- Em Vercel, o uso de `wkhtmltopdf` não é suportado; utilize PDFShift. O `pdfkit` é útil em ambiente local/desktop.
