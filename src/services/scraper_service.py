"""
ScraperService — Etapa 2
Faz scraping de cada URL e extrai o texto principal do artigo.
"""

import logging
import unicodedata
from typing import Dict

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ERROR_TOKEN = "__ERROR__"

# Timeout para requisições HTTP (segundos)
REQUEST_TIMEOUT = 10

# Headers para simular navegador e evitar bloqueios simples
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Tags HTML que geralmente contêm o corpo do artigo
ARTICLE_TAGS = ["article", "main", "section"]

# Classes/IDs comuns de containers de conteúdo
CONTENT_SELECTORS = [
    "article",
    '[class*="article"]',
    '[class*="content"]',
    '[class*="post-body"]',
    '[class*="entry-content"]',
    "main",
]


class ScraperService:
    """
    Responsável por fazer o scraping de uma lista de URLs e extrair
    o texto principal de cada página.
    """

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def scrape_all(self, urls: list) -> Dict[str, str]:
        """
        Processa uma lista de URLs e retorna dicionário com o texto extraído.

        Args:
            urls: Lista de URLs para scraping.

        Returns:
            Dict[url -> texto_extraido | "__ERROR__"]
            Valor "__ERROR__" indica falha no scraping daquele link.
        """
        results: Dict[str, str] = {}

        for url in urls:
            logger.info(f"[ScraperService] Fazendo scraping de: {url}")
            content = self._scrape(url)
            results[url] = content

        return results

    def scrape_error_links(self, error_urls: list) -> Dict[str, str]:
        """
        Reprocessa apenas URLs que já foram marcadas como erro anteriormente.

        Args:
            error_urls: Lista de URLs com status ERROR no arquivo de persistência.

        Returns:
            Dicionário {url: texto_extraido | "__ERROR__"} com os resultados do retry.
        """
        if not error_urls:
            logger.info("[ScraperService] Nenhum link com erro para reprocessar.")
            return {}

        logger.info(
            f"[ScraperService] Reprocessando {len(error_urls)} link(s) com erro."
        )

        recovered_results: Dict[str, str] = {}
        recovered_count = 0
        for url in error_urls:
            logger.info(f"[ScraperService] Nova tentativa de scraping: {url}")
            content = self._scrape(url)
            recovered_results[url] = content
            if content != ERROR_TOKEN:
                recovered_count += 1

        logger.info(
            f"[ScraperService] Reprocessamento concluído. {recovered_count} link(s) recuperado(s)."
        )
        return recovered_results

    def _scrape(self, url: str) -> str:
        """
        Extrai o texto principal de uma única URL.

        Returns:
            Texto do artigo ou "__ERROR__" em caso de falha.
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning(f"[ScraperService] Falha na requisição para {url}: {exc}")
            return ERROR_TOKEN

        try:
            html_text = self._decode_response_text(response)
            soup = BeautifulSoup(html_text, "lxml")

            # Remove elementos desnecessários
            for tag in soup(["script", "style", "nav", "header", "footer",
                              "aside", "form", "noscript", "iframe"]):
                tag.decompose()

            # Tenta encontrar o container principal do artigo
            text = self._extract_main_content(soup)

            if not text or len(text.strip()) < 100:
                # Fallback: pega todo o body
                body = soup.find("body")
                text = body.get_text(separator=" ", strip=True) if body else ""

            if not text or len(text.strip()) < 100:
                logger.warning(f"[ScraperService] Conteúdo insuficiente em {url}")
                return ERROR_TOKEN

            return self._clean_text(text)

        except Exception as exc:
            logger.error(f"[ScraperService] Erro ao parsear HTML de {url}: {exc}")
            return ERROR_TOKEN

    def _decode_response_text(self, response: requests.Response) -> str:
        """
        Decodifica o HTML usando a melhor pista de charset disponível e normaliza o texto.
        """
        detected_encoding = response.apparent_encoding or response.encoding or "utf-8"
        try:
            return response.content.decode(detected_encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return response.content.decode("utf-8", errors="replace")

    def _clean_text(self, text: str) -> str:
        """
        Normaliza símbolos estranhos e remove caracteres de controle invisíveis.
        """
        normalized = unicodedata.normalize("NFKC", text)
        cleaned = []
        for char in normalized:
            if char in "\n\r\t" or char == " " or unicodedata.category(char)[0] != "C":
                cleaned.append(char)
        return "".join(cleaned).replace("\uFFFD", " ").strip()

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Tenta extrair o bloco de texto mais relevante da página.
        """
        for selector in CONTENT_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=" ", strip=True)
                if len(text) > 200:
                    return text

        # Fallback: parágrafo mais longo da página
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 40)
        return text