"""
Script de diagnóstico: inspeciona a estrutura HTML da página de relatório
para identificar os seletores corretos antes de rodar a automação completa.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

URL = "https://splegisconsulta.saopaulo.sp.leg.br/Relatorio/IndexComissaoProjetoTramitacaoInterna"


def criar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
    service = Service("/opt/node22/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


def main():
    driver = criar_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print(f"Acessando: {URL}")
        driver.get(URL)
        time.sleep(3)

        print(f"\nTítulo da página: {driver.title}")
        print(f"URL atual: {driver.current_url}")

        # Selects
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"\n=== SELECTS ({len(selects)}) ===")
        for i, s in enumerate(selects):
            sid = s.get_attribute("id")
            sname = s.get_attribute("name")
            opcoes = [o.text.strip() for o in s.find_elements(By.TAG_NAME, "option")]
            print(f"  [{i}] id='{sid}' name='{sname}'")
            print(f"       Opções: {opcoes}")

        # Checkboxes
        cbs = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        print(f"\n=== CHECKBOXES ({len(cbs)}) ===")
        for cb in cbs:
            cid = cb.get_attribute("id")
            cname = cb.get_attribute("name")
            cval = cb.get_attribute("value")
            # Tenta pegar o label associado
            label_text = ""
            try:
                label = driver.find_element(By.XPATH, f"//label[@for='{cid}']")
                label_text = label.text.strip()
            except Exception:
                pass
            print(f"  id='{cid}' name='{cname}' value='{cval}' label='{label_text}'")

        # Botões
        botoes = driver.find_elements(By.XPATH, "//button | //input[@type='submit'] | //input[@type='button']")
        print(f"\n=== BOTÕES ({len(botoes)}) ===")
        for b in botoes:
            print(f"  tag={b.tag_name} type='{b.get_attribute('type')}' text='{b.text.strip()}' value='{b.get_attribute('value')}' id='{b.get_attribute('id')}'")

        # Links de exportação
        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"\n=== LINKS RELEVANTES ===")
        for a in links:
            texto = a.text.strip()
            href = a.get_attribute("href") or ""
            if any(p in (texto + href).upper() for p in ["CSV", "EXPORT", "DOWNLOAD", "BAIXAR", "XLS"]):
                print(f"  text='{texto}' href='{href}' title='{a.get_attribute('title')}'")

        # Salva screenshot
        driver.save_screenshot("diagnostico_pagina.png")
        print(f"\nScreenshot salvo: diagnostico_pagina.png")

        # Salva HTML
        with open("diagnostico_pagina.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"HTML salvo: diagnostico_pagina.html")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
