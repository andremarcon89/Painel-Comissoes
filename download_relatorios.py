"""
PASSO 1: Download dos relatórios brutos de tramitação das 7 Comissões.

Acessa a página do SPLegis Consulta, seleciona cada comissão + tipos de matéria
(PDL, PL, PLO, PR) e exporta o CSV resultante para a pasta relatorios_brutos/.

Dependências:
  pip install playwright
  playwright install chromium
"""

import os
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://splegisconsulta.saopaulo.sp.leg.br/Relatorio/IndexComissaoProjetoTramitacaoInterna"
COMISSOES = ["ADM", "CCJ", "ECON", "EDUC", "FIN", "SAUDE", "URB"]
TIPOS = ["PDL", "PL", "PLO", "PR"]
DOWNLOAD_DIR = Path(__file__).parent / "relatorios_brutos"


def aguardar_download(page, context, timeout_ms=60_000):
    """Aguarda e retorna o caminho do arquivo baixado."""
    with page.expect_download(timeout=timeout_ms) as dl_info:
        yield
    download = dl_info.value
    download.save_as(DOWNLOAD_DIR / download.suggested_filename)
    return DOWNLOAD_DIR / download.suggested_filename


def desmarcar_todos(page):
    cbs = page.query_selector_all("input[type=checkbox]")
    for cb in cbs:
        if cb.is_checked():
            cb.uncheck()


def marcar_tipo(page, tipo):
    """Marca checkbox pelo texto do label ou pelo value."""
    # Tenta label com texto exato
    label = page.query_selector(f"label:has-text('{tipo}')")
    if label:
        for_id = label.get_attribute("for")
        if for_id:
            page.check(f"#{for_id}")
            return
        cb = label.query_selector("input[type=checkbox]")
        if cb:
            cb.check()
            return
    # Fallback: value
    cb = page.query_selector(f"input[type=checkbox][value='{tipo}']")
    if cb:
        cb.check()
        return
    # Fallback: id ou name contendo o tipo
    cb = page.query_selector(f"input[type=checkbox][id*='{tipo}'], input[type=checkbox][name*='{tipo}']")
    if cb:
        cb.check()
        return
    print(f"  AVISO: checkbox '{tipo}' não encontrado")


def clicar_pesquisar(page):
    candidatos = [
        "button:has-text('Pesquisar')",
        "button:has-text('Consultar')",
        "button:has-text('Buscar')",
        "button:has-text('Filtrar')",
        "input[type=submit]",
        "button[type=submit]",
    ]
    for seletor in candidatos:
        el = page.query_selector(seletor)
        if el and el.is_visible():
            el.click()
            return
    raise RuntimeError("Botão de pesquisa não encontrado")


def clicar_exportar_csv(page):
    candidatos = [
        "a:has-text('CSV')",
        "button:has-text('CSV')",
        "a:has-text('Exportar')",
        "button:has-text('Exportar')",
        "a[href*='csv']",
        "a[href*='export']",
        "a[title*='CSV']",
        "button[title*='CSV']",
        "input[type=button][value*='CSV']",
        "input[type=button][value*='Exportar']",
    ]
    for seletor in candidatos:
        el = page.query_selector(seletor)
        if el and el.is_visible():
            return el
    # Busca qualquer elemento com texto/atributo relevante
    for el in page.query_selector_all("a, button, input[type=button]"):
        texto = (el.inner_text() or el.get_attribute("value") or el.get_attribute("title") or "").upper()
        href = el.get_attribute("href") or ""
        if any(p in texto or p in href.upper() for p in ["CSV", "EXPORT", "BAIXAR", "DOWNLOAD"]):
            return el
    raise RuntimeError("Botão de exportação CSV não encontrado")


def baixar_comissao(page, context, comissao):
    print(f"\n>>> Processando: {comissao}")
    page.goto(URL, wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(2_000)

    # --- Seleciona a comissão ---
    selects = page.query_selector_all("select")
    sel_comissao = None
    for s in selects:
        opcoes = [o.inner_text().strip() for o in s.query_selector_all("option")]
        if comissao in opcoes:
            sel_comissao = s
            break
    if sel_comissao is None:
        raise RuntimeError(f"Select de comissão não encontrado. Opções disponíveis: {[o.inner_text().strip() for s in selects for o in s.query_selector_all('option')]}")

    sel_comissao.select_option(label=comissao)
    page.wait_for_timeout(1_000)

    # --- Tipos de matéria ---
    desmarcar_todos(page)
    for tipo in TIPOS:
        marcar_tipo(page, tipo)
        print(f"  ✓ Tipo: {tipo}")

    page.wait_for_timeout(500)

    # --- Pesquisar ---
    clicar_pesquisar(page)
    print("  Pesquisando...")
    page.wait_for_timeout(3_000)
    try:
        page.wait_for_selector("table, .grid, .result, [class*='table']", timeout=15_000)
    except PWTimeout:
        print("  AVISO: tabela de resultados não detectada, tentando exportar mesmo assim")

    # --- Exportar CSV ---
    btn_export = clicar_exportar_csv(page)
    print("  Exportando CSV...")

    with page.expect_download(timeout=60_000) as dl_info:
        btn_export.click()

    download = dl_info.value
    destino = DOWNLOAD_DIR / f"acervo_{comissao}.csv"
    download.save_as(str(destino))
    print(f"  Salvo: {destino.name}")
    return destino


def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    baixados = []
    erros = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Diagnóstico inicial
        print(f"Acessando: {URL}")
        page.goto(URL, wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(2_000)
        print(f"Título: {page.title()}")

        selects = page.query_selector_all("select")
        print(f"Selects encontrados: {len(selects)}")
        for s in selects:
            opts = [o.inner_text().strip() for o in s.query_selector_all("option")]
            print(f"  id={s.get_attribute('id')} -> {opts}")

        cbs = page.query_selector_all("input[type=checkbox]")
        print(f"Checkboxes: {len(cbs)}")
        for cb in cbs:
            lbl = ""
            cid = cb.get_attribute("id")
            if cid:
                lbl_el = page.query_selector(f"label[for='{cid}']")
                if lbl_el:
                    lbl = lbl_el.inner_text().strip()
            print(f"  id={cid} value={cb.get_attribute('value')} label='{lbl}'")

        for comissao in COMISSOES:
            try:
                arq = baixar_comissao(page, context, comissao)
                baixados.append(arq)
            except Exception as e:
                print(f"  ERRO [{comissao}]: {e}")
                erros.append((comissao, str(e)))
                # Salva screenshot para diagnóstico
                page.screenshot(path=f"erro_{comissao}.png")

        context.close()
        browser.close()

    print(f"\n{'='*50}")
    print(f"RESUMO PASSO 1")
    print(f"{'='*50}")
    print(f"Baixados: {len(baixados)}")
    for a in baixados:
        print(f"  {a.name}")
    if erros:
        print(f"Erros: {len(erros)}")
        for c, e in erros:
            print(f"  {c}: {e}")


if __name__ == "__main__":
    main()
