"""
ErrorLinkOrchestrator
Responsável apenas por reprocessar links previamente marcados como erro.
"""

import logging
from typing import Dict

from services.scraper_service import ScraperService
from services.summary_service import SummaryService
from services.link_persistence_service import LinkPersistenceService
from services.link_persistence_service import STATUS_ERROR

logger = logging.getLogger(__name__)


class ErrorLinkOrchestrator:
    """
    Orquestrador dedicado ao retry de links com status ERROR.
    Ele não faz busca nem sumarização; apenas tenta recuperar os conteúdos
    que falharam em execuções anteriores.
    """

    def __init__(
        self,
        scraper_service: ScraperService,
        summary_service: SummaryService,
        persistence_service: LinkPersistenceService,
    ):
        self.scraper_service = scraper_service
        self.summary_service = summary_service
        self.persistence_service = persistence_service

    def run(self) -> Dict[str, str]:
        """
        Reprocessa somente os links já persistidos com status ERROR.

        Returns:
            Dicionário {url: texto_extraido | "__ERROR__"} com os resultados do retry.
        """
        status_map = self.persistence_service.load_status_map()
        error_links = [url for url, status in status_map.items() if status == STATUS_ERROR]

        if not error_links:
            logger.info("[ErrorLinkOrchestrator] Nenhum link com erro para reprocessar.")
            return {}

        logger.info(
            f"[ErrorLinkOrchestrator] Reprocessando {len(error_links)} link(s) com erro."
        )

        recovered_scraped_data = self.scraper_service.scrape_error_links(error_links)
        if not recovered_scraped_data:
            return {}

        recovered_summaries = self.summary_service.summarize_all(recovered_scraped_data)
        self.persistence_service.save_results(recovered_summaries)
        logger.info("[ErrorLinkOrchestrator] Resultados do retry persistidos.")

        return recovered_summaries