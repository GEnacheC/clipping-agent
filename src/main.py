"""
main.py
Ponto de entrada manual para testes e execução direta.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from services.search_service import SearchService
from services.scraper_service import ScraperService
from services.summary_service import SummaryService
from services.report_service import ReportService
from services.gemini_service import GeminiService
from services.link_persistence_service import LinkPersistenceService
from error_orchestrator import ErrorLinkOrchestrator
from orchestrator import ClippingOrchestrator

Path("data").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/clipping.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

load_dotenv()


def build_orchestrator(tbs: str = "") -> ClippingOrchestrator:
    """
    Instancia todos os serviços e monta o orquestrador.
    tbs: filtro de período para Serper ("h","d","w","m","y" ou "" para qualquer período)
    """
    company_name = os.getenv("COMPANY_NAME", "").strip()
    if not company_name:
        raise ValueError("Variável de ambiente COMPANY_NAME não configurada.")

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        raise ValueError("Variável de ambiente GEMINI_API_KEY não configurada.")

    serper_api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not serper_api_key:
        raise ValueError("Variável de ambiente SERPER_API_KEY não configurada.")

    visited_links_file = os.getenv("VISITED_LINKS_FILE", "data/visited_links.txt")
    output_md_file     = os.getenv("OUTPUT_MD_FILE",     "data/clipping_output.md")
    search_count       = int(os.getenv("SEARCH_RESULTS_COUNT", "10"))

    Path("data").mkdir(exist_ok=True)

    return ClippingOrchestrator(
        search_service=SearchService(
            api_key=serper_api_key,
            results_count=search_count,
            tbs=tbs,
        ),
        scraper_service=ScraperService(),
        summary_service=SummaryService(),
        report_service=ReportService(output_path=output_md_file),
        gemini_service=GeminiService(api_key=gemini_api_key),
        persistence_service=LinkPersistenceService(filepath=visited_links_file),
        company_name=company_name,
    )


def build_error_orchestrator() -> ErrorLinkOrchestrator:
    visited_links_file = os.getenv("VISITED_LINKS_FILE", "data/visited_links.txt")
    return ErrorLinkOrchestrator(
        scraper_service=ScraperService(),
        summary_service=SummaryService(),
        persistence_service=LinkPersistenceService(filepath=visited_links_file),
    )


def run_clipping() -> None:
    try:
        orchestrator = build_orchestrator()
        synthesis = orchestrator.run()

        if synthesis:
            print("\n" + "=" * 60)
            print("SÍNTESE EXECUTIVA (Gemini)")
            print("=" * 60)
            print(synthesis)
            print("=" * 60 + "\n")
        else:
            logger.info("Nenhum conteúdo novo processado neste ciclo.")

    except ValueError as exc:
        logger.error(f"Configuração inválida: {exc}")
        sys.exit(1)
    except Exception as exc:
        logger.exception(f"Erro inesperado no pipeline: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    run_clipping()