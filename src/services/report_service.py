"""
ReportService — Etapa 4
Gera um arquivo .md a partir do dicionário de resumos.
Cada chave (URL) vira um título e o resumo vira o parágrafo abaixo.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

import markdown2
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)


class ReportService:
    """
    Responsável por gerar o relatório em Markdown com os resumos coletados.
    Links com erro são incluídos com uma nota explicativa.
    """

    def __init__(self, output_path: str = "data/clipping_output.md"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self, summaries: Dict[str, str], company_name: str) -> str:
        """
        Gera o arquivo .md e retorna o conteúdo como string.

        Args:
            summaries: Dicionário {url: resumo | "__ERROR__"} da SummaryService.
            company_name: Nome da empresa para o cabeçalho do relatório.

        Returns:
            Conteúdo Markdown gerado como string.
        """
        valid_summaries = {
            url: summary
            for url, summary in summaries.items()
            if summary != "__ERROR__"
        }

        if not valid_summaries:
            logger.warning("[ReportService] Nenhum resumo válido para gerar relatório.")
            return ""

        timestamp_human = datetime.now().strftime("%d/%m/%Y %H:%M")
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_path.parent / f"clipping_output_{timestamp_file}.md"

        lines = [
            f"# Clipping: {company_name}",
            f"_Gerado em: {timestamp_human}_",
            "",
            "---",
            "",
        ]

        for url, summary in valid_summaries.items():
            lines.append(f"## {url}")
            lines.append("")
            lines.append(summary)
            lines.append("")
            lines.append("---")
            lines.append("")

        content = "\n".join(lines)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"[ReportService] Relatório salvo em: {output_path}")
        except IOError as exc:
            logger.error(f"[ReportService] Erro ao salvar relatório: {exc}")

        return content

    def get_summaries_for_gemini(self, summaries: Dict[str, str]) -> Dict[str, str]:
        """
        Filtra e retorna apenas os resumos válidos para envio ao Gemini.

        Args:
            summaries: Dicionário completo com possíveis erros.

        Returns:
            Dicionário apenas com entradas válidas.
        """
        return {
            url: summary
            for url, summary in summaries.items()
            if summary != "__ERROR__"
        }

    def save_synthesis(self, synthesis: str, company_name: str, filename: str | None = None) -> str:
        """
        Salva a síntese gerada pelo Gemini em um arquivo Markdown e retorna o caminho.

        Args:
            synthesis: Texto da síntese gerada.
            company_name: Nome da empresa para o cabeçalho.
            filename: Nome do arquivo (opcional). Se não fornecido, gera com timestamp.

        Returns:
            Caminho do arquivo salvo como string.
        """
        timestamp_human = datetime.now().strftime("%d/%m/%Y %H:%M")
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = filename or f"gemini_synthesis_{timestamp_file}.md"
        path = self.output_path.parent / file_name

        lines = [
            f"# Síntese Executiva: {company_name}",
            "",
            synthesis,
            "",
            f"_Gerado em: {timestamp_human}_",
        ]

        content = "\n".join(lines)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"[ReportService] Síntese salva em: {path}")
        except IOError as exc:
            logger.error(f"[ReportService] Erro ao salvar síntese: {exc}")

        # Converter síntese para PDF
        try:
            pdf_path = path.with_suffix(".pdf")
            html_body = markdown2.markdown(content, extras=["fenced-code-blocks", "tables"])
            html_full = f"""<!DOCTYPE html>
            <html><head><meta charset="utf-8">
            <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; color: #222; }}
            h1 {{ color: #1a1a2e; }} h2 {{ color: #16213e; }}
            hr {{ border: 1px solid #ddd; }}
            em {{ color: #555; }}
            </style></head><body>{html_body}</body></html>"""
            with open(pdf_path, "wb") as pdf_file:
                result = pisa.CreatePDF(html_full, dest=pdf_file)
            if result.err:
                logger.error(f"[ReportService] Erro ao gerar PDF: {result.err}")
            else:
                logger.info(f"[ReportService] PDF gerado em: {pdf_path}")
        except Exception as exc:
            logger.error(f"[ReportService] Erro ao gerar PDF: {exc}")

        return str(path)