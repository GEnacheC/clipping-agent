"""
worker.py
Worker para execução agendada do pipeline de clipping.
Pode ser chamado por um cron job, APScheduler, Celery, etc.

Exemplo de uso com APScheduler (rodar a cada 24h):
    python worker.py

Exemplo de agendamento externo via cron:
    0 8 * * * cd /caminho/do/projeto && python worker.py >> data/worker.log 2>&1
"""

import logging
import sys
import time

logger = logging.getLogger(__name__)


def start_scheduler(interval_hours: int = 24) -> None:
    """
    Inicia o worker com loop de execução a cada `interval_hours` horas.
    Usa apenas stdlib (sem dependências externas de agendamento).

    Args:
        interval_hours: Intervalo entre execuções em horas (padrão: 24).
    """
    # Import local para evitar erros de configuração ao importar o módulo
    from main import run_clipping, build_orchestrator  # noqa: F401

    interval_seconds = interval_hours * 3600
    logger.info(f"[Worker] Iniciado. Executará a cada {interval_hours}h.")

    while True:
        logger.info("[Worker] Disparando ciclo de clipping...")
        try:
            run_clipping()
        except Exception as exc:
            logger.error(f"[Worker] Erro no ciclo: {exc}")

        logger.info(f"[Worker] Próxima execução em {interval_hours}h. Aguardando...")
        time.sleep(interval_seconds)


