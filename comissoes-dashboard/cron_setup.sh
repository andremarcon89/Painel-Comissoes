#!/bin/bash

# Script para configurar execução automática do pipeline via cron

set -e  # Sair em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}Configurador de Cron - Pipeline de Comissões${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Obter caminho do projeto
PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Validar se estamos no diretório correto
if [ ! -f "$PROJECT_PATH/scripts/run_pipeline.py" ]; then
    echo -e "${RED}✗ Erro: arquivo run_pipeline.py não encontrado em $PROJECT_PATH/scripts/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Projeto encontrado em: $PROJECT_PATH${NC}"
echo ""

# Criar pasta de logs se não existir
LOGS_DIR="$PROJECT_PATH/logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo "Criando diretório de logs..."
    mkdir -p "$LOGS_DIR"
    echo -e "${GREEN}✓ Diretório criado: $LOGS_DIR${NC}"
else
    echo -e "${GREEN}✓ Diretório de logs já existe: $LOGS_DIR${NC}"
fi

echo ""
echo "Configurando entradas no crontab..."
echo ""

# Definir o comando cron
# Executa o pipeline 3 vezes por dia:
# 06:00 (0 6) - 18:00 em UTC é 15:00 em Brasília (UTC-3)
# 15:00 (0 15) - 18:00 em UTC é 15:00 em Brasília (UTC-3)
# 20:00 (0 20) - 23:00 em UTC é 20:00 em Brasília (UTC-3)
# Ajustamento: Brasília está em UTC-3, então:
# - 06:00 BRT = 09:00 UTC → 0 9
# - 15:00 BRT = 18:00 UTC → 0 18
# - 20:00 BRT = 23:00 UTC → 0 23

CRON_ENTRY="0 9,18,23 * * * cd $PROJECT_PATH && python scripts/run_pipeline.py >> $LOGS_DIR/pipeline.log 2>&1"

# Salvar crontab atual
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Verificar se a entrada já existe
if grep -F "$PROJECT_PATH/scripts/run_pipeline.py" "$TEMP_CRON" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Aviso: Entrada do cron já existe para este projeto${NC}"
    echo "Removendo entrada anterior..."
    grep -v "$PROJECT_PATH/scripts/run_pipeline.py" "$TEMP_CRON" > "${TEMP_CRON}.new"
    mv "${TEMP_CRON}.new" "$TEMP_CRON"
fi

# Adicionar nova entrada
echo "$CRON_ENTRY" >> "$TEMP_CRON"

# Instalar novo crontab
crontab "$TEMP_CRON"
rm -f "$TEMP_CRON"

echo -e "${GREEN}✓ Cron configurado com sucesso!${NC}"
echo ""

echo -e "${BLUE}Detalhes da configuração:${NC}"
echo "  Horários (Brasília):"
echo "    • 06:00 (manhã)"
echo "    • 15:00 (tarde)"
echo "    • 20:00 (noite)"
echo ""
echo "  Comando: python scripts/run_pipeline.py"
echo "  Logs: $LOGS_DIR/pipeline.log"
echo "  Projeto: $PROJECT_PATH"
echo ""

echo -e "${BLUE}Próximas execuções agendadas:${NC}"
crontab -l | grep "run_pipeline.py" || echo "Nenhuma entrada encontrada"
echo ""

echo -e "${BLUE}Para remover a entrada de cron, execute:${NC}"
echo "  crontab -e"
echo "  # e delete a linha correspondente"
echo ""

echo -e "${GREEN}Configuração concluída!${NC}"
echo -e "${BLUE}===============================================${NC}"
