import asyncio
import logging
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mapeamento de comissões: nome_exibicao -> sigla_arquivo
COMISSOES = {
    'Constituição, Justiça e Legislação Participativa': 'CCJ',
    'Finanças e Orçamento': 'FIN',
    'Política Urbana, Metropolitana e Meio Ambiente': 'URB',
    'Administração Pública': 'ADM',
    'Trânsito, Transporte e Atividade Econômica': 'ECON',
    'Educação, Cultura e Esportes': 'EDUC',
    'Saúde': 'SAUDE',
}

TIPOS_PROJETO = ['PDL', 'PL', 'PLO', 'PR']
BASE_URL = 'https://splegisconsulta.saopaulo.sp.leg.br/Relatorio/IndexComissaoProjetoTramitacaoInterna'
TIMEOUT_DOWNLOAD = 90000  # 90 segundos em ms


async def download_comissao(page, browser_context, nome_comissao, sigla):
    """Baixa o relatório CSV de uma comissão específica."""
    try:
        logger.info(f"Iniciando download da comissão: {nome_comissao} ({sigla})")

        # Navegar para a página
        logger.info(f"Acessando URL: {BASE_URL}")
        await page.goto(BASE_URL, wait_until='networkidle')
        await page.wait_for_timeout(1000)  # Pequeno delay para garantir carregamento

        # Localizar e selecionar a comissão
        logger.info(f"Selecionando comissão: {nome_comissao}")
        try:
            await page.select_option('select[name="comissao"]', nome_comissao)
            logger.info(f"Comissão {sigla} selecionada com sucesso")
        except Exception as e:
            logger.warning(f"Falha ao selecionar com nome 'comissao': {e}")
            # Tentar alternativas
            try:
                await page.select_option('select#Comissao', nome_comissao)
                logger.info(f"Comissão {sigla} selecionada com sucesso (alternativa #Comissao)")
            except Exception as e2:
                logger.error(f"Não foi possível selecionar a comissão: {e2}")
                return False

        await page.wait_for_timeout(500)

        # Localizar e marcar checkboxes de tipo de projeto
        logger.info(f"Marcando tipos de projeto: {', '.join(TIPOS_PROJETO)}")
        checkboxes_encontrados = 0

        for tipo in TIPOS_PROJETO:
            try:
                # Tentar com value attribute
                checkbox = page.locator(f'input[type="checkbox"][value="{tipo}"]')
                if await checkbox.count() > 0:
                    await checkbox.check()
                    checkboxes_encontrados += 1
                    logger.debug(f"Checkbox {tipo} marcado")
                else:
                    # Tentar com label contendo o texto
                    label = page.locator(f'label:has-text("{tipo}")')
                    if await label.count() > 0:
                        checkbox = label.locator('input[type="checkbox"]')
                        await checkbox.check()
                        checkboxes_encontrados += 1
                        logger.debug(f"Checkbox {tipo} marcado (via label)")
            except Exception as e:
                logger.warning(f"Erro ao marcar checkbox {tipo}: {e}")

        if checkboxes_encontrados == 0:
            logger.warning(f"Nenhum checkbox foi marcado para {sigla}")

        await page.wait_for_timeout(500)

        # Clicar no botão "Filtrar"
        logger.info(f"Clicando no botão Filtrar")
        try:
            await page.click('button:has-text("Filtrar")')
            logger.info(f"Botão Filtrar clicado")
        except Exception as e:
            logger.warning(f"Falha ao clicar em Filtrar: {e}")
            try:
                # Tentar alternativas
                await page.click('button[type="submit"]:has-text("Filtrar")')
                logger.info(f"Botão Filtrar clicado (alternativa submit)")
            except Exception as e2:
                logger.error(f"Não foi possível clicar em Filtrar: {e2}")
                return False

        # Aguardar carregamento da tabela
        logger.info(f"Aguardando carregamento da tabela")
        try:
            await page.wait_for_selector('table', timeout=30000)
            logger.info(f"Tabela carregada")
        except Exception as e:
            logger.warning(f"Timeout ao aguardar tabela: {e}")

        await page.wait_for_timeout(1000)  # Aguardar completamente

        # Aguardar e clicar no botão de download CSV
        logger.info(f"Procurando botão de download CSV")
        download_promise = browser_context.expect_download()

        try:
            # Tentar múltiplos seletores comuns para botão de download
            download_clicked = False

            # Opção 1: link com href CSV
            try:
                await page.click('a[href*=".csv"]')
                download_clicked = True
                logger.info(f"Download iniciado via link CSV")
            except:
                pass

            # Opção 2: botão com texto "CSV" ou "Download"
            if not download_clicked:
                try:
                    await page.click('button:has-text("CSV")')
                    download_clicked = True
                    logger.info(f"Download iniciado via botão CSV")
                except:
                    pass

            # Opção 3: botão com ícone de download
            if not download_clicked:
                try:
                    await page.click('[class*="download"]')
                    download_clicked = True
                    logger.info(f"Download iniciado via classe download")
                except:
                    pass

            # Opção 4: procurar por qualquer botão próximo à tabela
            if not download_clicked:
                try:
                    await page.click('button >> nth=0')
                    download_clicked = True
                    logger.info(f"Download iniciado via primeiro botão")
                except:
                    pass

            if not download_clicked:
                logger.error(f"Não foi possível localizar botão de download")
                return False

        except Exception as e:
            logger.error(f"Erro ao clicar em download: {e}")
            return False

        # Aguardar download com timeout
        logger.info(f"Aguardando conclusão do download (timeout: {TIMEOUT_DOWNLOAD}ms)")
        try:
            download = await asyncio.wait_for(
                download_promise,
                timeout=TIMEOUT_DOWNLOAD / 1000
            )

            # Salvar arquivo na pasta data/raw
            output_dir = Path('data/raw')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'{sigla}.csv'

            # Copiar arquivo baixado para o destino
            await download.save_as(output_path)
            logger.info(f"Arquivo salvo com sucesso: {output_path}")
            return True

        except asyncio.TimeoutError:
            logger.error(f"Timeout ao aguardar download de {sigla}")
            return False
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo de {sigla}: {e}")
            return False

    except Exception as e:
        logger.error(f"Erro ao processar comissão {sigla}: {e}")
        return False


