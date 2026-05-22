"""
SearchService — Etapa 1
Busca links usando a API Serper (google.serper.dev).
Requer SERPER_API_KEY no .env.
"""

import http.client
import json
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

MAX_RESULTS_PER_QUERY = 10


class SearchService:
    """
    Busca links de notícias/artigos sobre uma empresa via Serper API.
    Suporta filtro de período via parâmetro tbs (h=hora, d=dia, w=semana, m=mês, y=ano, ""=qualquer).
    """

    def __init__(
        self,
        api_key: str,
        results_count: int = 10,
        lang: str = "pt-br",
        tbs: str = "",
    ):
        self.api_key = (api_key or os.getenv("SERPER_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError("[SearchService] SERPER_API_KEY não configurada.")
        self.results_count = min(results_count, MAX_RESULTS_PER_QUERY)
        self.lang = lang
        self.tbs = tbs  # ex: "qdr:d", "qdr:w", "qdr:m" — vazio = qualquer período

    def search(self, company_name: str, visited_links: set) -> List[str]:
        """
        Executa a busca e retorna apenas links não visitados.
        """
        logger.info(f"[SearchService] Buscando: {company_name!r} | tbs={self.tbs!r}")

        raw_links = self._fetch(company_name)
        new_links = [url for url in raw_links if url not in visited_links]
        skipped = len(raw_links) - len(new_links)

        if skipped:
            logger.info(f"[SearchService] {skipped} link(s) já visitado(s), ignorados.")
        logger.info(f"[SearchService] {len(new_links)} novo(s) link(s) encontrado(s).")
        return new_links

    def _fetch(self, query: str) -> List[str]:
        payload: dict = {
            "q": query,
            "gl": "br",
            "hl": self.lang,
            "num": self.results_count,
        }
        # Só inclui tbs se tiver valor — vazio significa "qualquer período"
        if self.tbs:
            payload["tbs"] = f"qdr:{self.tbs}"

        try:
            conn = http.client.HTTPSConnection("google.serper.dev", timeout=15)
            conn.request(
                "POST",
                "/search",
                body=json.dumps(payload),
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            res = conn.getresponse()
            raw = res.read().decode("utf-8")
            conn.close()
        except Exception as exc:
            logger.error(f"[SearchService] Erro de conexão com Serper: {exc}")
            return []

        if res.status != 200:
            logger.error(f"[SearchService] Serper retornou HTTP {res.status}: {raw[:200]}")
            return []

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(f"[SearchService] Resposta inválida da Serper: {exc}")
            return []

        organic = data.get("organic", [])
        links = [item["link"] for item in organic if item.get("link")]
        logger.info(f"[SearchService] Serper retornou {len(links)} resultado(s).")
        return links