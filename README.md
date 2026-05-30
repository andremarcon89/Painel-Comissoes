# Painel de Comissões — Relatórios de Tramitação

Dashboard Interativo para monitoramento do Acervo de Projetos em Análise nas Comissões Permanentes da Câmara Municipal de São Paulo.

---

## Estrutura do projeto

```
Painel-Comissoes/
├── download_relatorios.py     # Passo 1: acessa o SPLegis e baixa os CSVs brutos
├── tratar_relatorios.py       # Passo 2: trata os CSVs e gera o Excel consolidado
├── rodar_tudo.py              # Script principal (executa os dois passos)
├── inspecionar_pagina.py      # Utilitário de diagnóstico da página web
├── relatorios_brutos/         # CSVs baixados diretamente do sistema (gerado automaticamente)
└── relatorios_tratados/       # CSVs tratados + Excel consolidado (gerado automaticamente)
```

---

## Pré-requisitos

Python 3.9+ e as seguintes bibliotecas:

```bash
pip install playwright pandas openpyxl
playwright install chromium
```

---

## Como usar

### Opção 1 — Executar tudo de uma vez

```bash
python3 rodar_tudo.py
```

Executa o **Passo 1** (download) seguido do **Passo 2** (tratamento).

### Opção 2 — Só tratar CSVs já baixados

Se você já tem os arquivos brutos em `relatorios_brutos/`:

```bash
python3 rodar_tudo.py --so-tratar
```

### Opção 3 — Diagnóstico da página

Para inspecionar os elementos da página antes de rodar a automação:

```bash
python3 rodar_tudo.py --inspecionar
```

---

## Passo 1 — Download (`download_relatorios.py`)

Para cada uma das 7 comissões (**ADM, CCJ, ECON, EDUC, FIN, SAUDE, URB**):

1. Acessa: `https://splegisconsulta.saopaulo.sp.leg.br/Relatorio/IndexComissaoProjetoTramitacaoInterna`
2. Seleciona a comissão no campo correspondente
3. Marca os tipos de matéria: **PDL, PL, PLO, PR**
4. Clica em "Pesquisar"
5. Exporta o resultado em CSV

**Saída:** `relatorios_brutos/acervo_<COMISSAO>.csv`

---

## Passo 2 — Tratamento (`tratar_relatorios.py`)

Lê cada CSV bruto e realiza a segmentação das colunas compostas:

| Coluna original      | Colunas geradas                                                                                      |
|----------------------|------------------------------------------------------------------------------------------------------|
| `Tramitação`         | `Data Tramitação` \| `Local de Tramitação`                                                           |
| `Tramitação Interna` | `Data da Tramitação Interna` \| `Local de Tramitação Interna` \| `Motivo Tramitação Interna`         |

**Saídas:**
- `relatorios_tratados/acervo_<COMISSAO>_tratado.csv` — um arquivo por comissão
- `relatorios_tratados/acervo_comissoes_tratado.xlsx` — pasta de trabalho Excel com **7 abas** (uma por comissão), cabeçalhos formatados e colunas auto-dimensionadas

---

## Comissões cobertas

| Sigla | Comissão                                                    |
|-------|-------------------------------------------------------------|
| ADM   | Administração Pública                                       |
| CCJ   | Constituição, Justiça e Legislação Participativa            |
| ECON  | Economia e Administração                                    |
| EDUC  | Educação, Cultura e Esportes                                |
| FIN   | Finanças e Orçamento                                        |
| SAUDE | Saúde, Promoção Social e Trabalho                           |
| URB   | Política Urbana, Metropolitana e Meio Ambiente              |

---

## Tipos de matéria

| Sigla | Tipo                           |
|-------|--------------------------------|
| PDL   | Projeto de Decreto Legislativo |
| PL    | Projeto de Lei                 |
| PLO   | Projeto de Lei Orgânica        |
| PR    | Projeto de Resolução           |
