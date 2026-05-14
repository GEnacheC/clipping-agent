"""
SearchService — Etapa 1
Busca links sobre uma empresa usando motor de pesquisa.
Retorna lista de URLs ainda não visitadas.
"""

import logging
import os
import random
import time
from typing import List

from serpapi import GoogleSearch

logger = logging.getLogger(__name__)

MAX_RESULTS_PER_QUERY = 10
MAX_RETRIES = 4


class SearchService:
    """
    Responsável por buscar links de notícias/artigos sobre uma empresa.
    Filtra links já visitados antes de retornar.
    """

    def __init__(
        self,
        api_key: str,
        results_count: int = 10,
        lang: str = "pt-BR",
        pause: float = 2.0,
    ):
        """
        Args:
            api_key: Chave da API SerpAPI.
            results_count: Quantidade máxima de resultados por busca.
            lang: Idioma preferido dos resultados.
            pause: Pausa (segundos) entre requisições para evitar bloqueio.
        """
        self.api_key = (api_key or os.getenv("SERPAPI_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError("[SearchService] SERPAPI_API_KEY não configurada.")
        self.results_count = min(results_count, MAX_RESULTS_PER_QUERY)
        self.lang = lang
        self.pause = pause

    def search(self, company_name: str, visited_links: set) -> List[str]:
        """
        Executa a busca e retorna apenas links não visitados.

        Args:
            company_name: Nome da empresa a ser pesquisada.
            visited_links: Conjunto de links já processados (para exclusão).

        Returns:
            Lista de URLs novas encontradas.
        """
        query = f'{company_name}'
        logger.info(f"[SearchService] Buscando por: {query!r}")

        new_links: List[str] = []

        results = self._search_with_retries(query)
        for url in results:
            if url not in visited_links:
                new_links.append(url)
                logger.debug(f"[SearchService] Novo link encontrado: {url}")
            else:
                logger.debug(f"[SearchService] Link já visitado, ignorado: {url}")

        logger.info(f"[SearchService] {len(new_links)} novo(s) link(s) encontrado(s).")
        return new_links

    def _search_with_retries(self, query: str) -> List[str]:
        """
        Tenta executar a busca com retentativas quando o Google responde 429.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                search_client = GoogleSearch(
                    {
                        "engine": "google",
                        "q": query,
                        "num": self.results_count,
                        "hl": "pt",
                        "gl": "br",
                        "api_key": self.api_key,
                    }
                )
                data = search_client.get_dict()
                organic_results = data.get("organic_results", [])
                links = [item.get("link") for item in organic_results if item.get("link")]
                return links[: self.results_count]
            except Exception as exc:
                if self._is_rate_limit_error(exc) and attempt < MAX_RETRIES:
                    wait_seconds = self._compute_backoff(attempt)
                    logger.warning(
                        "[SearchService] Rate limit na SerpAPI. Nova tentativa em %.1fs (%d/%d).",
                        wait_seconds,
                        attempt,
                        MAX_RETRIES,
                    )
                    time.sleep(wait_seconds)
                    continue

                logger.error(f"[SearchService] Erro durante a busca: {exc}")
                return []

        return []

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        message = str(exc)
        return "429" in message or "Too Many Requests" in message

    def _compute_backoff(self, attempt: int) -> float:
        # Backoff exponencial com jitter para reduzir chance de novo bloqueio.
        base = max(self.pause, 2.0)
        return base * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)