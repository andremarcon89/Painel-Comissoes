import subprocess
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orquestra todo o pipeline de atualização de dados."""

    def __init__(self):
        self.start_time = datetime.now()
        self.comissoes_processadas = {}
        self.comissoes_falhadas = {}
        self.raw_dir = Path('data/raw')
        self.processed_dir = Path('data/processed')
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def run_download_reports(self):
        """Executa o script de download de relatórios."""
        logger.info("=" * 70)
        logger.info("ETAPA 1: DOWNLOAD DE RELATÓRIOS")
        logger.info("=" * 70)

        try:
            logger.info("Executando download_reports.py...")
            result = subprocess.run(
                [sys.executable, 'scripts/download_reports.py'],
                cwd='.',
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos de timeout
            )

            if result.returncode == 0:
                logger.info("Download de relatórios concluído com sucesso")
                logger.debug(f"Output: {result.stdout}")
                return True
            else:
                logger.warning(f"Download retornou código de erro {result.returncode}")
                logger.warning(f"Stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout ao executar download_reports.py")
            return False
        except FileNotFoundError:
            logger.error("Arquivo download_reports.py não encontrado")
            return False
        except Exception as e:
            logger.error(f"Erro ao executar download_reports.py: {e}")
            return False

    def process_raw_files(self):
        """Processa cada arquivo CSV baixado em data/raw/."""
        logger.info("\n" + "=" * 70)
        logger.info("ETAPA 2: PROCESSAMENTO DE ARQUIVOS CSV")
        logger.info("=" * 70)

        if not self.raw_dir.exists():
            logger.warning(f"Diretório {self.raw_dir} não encontrado")
            return

        csv_files = sorted(self.raw_dir.glob('*.csv'))

        if not csv_files:
            logger.warning("Nenhum arquivo CSV encontrado em data/raw/")
            return

        logger.info(f"Encontrados {len(csv_files)} arquivo(s) CSV para processar")

        for csv_path in csv_files:
            sigla = csv_path.stem  # Nome sem extensão
            logger.info(f"\nProcessando: {csv_path.name}")

            try:
                result = subprocess.run(
                    [sys.executable, 'scripts/process_data.py', str(csv_path), sigla],
                    cwd='.',
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minutos de timeout por comissão
                )

                if result.returncode == 0:
                    logger.info(f"✓ Comissão {sigla} processada com sucesso")
                    self.comissoes_processadas[sigla] = {
                        'status': 'sucesso',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    logger.error(f"✗ Falha ao processar comissão {sigla}")
                    logger.debug(f"Stderr: {result.stderr}")
                    self.comissoes_falhadas[sigla] = {
                        'erro': 'Processamento falhou',
                        'timestamp': datetime.now().isoformat()
                    }

            except subprocess.TimeoutExpired:
                logger.error(f"✗ Timeout ao processar {sigla}")
                self.comissoes_falhadas[sigla] = {
                    'erro': 'Timeout no processamento',
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"✗ Erro ao processar {sigla}: {e}")
                self.comissoes_falhadas[sigla] = {
                    'erro': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def consolidate_json_files(self):
        """Consolida todos os JSONs processados em um arquivo único."""
        logger.info("\n" + "=" * 70)
        logger.info("ETAPA 3: CONSOLIDAÇÃO DE DADOS JSON")
        logger.info("=" * 70)

        consolidated = {
            'ultima_atualizacao': datetime.now().isoformat(),
            'comissoes': {}
        }

        json_files = sorted(self.processed_dir.glob('*.json'))
        json_files = [f for f in json_files if f.name != 'all_comissoes.json' and f.name != 'status.json']

        logger.info(f"Consolidando {len(json_files)} arquivo(s) JSON")

        for json_path in json_files:
            sigla = json_path.stem
            logger.info(f"Lendo: {json_path.name}")

            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    consolidated['comissoes'][sigla] = data
                    logger.debug(f"✓ {sigla} consolidado")

            except Exception as e:
                logger.error(f"✗ Erro ao ler {json_path}: {e}")

        # Salvar arquivo consolidado
        output_path = self.processed_dir / 'all_comissoes.json'

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Arquivo consolidado salvo: {output_path}")
            logger.info(f"  Total de comissões consolidadas: {len(consolidated['comissoes'])}")

        except Exception as e:
            logger.error(f"✗ Erro ao salvar consolidado: {e}")

    def generate_status_file(self):
        """Gera arquivo status.json com informações da execução."""
        logger.info("\n" + "=" * 70)
        logger.info("ETAPA 4: GERAÇÃO DO ARQUIVO DE STATUS")
        logger.info("=" * 70)

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        status = {
            'timestamp': end_time.isoformat(),
            'duracao_segundos': duration,
            'total_comissoes': len(self.comissoes_processadas) + len(self.comissoes_falhadas),
            'comissoes_atualizadas': len(self.comissoes_processadas),
            'comissoes_falhadas': len(self.comissoes_falhadas),
            'detalhes': {
                'sucesso': self.comissoes_processadas,
                'erro': self.comissoes_falhadas
            }
        }

        output_path = self.processed_dir / 'status.json'

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Arquivo de status salvo: {output_path}")

        except Exception as e:
            logger.error(f"✗ Erro ao salvar status: {e}")

        return status

    def print_summary(self, status):
        """Imprime resumo final da execução."""
        logger.info("\n" + "=" * 70)
        logger.info("RESUMO FINAL DO PIPELINE")
        logger.info("=" * 70)

        logger.info(f"Data/Hora de conclusão: {status['timestamp']}")
        logger.info(f"Duração total: {status['duracao_segundos']:.2f} segundos")
        logger.info("")
        logger.info(f"Total de comissões: {status['total_comissoes']}")
        logger.info(f"✓ Atualizadas com sucesso: {status['comissoes_atualizadas']}")
        logger.info(f"✗ Falhadas: {status['comissoes_falhadas']}")

        if self.comissoes_processadas:
            logger.info("\nComissões processadas com sucesso:")
            for sigla in sorted(self.comissoes_processadas.keys()):
                logger.info(f"  ✓ {sigla}")

        if self.comissoes_falhadas:
            logger.info("\nComissões que falharam:")
            for sigla, info in sorted(self.comissoes_falhadas.items()):
                logger.info(f"  ✗ {sigla}: {info.get('erro', 'Erro desconhecido')}")

        logger.info("=" * 70)
        logger.info("Pipeline concluído!")
        logger.info("=" * 70)

    def run(self):
        """Executa o pipeline completo."""
        try:
            logger.info("Iniciando pipeline de atualização de dados")
            logger.info(f"Timestamp: {self.start_time.isoformat()}")

            # Etapa 1: Download
            if not self.run_download_reports():
                logger.warning("Download falhou, mas continuando com arquivos existentes...")

            # Etapa 2: Processamento
            self.process_raw_files()

            # Etapa 3: Consolidação
            self.consolidate_json_files()

            # Etapa 4: Status
            status = self.generate_status_file()

            # Resumo final
            self.print_summary(status)

            # Retornar código de sucesso se pelo menos uma comissão foi processada
            return len(self.comissoes_processadas) > 0

        except Exception as e:
            logger.error(f"Erro fatal no pipeline: {e}")
            return False


def main():
    """Função principal."""
    orchestrator = PipelineOrchestrator()
    sucesso = orchestrator.run()
    sys.exit(0 if sucesso else 1)


if __name__ == '__main__':
    main()
