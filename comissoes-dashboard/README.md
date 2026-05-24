# Comissões Dashboard

Projeto que automatiza o download, tratamento e visualização do acervo das Comissões da Câmara Municipal de São Paulo.

## Funcionalidades

- Download automático de dados das Comissões
- Tratamento e processamento de dados em Excel
- Dashboard interativo para visualização dos dados
- API REST para acesso aos dados processados

## Estrutura do Projeto

```
comissoes-dashboard/
├── scripts/           # Scripts Python para automação
├── data/
│   ├── raw/          # Dados brutos baixados
│   └── processed/    # Dados processados
├── dashboard/
│   ├── js/           # Arquivos JavaScript
│   └── css/          # Arquivos de estilo
└── requirements.txt  # Dependências do projeto
```

## Dependências

- **pandas**: Manipulação e análise de dados
- **openpyxl**: Leitura e escrita de arquivos Excel
- **playwright**: Automação de navegador para scraping
- **fastapi**: Framework para API REST
- **uvicorn**: Servidor ASGI

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

(Documentação de uso será adicionada conforme o projeto se desenvolve)

## Licença

MIT
