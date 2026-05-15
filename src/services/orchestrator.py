"""
ClippingOrchestrator
Coordena todas as etapas do pipeline de clipping.
Pode ser chamado diretamente na main.py (para testes) ou por um worker agendado.
"""

import logging
from typing import Optional

from services.search_service import SearchService
from services.scraper_service import ScraperService
from services.summary_service import SummaryService
from services.report_service import ReportService
from services.gemini_service import GeminiService
from services.link_persistence_service import LinkPersistenceService

logger = logging.getLogger(__name__)


class ClippingOrchestrator:
    """
    Orquestrador do agente de clipping.
    Recebe instâncias de todos os serviços e os executa em sequência.
    Cada serviço é independente; o orquestrador apenas passa os dados adiante.
    """

    def __init__(
        self,
        search_service: SearchService,
        scraper_service: ScraperService,
        summary_service: SummaryService,
        report_service: ReportService,
        gemini_service: GeminiService,
        persistence_service: LinkPersistenceService,
        company_name: str,
    ):
        self.search_service = search_service
        self.scraper_service = scraper_service
        self.summary_service = summary_service
        self.report_service = report_service
        self.gemini_service = gemini_service
        self.persistence_service = persistence_service
        self.company_name = company_name

    def run(self) -> Optional[str]:
        """
        Executa o pipeline completo de clipping.

        Returns:
            Síntese final gerada pelo Gemini, ou None se não houver conteúdo novo.
        """
        logger.info("=" * 60)
        logger.info(f"[Orchestrator] Iniciando ciclo de clipping para: {self.company_name!r}")
        logger.info("=" * 60)

        # ── Etapa 0: Carregar links já visitados ──────────────────────────────
        visited_links = self.persistence_service.load_visited()
        logger.info(f"[Orchestrator] Links já visitados: {len(visited_links)}")

        # ── Etapa 1: Buscar novos links ────────────────────────────────────────
        new_links = self.search_service.search(self.company_name, visited_links)

        if not new_links:
            logger.info("[Orchestrator] Nenhum link novo encontrado. Encerrando ciclo.")
            return None

        if new_links:
            logger.info(f"[Orchestrator] {len(new_links)} novo(s) link(s) para processar.")

        # ── Etapa 2: Scraping dos novos links ───────────────────────────────
        scraped_data = self.scraper_service.scrape_all(new_links)
        logger.info(f"[Orchestrator] Scraping concluído. {len(scraped_data)} URL(s) processada(s).")

        # ── Etapa 3: Sumarização ──────────────────────────────────────────────
        summaries = self.summary_service.summarize_all(scraped_data)
        logger.info(f"[Orchestrator] Sumarização concluída.")

        # ── Etapa 0b: Persistir todos os links ANTES de prosseguir ────────────
        # (garante registro mesmo que as etapas seguintes falhem)
        self.persistence_service.save_results(summaries)
        logger.info("[Orchestrator] Links persistidos com status.")

        # ── Etapa 4: Gerar relatório .md ──────────────────────────────────────
        valid_summaries = self.report_service.get_summaries_for_gemini(summaries)

        if not valid_summaries:
            logger.warning("[Orchestrator] Todos os links resultaram em erro. Sem relatório.")
            return None

        md_content = self.report_service.generate(valid_summaries, self.company_name)
        logger.info("[Orchestrator] Relatório .md gerado.")

        # ── Etapa 5: Síntese com Gemini ───────────────────────────────────────
        synthesis = self.gemini_service.synthesize(valid_summaries, self.company_name)
        logger.info("[Orchestrator] Síntese Gemini concluída.")

        try:
            synthesis_path = self.report_service.save_synthesis(synthesis, self.company_name)
            logger.info(f"[Orchestrator] Síntese salva em: {synthesis_path}")
        except Exception as exc:
            logger.error(f"[Orchestrator] Erro ao salvar síntese: {exc}")
        logger.info("=" * 60)
        logger.info("[Orchestrator] Ciclo finalizado com sucesso.")
        logger.info("=" * 60)

        # return None  # Retorna None por enquanto, pois a síntese está comentada para testes iniciais
        return synthesis