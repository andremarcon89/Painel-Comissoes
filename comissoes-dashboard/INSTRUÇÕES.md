# 🚀 Instruções de Uso - Dashboard Comissões

## 📦 Instalação

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Instalar navegador Playwright (necessário para download):**
```bash
playwright install chromium
```

## 🎯 Uso Rápido

### Opção 1: Apenas Dashboard (com dados existentes)
```bash
cd comissoes-dashboard
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```
Acesse em: `http://localhost:8000`

### Opção 2: Pipeline Completo (download + processamento + consolidação)
```bash
cd comissoes-dashboard
python scripts/run_pipeline.py
```

### Opção 3: Testar uma comissão específica
```bash
cd comissoes-dashboard
python scripts/download_reports.py --comissao FIN
python scripts/process_data.py data/raw/FIN.csv FIN
```

---

## 📋 Scripts Disponíveis

### 1️⃣ `scripts/download_reports.py` - Download de Relatórios
Baixa CSVs da página oficial de comissões usando Playwright.

**Uso:**
```bash
# Baixar todas as 7 comissões
python scripts/download_reports.py

# Baixar apenas uma comissão (útil para testes)
python scripts/download_reports.py --comissao FIN
python scripts/download_reports.py FIN
```

**Saída:**
- `data/raw/CCJ.csv`
- `data/raw/FIN.csv`
- `data/raw/URB.csv`
- `data/raw/ADM.csv`
- `data/raw/ECON.csv`
- `data/raw/EDUC.csv`
- `data/raw/SAUDE.csv`

---

### 2️⃣ `scripts/process_data.py` - Processamento de Dados
Transforma CSV bruto em JSON estruturado com cálculos e análises.

**Uso:**
```bash
# Processar arquivo específico
python scripts/process_data.py data/raw/FIN.csv FIN
```

**Transformações realizadas:**
- Detecção automática de separador
- Extração de Tipo, Número, Ano do Processo
- Fragmentação de campos compostos (Tramitação, Tramitação Interna)
- Preenchimento de valores nulos (Relator)
- Reordenação e limpeza de colunas
- Geração de estatísticas (por relator, por estado)

**Saída:**
- `data/processed/FIN.json` (estrutura completa com registros)
- `data/processed/FIN_tratado.csv` (CSV limpo)

---

### 3️⃣ `scripts/run_pipeline.py` - Orquestrador
Coordena todo o pipeline em uma única execução.

**Uso:**
```bash
python scripts/run_pipeline.py
```

**Etapas:**
1. Download de relatórios
2. Processamento de cada CSV
3. Consolidação em `all_comissoes.json`
4. Geração de `status.json`
5. Relatório final

**Saída:**
- `data/processed/all_comissoes.json` (consolidado)
- `data/processed/status.json` (histórico de execução)
- `pipeline.log` (logs detalhados)

---

### 4️⃣ `scripts/validate_pipeline.py` - Validação Automatizada
Testa se o pipeline está funcionando corretamente.

**Uso:**
```bash
python scripts/validate_pipeline.py
```

**Verifica:**
- ✓ Importação de módulos
- ✓ Estrutura do JSON
- ✓ Campos obrigatórios
- ✓ Remoção de colunas compostas
- ✓ Criação de novas colunas
- ✓ Qualidade dos dados

---

## 🌐 Dashboard Web

### Acessar
```bash
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```
Abrir em navegador: `http://localhost:8000`

### Funcionalidades
- **Seletor de Comissão:** Escolha entre 7 comissões
- **Indicadores:** Total, data, distribuição por tipo
- **Gráficos:** Por Relator e Por Estado (clicáveis)
- **Modal de Detalhes:** Tabela paginada com filtros
- **Exportação:**
  - 📥 Relatório completo da comissão
  - 📥 Relatório de lista filtrada
  - 📥 Relatório consolidado de todas as comissões

### APIs Disponíveis
```
GET /api/dados/{SIGLA}      → Dados de uma comissão
GET /api/dados/all          → Dados consolidados
GET /api/status             → Status da última execução
GET /health                 → Verificação de saúde
```

---

## ⏰ Agendamento Automático (Cron)

### Configurar execução 3x por dia
```bash
chmod +x cron_setup.sh
./cron_setup.sh
```

