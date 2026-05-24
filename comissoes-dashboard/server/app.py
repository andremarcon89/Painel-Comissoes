import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Caminhos
BASE_DIR = Path(__file__).parent.parent
DASHBOARD_DIR = BASE_DIR / 'dashboard'
DATA_DIR = BASE_DIR / 'data' / 'processed'

# Criar aplicação FastAPI
app = FastAPI(
    title='Dashboard Comissões',
    description='API para dados das Comissões da Câmara Municipal de São Paulo',
    version='1.0.0'
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Rotas da API
@app.get('/api/dados/{comissao}')
def get_comissao_data(comissao: str):
    """Retorna os dados processados de uma comissão específica."""
    comissao = comissao.upper()
    json_path = DATA_DIR / f'{comissao}.json'

    if not json_path.exists():
        logger.warning(f"Arquivo não encontrado: {json_path}")
        raise HTTPException(
            status_code=404,
            detail=f'Dados da comissão "{comissao}" não encontrados'
        )

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Dados de {comissao} retornados com sucesso")
        return data
    except Exception as e:
        logger.error(f"Erro ao ler arquivo de {comissao}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f'Erro ao processar dados de "{comissao}"'
        )


@app.get('/api/dados/all')
def get_all_data():
    """Retorna dados consolidados de todas as comissões."""
    json_path = DATA_DIR / 'all_comissoes.json'

    if not json_path.exists():
        logger.warning(f"Arquivo consolidado não encontrado: {json_path}")
        raise HTTPException(
            status_code=404,
            detail='Dados consolidados não encontrados. Execute o pipeline antes.'
        )

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("Dados consolidados retornados com sucesso")
        return data
    except Exception as e:
        logger.error(f"Erro ao ler arquivo consolidado: {e}")
        raise HTTPException(
            status_code=500,
            detail='Erro ao processar dados consolidados'
        )


@app.get('/api/status')
def get_status():
    """Retorna o status da última execução do pipeline."""
    json_path = DATA_DIR / 'status.json'

    if not json_path.exists():
        logger.warning(f"Arquivo de status não encontrado: {json_path}")
        raise HTTPException(
            status_code=404,
            detail='Status do pipeline não encontrado. Execute o pipeline primeiro.'
        )

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("Status retornado com sucesso")
        return data
    except Exception as e:
        logger.error(f"Erro ao ler arquivo de status: {e}")
        raise HTTPException(
            status_code=500,
            detail='Erro ao processar status'
        )


@app.get('/health')
def health_check():
    """Verificação de saúde da aplicação."""
    return {
        'status': 'ok',
        'service': 'Dashboard Comissões',
        'version': '1.0.0'
    }


# Servir arquivos estáticos do dashboard
if DASHBOARD_DIR.exists():
    app.mount('/', StaticFiles(directory=DASHBOARD_DIR, html=True), name='dashboard')
    logger.info(f"Dashboard montado em / ({DASHBOARD_DIR})")
else:
    logger.warning(f"Diretório do dashboard não encontrado: {DASHBOARD_DIR}")


# Evento de inicialização
@app.on_event('startup')
async def startup_event():
    logger.info("=" * 60)
    logger.info("Dashboard Comissões iniciado com sucesso")
    logger.info("=" * 60)
    logger.info(f"Documentação disponível em: http://localhost:8000/docs")
    logger.info(f"Base de dados: {BASE_DIR}")
    logger.info("=" * 60)


# Evento de encerramento
@app.on_event('shutdown')
async def shutdown_event():
    logger.info("Dashboard Comissões encerrado")


if __name__ == '__main__':
    import uvicorn

    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(
        'app:app',
        host='0.0.0.0',
        port=8000,
        reload=False,
        log_level='info'
    )
