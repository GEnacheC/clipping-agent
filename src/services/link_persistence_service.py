"""
LinkPersistenceService
Gerencia a persistência de links visitados em arquivo .txt.
Cada linha do arquivo segue o formato: STATUS|URL
  - OK|https://...   → processado com sucesso
  - ERROR|https://...→ tentativa falhou (scraping ou resumo)
"""

import logging
from pathlib import Path
from typing import Dict, Set

logger = logging.getLogger(__name__)

STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
SEPARATOR = "|"


class LinkPersistenceService:
    """
    Responsável por ler e gravar o histórico de links processados.
    Garante que nenhum link seja reprocessado, mesmo em caso de erro anterior.
    """

    def __init__(self, filepath: str = "data/visited_links.txt"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Cria o arquivo se não existir
        if not self.filepath.exists():
            self.filepath.touch()
            logger.info(f"[LinkPersistenceService] Arquivo criado: {self.filepath}")

    def load_visited(self) -> Set[str]:
        """
        Lê o arquivo e retorna o conjunto de todas as URLs já processadas
        (independente de terem tido sucesso ou erro).
        """
        visited: Set[str] = set()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if SEPARATOR in line:
                        _, url = line.split(SEPARATOR, 1)
                        visited.add(url.strip())
        except IOError as exc:
            logger.error(f"[LinkPersistenceService] Erro ao ler arquivo: {exc}")
        logger.info(f"[LinkPersistenceService] {len(visited)} link(s) já registrado(s).")
        return visited

    def save_results(self, results: Dict[str, str]) -> None:
        """
        Persiste o resultado de cada link processado no ciclo atual.

        Args:
            results: Dicionário {url: resumo | "__ERROR__"}
                     Vindo da SummaryService (após scraping + resumo).
        """
        lines_to_write = []
        for url, content in results.items():
            status = STATUS_ERROR if content == "__ERROR__" else STATUS_OK
            lines_to_write.append(f"{status}{SEPARATOR}{url}\n")

        if not lines_to_write:
            return

        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.writelines(lines_to_write)
            logger.info(
                f"[LinkPersistenceService] {len(lines_to_write)} link(s) persistido(s) em {self.filepath}."
            )
        except IOError as exc:
            logger.error(f"[LinkPersistenceService] CRÍTICO — falha ao persistir links: {exc}")
            # Loga individualmente para não perder rastreabilidade
            for line in lines_to_write:
                logger.error(f"[LinkPersistenceService] Não persistido → {line.strip()}")

    def load_status_map(self) -> Dict[str, str]:
        """
        Retorna mapa completo {url: status} para auditoria.
        """
        status_map: Dict[str, str] = {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if SEPARATOR in line:
                        status, url = line.split(SEPARATOR, 1)
                        status_map[url.strip()] = status.strip()
        except IOError as exc:
            logger.error(f"[LinkPersistenceService] Erro ao ler status map: {exc}")
        return status_map