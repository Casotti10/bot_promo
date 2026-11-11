from config import BOT_TOKEN, DISCORD_CHANNEL_ID

import asyncio
import os
import time

from urllib.parse import urlparse, urlunparse

import discord
from discord.ext import tasks

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By



links_enviados = set()  # Conjunto para armazenar links já enviados



# 1. Configurar o driver do Selenium
def configure_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
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

## 2. Função que realiza a coleta das promoções do Mercado Livre
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
                percent_text = produto.find_element(
                    By.CSS_SELECTOR,
                    "span.poly-price__discount-polylabel"
                ).text

                percent_value = int(
                    percent_text.replace("%", "")
                    .replace("OFF", "")
                    .strip()
                )

                if percent_value > 20:

                    nome = produto.find_element(
                        By.CSS_SELECTOR,
                        "a.poly-component__title"
                    ).text

                    valor_antigo = produto.find_element(
                        By.CSS_SELECTOR,
                        "s.andes-money-amount--previous"
                    ).find_element(
                        By.CSS_SELECTOR,
                        "span.andes-money-amount__fraction"
                    ).text

                    valor_novo = produto.find_element(
                        By.CSS_SELECTOR,
                        "span.andes-money-amount:not(.andes-money-amount--previous)"
                    ).find_element(
                        By.CSS_SELECTOR,
                        "span.andes-money-amount__fraction"
                    ).text

                    link = produto.find_element(
                        By.CSS_SELECTOR,
                        "a.poly-component__title"
                    ).get_attribute("href")

                    img_elem = produto.find_element(
                        By.CSS_SELECTOR,
                        "img.poly-component__picture, img"
                    )

                    imagem_url = (
                        img_elem.get_attribute("src")
                        or img_elem.get_attribute("data-src")
                    )

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


# 3. Enviando produto para o canal do Discord
async def enviar_discord(canal, nome, antigo, novo, porcentagem, link, imagem_url):

    # Remove parâmetros de rastreamento da URL
    # Isso evita que o link ultrapasse o limite de 512 caracteres do botão
    link_limpo = urlunparse(
        urlparse(link)._replace(query="", fragment="")
    )

    embed = discord.Embed(
        title="Promoção: " + nome,
        description=f"De {antigo} por {novo} ({porcentagem}% OFF)",
        url=link_limpo,
        color=discord.Color.purple()
    )

    embed.add_field(name="De", value=antigo, inline=True)
    embed.add_field(name="Para", value=novo, inline=True)
    embed.add_field(
        name="Desconto",
        value=f"{porcentagem}% OFF",
        inline=True
    )

    embed.set_footer(text="Promoções do Mercado Livre")

    # Adiciona a imagem do produto ao embed
    if imagem_url:
        embed.set_image(url=imagem_url)

    # ------------------------------------------------
    # CORREÇÃO: CRIANDO A VIEW ANTES DE ADICIONAR O BOTÃO
    # ------------------------------------------------

    # Cria a estrutura que armazenará o botão
    view = discord.ui.View()

    # Adiciona o botão com o link limpo do produto
    view.add_item(
        discord.ui.Button(
            label="Link do Produto",
            url=link_limpo
        )
    )

    # Envia a promoção para o canal do Discord
    await canal.send(embed=embed, view=view)

    print(
        f" <3 Promoção enviada para o Discord: {nome} "
        f"- De {antigo} para {novo} ({porcentagem}% OFF)"
    )


# 4. Classe responsável pelo bot
class PromoBot(discord.Client):

    async def setup_hook(self):
        self.monitoramento.start()

    @tasks.loop(minutes=10)
    async def monitoramento(self):

        canal = await self.fetch_channel(DISCORD_CHANNEL_ID)

        try:
            # Executa a coleta sem bloquear o funcionamento do Discord
            promocoes = await asyncio.to_thread(coletar_promocoes)

            for promocao in promocoes:

                # Envia cada promoção para o canal
                await enviar_discord(canal=canal, **promocao)

                # Armazena o link enviado
                links_enviados.add(promocao["link"])

        except Exception as e:
            print(f"Erro ao coletar promoções: {e}")

# 5. Executa a função e inicia o bot
if __name__ == "__main__":

    if not BOT_TOKEN:
        raise ValueError(
            "Configure a variável de ambiente DISCORD_BOT_TOKEN."
        )
    intent = discord.Intents.default()
    roxo = PromoBot(intents=intent)
    roxo.run(BOT_TOKEN)

    resultado = coletar_promocoes()