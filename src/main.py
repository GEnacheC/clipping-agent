"""
main.py
Ponto de entrada manual para testes e execução direta.
Para uso em worker agendado, importe e chame run_clipping() de outro módulo.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Imports dos serviços e orquestrador ───────────────────────────────────
from services.search_service import SearchService
from services.scraper_service import ScraperService
from services.summary_service import SummaryService
from services.report_service import ReportService
from services.gemini_service import GeminiService
from services.link_persistence_service import LinkPersistenceService
from error_orchestrator import ErrorLinkOrchestrator
from orchestrator import ClippingOrchestrator

# ── Configuração de logging ────────────────────────────────────────────────
# Cria o diretório data/ se não existir
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

# ── Carrega variáveis de ambiente ──────────────────────────────────────────
load_dotenv()


def build_orchestrator() -> ClippingOrchestrator:
    """
    Instancia todos os serviços e monta o orquestrador.
    Centraliza a configuração para facilitar testes e injeção de dependências.
    """
    company_name = os.getenv("COMPANY_NAME", "").strip()
    if not company_name:
        raise ValueError("Variável de ambiente COMPANY_NAME não configurada.")

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        raise ValueError("Variável de ambiente GEMINI_API_KEY não configurada.")

    serpapi_api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not serpapi_api_key:
        raise ValueError("Variável de ambiente SERPAPI_API_KEY não configurada.")

    visited_links_file = os.getenv("VISITED_LINKS_FILE", "data/visited_links.txt")
    output_md_file = os.getenv("OUTPUT_MD_FILE", "data/clipping_output.md")
    search_count = int(os.getenv("SEARCH_RESULTS_COUNT", "10"))

    # Garante que o diretório de dados existe
    Path("data").mkdir(exist_ok=True)

    return ClippingOrchestrator(
        search_service=SearchService(api_key=serpapi_api_key, results_count=search_count),
        scraper_service=ScraperService(),
        summary_service=SummaryService(),
        report_service=ReportService(output_path=output_md_file),
        gemini_service=GeminiService(api_key=gemini_api_key),
        persistence_service=LinkPersistenceService(filepath=visited_links_file),
        company_name=company_name,
    )


def build_error_orchestrator() -> ErrorLinkOrchestrator:
    """
    Instancia o orquestrador dedicado a links com erro.
    """
    visited_links_file = os.getenv("VISITED_LINKS_FILE", "data/visited_links.txt")

    return ErrorLinkOrchestrator(
        scraper_service=ScraperService(),
        summary_service=SummaryService(),
        persistence_service=LinkPersistenceService(filepath=visited_links_file),
    )


def run_clipping() -> None:
    """
    Função principal que pode ser chamada tanto pelo main quanto por um worker.
    """
    try:
        # Etapa separada: reprocessa apenas links que já estavam marcados como erro.
        # error_orchestrator = build_error_orchestrator()
        # error_orchestrator.run()

        # Pipeline principal: busca novos links e processa normalmente.
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