**Horários (Brasília):**
- 06:00 (manhã)
- 15:00 (tarde)
- 20:00 (noite)

**Arquivo de logs:**
- `logs/pipeline.log` (contém toda a execução)

---

## 📊 Estrutura de Dados

### JSON de Entrada (CSV original)
```
Processo,Ementa,Autor,Relator,Tramitação,Tramitacao Interna,Dias na Comissão,Dias no Estado Atual
PL 299/2026,Texto,...,Ver.X,16/04/2026 21:40:00 - FIN (Recebido),20/05/2026 02:46 - Secretaria / Aguardando,37,3
```

### JSON de Saída (processado)
```json
{
  "comissao": "FIN",
  "ultima_atualizacao": "2026-05-24T10:00:00",
  "total": 329,
  "por_relator": {
    "Ver. KEIT LIMA (PSOL)": 58,
    ...
  },
  "por_estado": {
    "Estudo para manifestação do relator": 115,
    ...
  },
  "registros": [
    {
      "Processo": "PL 299/2026",
      "Tipo": "PL",
      "Numero": "299",
      "Ano": "2026",
      "Ementa": "Autoriza a concessão...",
      "Autor": "Ver. JOSÉ...",
      "Relator": "Ver. KEIT LIMA (PSOL)",
      "Data_Tramitação": "16/04/2026 21:40:00",
      "Local_Tramitação": "FIN",
      "Origem_Tramitação": "Recebido de SGP22",
      "Data_TI": "20/05/2026 02:46",
      "Local_TI": "Secretaria (SGP12)",
      "Estado": "Aguardando Notas Taquigráficas",
      "Dias na Comissão": 37,
      "Dias no Estado Atual": 3
    }
  ]
}
```

---

## 🔍 Solução de Problemas

### Problema: "ModuleNotFoundError: pandas"
**Solução:**
```bash
pip install -r requirements.txt
```

### Problema: Playwright não encontra navegador
**Solução:**
```bash
pip install playwright
playwright install chromium
```

### Problema: Porta 8000 já em uso
**Solução:**
```bash
python -m uvicorn server.app:app --port 8001
```

### Problema: Download falha
**Solução:**
- Verificar conexão com a internet
- Tentar com `--comissao FIN` (teste individual)
- Verificar logs em `pipeline.log`

---

## 📝 Logs

### Arquivo: `pipeline.log`
Contém toda a execução do pipeline:
```
2026-05-24 10:00:00 - INFO - Iniciando download de relatórios
2026-05-24 10:05:00 - INFO - ✓ Comissão FIN processada com sucesso
...
```

### Ver logs em tempo real
```bash
tail -f pipeline.log
```

---

## 🧪 Validação

### Testar pipeline completo
```bash
python scripts/validate_pipeline.py
```

**Resultado esperado:**
```
✓ PASS CSV de teste existe
✓ PASS Módulo process_data.py importável
✓ PASS Processamento dos dados de teste
...
Resultados: 21 PASS / 0 FAIL
```

---

## 📚 Tecnologias Utilizadas

- **Backend:** FastAPI, Uvicorn
- **Processamento:** Pandas, openpyxl
- **Web Scraping:** Playwright
- **Frontend:** HTML5, CSS3, JavaScript puro
- **Gráficos:** Chart.js (CDN)
- **Exportação:** SheetJS (XLSX)

---

## 📧 Contato

Desenvolvido para a Câmara Municipal de São Paulo
- Site: https://splegisconsulta.saopaulo.sp.leg.br
- Dashboard: http://localhost:8000

---

## ✅ Checklist de Implantação

- [ ] Instalar dependências (`pip install -r requirements.txt`)
- [ ] Instalar Playwright (`playwright install chromium`)
- [ ] Testar validação (`python scripts/validate_pipeline.py`)
- [ ] Executar pipeline (`python scripts/run_pipeline.py`)
- [ ] Iniciar servidor (`uvicorn server.app:app --host 0.0.0.0 --port 8000`)
- [ ] Acessar dashboard (http://localhost:8000)
- [ ] Configurar cron (opcional) (`./cron_setup.sh`)

---

**Última atualização:** 2026-05-24
**Versão:** 1.0.0