async def main(comissao_filtro=None):
    """Função principal."""
    logger.info("Iniciando download de relatórios das comissões")

    resultados = {}
    comissoes_para_processar = COMISSOES.items()

    # Filtrar comissão se especificado
    if comissao_filtro:
        comissoes_para_processar = [
            (nome, sigla) for nome, sigla in COMISSOES.items()
            if sigla.upper() == comissao_filtro.upper()
        ]
        if not comissoes_para_processar:
            logger.error(f"Comissão '{comissao_filtro}' não encontrada")
            logger.info(f"Comissões disponíveis: {', '.join(COMISSOES.values())}")
            return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for nome_comissao, sigla in comissoes_para_processar:
            # Criar novo contexto com handling de download para cada comissão
            context = await browser.new_context(
                accept_downloads=True,
                extra_http_headers={'Accept-Language': 'pt-BR,pt;q=0.9'}
            )
            page = await context.new_page()

            try:
                sucesso = await download_comissao(page, context, nome_comissao, sigla)
                resultados[sigla] = 'OK' if sucesso else 'ERRO'
            except Exception as e:
                logger.error(f"Erro não tratado para {sigla}: {e}")
                resultados[sigla] = 'ERRO'
            finally:
                await context.close()

        await browser.close()

    # Relatório final
    logger.info("\n" + "=" * 60)
    logger.info("RELATÓRIO FINAL DE DOWNLOADS")
    logger.info("=" * 60)

    total = len(resultados)
    sucessos = sum(1 for v in resultados.values() if v == 'OK')
    erros = total - sucessos

    for sigla, status in sorted(resultados.items()):
        emoji = "✓" if status == "OK" else "✗"
        logger.info(f"{emoji} {sigla}: {status}")

    logger.info("=" * 60)
    logger.info(f"Total: {total} | Sucessos: {sucessos} | Erros: {erros}")
    logger.info("=" * 60 + "\n")

    return erros == 0


if __name__ == '__main__':
    comissao = None

    # Processar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == '--comissao' and len(sys.argv) > 2:
            comissao = sys.argv[2]
        elif sys.argv[1].startswith('--comissao='):
            comissao = sys.argv[1].split('=')[1]
        elif sys.argv[1] in COMISSOES.values():
            comissao = sys.argv[1]

    try:
        sucesso = asyncio.run(main(comissao))
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)
