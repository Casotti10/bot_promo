import asyncio
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# 1. Configurar o driver do Selenium
def configure_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # DESATIVADO: Mercado Livre bloqueia headless
    # chrome_options.add_argument("--window-size=1920,1080")

    # Estabilidade no Windows
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-allow-origins=*")
    chrome_options.add_argument("--start-maximized")

    # Anti-detecção: remove o aviso de automação do Chrome
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)

    # Injeta o disfarce em todas as páginas que forem abertas
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        },
    )

    return driver

# 2. Função que realiza a coleta das promoções do Mercado Livre
def coletar_promocoes():
    driver = configure_driver()
    promocoes_novas = []

    try:
        url = "https://www.mercadolivre.com.br/ofertas"
        driver.get(url)

        # Aguarda 5 segundos para a página e as imagens carregarem
        time.sleep(5)

        # Busca todos os cartões de produtos da página
        produtos = driver.find_elements(
            By.CSS_SELECTOR, ".poly-card, li.promotion-item"
        )
        print(f"Quantidade de produtos encontrados: {len(produtos)}")

        for produto in produtos:
            try:
                percent_text = produto.find_element(By.CSS_SELECTOR, "span.poly-price__discount-polylabel").text
                percent_value = int(percent_text.replace("%", "").replace("OFF", "").strip())

                if percent_value > 50:
                    nome = produto.find_element(By.CSS_SELECTOR, "a.poly-component__title").text
                    valor_antigo = produto.find_element(By.CSS_SELECTOR, "s.andes-money-amount--previous").find_element(By.CSS_SELECTOR, "span.andes-money-amount__fraction").text
                    valor_novo = produto.find_element(By.CSS_SELECTOR, "span.andes-money-amount:not(.andes-money-amount--previous)").find_element(By.CSS_SELECTOR, "span.andes-money-amount__fraction").text
                    link = produto.find_element(By.CSS_SELECTOR, "a.poly-component__title").get_attribute("href")
                    
                    img_elem = produto.find_element(By.CSS_SELECTOR, "img.poly-component__picture, img")
                    imagem_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")

                    promocoes_novas.append(
                        {
                            "nome": nome,
                            "antigo": f"R$ {valor_antigo}",
                            "novo": f"R$ {valor_novo}",
                            "porcentagem": percent_value,
                            "link": link,
                            "imagem_url": imagem_url,
                        }
                    )

            except:
                continue

        print(promocoes_novas)

    except Exception as e:
        print(f"Erro geral: {e}")

    finally:
        # Garante que o navegador seja sempre fechado ao final
        driver.quit()

    return promocoes_novas


# Executa a função e armazena o resultado
if __name__ == "__main__":
    resultado = coletar_promocoes()