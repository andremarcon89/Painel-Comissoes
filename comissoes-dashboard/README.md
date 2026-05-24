# Comissões Dashboard

Dashboard interativo para visualização do acervo das Comissões da Câmara Municipal de São Paulo.

Este é um **site estático** que roda no GitHub Pages ou em qualquer servidor web, sem necessidade de backend.

## 🌐 Acesso Online

Abra o dashboard no GitHub Pages: [seu-usuario.github.io/Painel-Comissoes](https://seu-usuario.github.io/Painel-Comissoes)

## ✨ Funcionalidades

- 📊 Dashboard interativo com gráficos donut
- 🔍 Seletor de comissão com dados em tempo real
- 📈 Indicadores: Total, Data de atualização, Distribuição por tipo
- 🗂️ Modal com tabela paginada (20 registros/página)
- 📥 Exportação de dados em Excel (.xlsx)
- 📱 Design responsivo e profissional
- 🎨 Cores institucionais da Câmara Municipal de SP

## 📁 Estrutura do Projeto

```
comissoes-dashboard/
├── dashboard/
│   ├── index.html          # Dashboard estático
│   ├── data/
│   │   └── FIN.json        # Dados das comissões
│   ├── js/                 # Assets JavaScript futuros
│   └── css/                # Assets CSS futuros
├── data/
│   ├── raw/                # CSVs originais
│   └── processed/          # JSONs processados
├── scripts/                # Scripts Python (uso local)
└── README.md
```

## 🚀 Como Usar

### Online (GitHub Pages)
Abra em seu navegador:
```
https://seu-usuario.github.io/Painel-Comissoes/dashboard/
```

### Localmente
1. Clone o repositório
2. Abra `dashboard/index.html` em seu navegador
3. Selecione uma comissão no dropdown

## 🔧 Para Atualizar os Dados

Se tiver acesso aos CSVs brutos:

1. Instale dependências Python:
   ```bash
   pip install pandas openpyxl
   ```

2. Processe o CSV:
   ```bash
   python scripts/process_data.py data/raw/FIN.csv FIN
   ```

3. Copie o JSON gerado para o dashboard:
   ```bash
   cp data/processed/FIN.json dashboard/data/FIN.json
   ```

4. Faça commit e push para GitHub

## 📊 Tecnologias

- **Frontend**: HTML5, CSS3, JavaScript puro (sem frameworks)
- **Gráficos**: Chart.js (via CDN)
- **Exportação**: SheetJS (via CDN)
- **Dados**: JSON estático
- **Hosting**: GitHub Pages

## 📝 Formato dos Dados

Os arquivos JSON em `dashboard/data/` seguem este formato:

```json
{
  "comissao": "FIN",
  "ultima_atualizacao": "2026-05-24T10:00:00",
  "total": 329,
  "por_relator": { "Ver. KEIT LIMA (PSOL)": 58, ... },
  "por_estado": { "Estudo para manifestação": 115, ... },
  "registros": [ { "Processo": "PL 299/2026", ... }, ... ]
}
```

## 📄 Licença

MIT

## 🔗 Referência

Dados originários de: https://splegisconsulta.saopaulo.sp.leg.br
