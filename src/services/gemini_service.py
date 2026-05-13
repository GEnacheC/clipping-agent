"""
GeminiService — Etapa 5
Envia o dicionário de resumos ao Google Gemini para síntese final.
"""

import logging
from typing import Dict

from google import genai

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"

PROMPT_TEMPLATE = """
Você é um assistente especializado em clipping de notícias corporativas.

Abaixo estão resumos de artigos encontrados sobre a empresa "{company_name}".
Cada item contém a URL de origem e o resumo do conteúdo.

{articles_block}

Com base nesses resumos, produza uma SÍNTESE EXECUTIVA em português brasileiro contendo:
1. **Visão Geral**: O que está sendo dito sobre a empresa neste período.
2. **Principais Temas**: Liste os 3-5 temas mais recorrentes.
3. **Pontos Positivos**: Destaque menções favoráveis à empresa.
4. **Pontos de Atenção**: Destaque críticas ou alertas relevantes.
5. **Conclusão**: Uma breve conclusão sobre a reputação/imagem atual da empresa.

Seja objetivo e conciso. Máximo de 500 palavras.
"""


class GeminiService:
    """
    Responsável por enviar os resumos ao Google Gemini e obter uma síntese final.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("[GeminiService] GEMINI_API_KEY não configurada.")
        self.client = genai.Client(api_key=api_key)

    def synthesize(self, summaries: Dict[str, str], company_name: str) -> str:
        """
        Envia os resumos ao Gemini e retorna a síntese gerada.

        Args:
            summaries: Dicionário {url: resumo} — apenas entradas válidas.
            company_name: Nome da empresa para contextualizar o prompt.

        Returns:
            Texto da síntese gerada pelo Gemini, ou string de erro.
        """
        if not summaries:
            logger.warning("[GeminiService] Nenhum resumo válido para sintetizar.")
            return "Nenhum conteúdo disponível para síntese."

        articles_block = self._format_articles(summaries)
        prompt = PROMPT_TEMPLATE.format(
            company_name=company_name,
            articles_block=articles_block,
        )

        logger.info(f"[GeminiService] Enviando {len(summaries)} resumo(s) ao Gemini...")

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            synthesis = response.text
            logger.info("[GeminiService] Síntese recebida com sucesso.")
            return synthesis

        except Exception as exc:
            logger.error(f"[GeminiService] Erro ao chamar Gemini API: {exc}")
            return f"__ERROR__: {exc}"

    def _format_articles(self, summaries: Dict[str, str]) -> str:
        """
        Formata o bloco de artigos para inserção no prompt.
        """
        lines = []
        for idx, (url, summary) in enumerate(summaries.items(), start=1):
            lines.append(f"[{idx}] URL: {url}")
            lines.append(f"Resumo: {summary}")
            lines.append("")
        return "\n".join(lines)