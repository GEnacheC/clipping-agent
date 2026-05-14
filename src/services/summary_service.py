"""
SummaryService — Etapa 3
Resume textos usando algoritmos clássicos de NLP (sem IA).
Utiliza a biblioteca `sumy` com o algoritmo LSA (Latent Semantic Analysis).
"""

import logging
from typing import Dict

import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

logger = logging.getLogger(__name__)

# Idioma para o algoritmo de sumarização
LANGUAGE = "portuguese"

# Número de frases no resumo
SENTENCES_COUNT = 5

# Garante que os recursos do NLTK estejam disponíveis
def _ensure_nltk_resources():
    for resource in ["punkt", "punkt_tab", "stopwords"]:
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except (LookupError, OSError):
            try:
                nltk.data.find(f"corpora/{resource}")
            except (LookupError, OSError):
                logger.info(f"[SummaryService] Baixando recurso NLTK: {resource}")
                nltk.download(resource, quiet=True)


class SummaryService:
    """
    Responsável por resumir textos extraídos pelo ScraperService.
    Usa LSA (Latent Semantic Analysis) da biblioteca sumy.
    Links com erro são marcados mas mantidos no dicionário de saída.
    """

    def __init__(self, sentences_count: int = SENTENCES_COUNT):
        self.sentences_count = sentences_count
        _ensure_nltk_resources()
        self.stemmer = Stemmer(LANGUAGE)
        self.summarizer = LsaSummarizer(self.stemmer)
        self.summarizer.stop_words = get_stop_words(LANGUAGE)

    def summarize_all(self, scraped_data: Dict[str, str]) -> Dict[str, str]:
        """
        Recebe dicionário {url: texto} e retorna {url: resumo}.

        Links com valor "__ERROR__" são mantidos com status de erro
        para que o LinkPersistenceService possa registrá-los corretamente.

        Args:
            scraped_data: Saída do ScraperService.

        Returns:
            Dict[url -> resumo | "__ERROR__"]
        """
        summaries: Dict[str, str] = {}

        for url, text in scraped_data.items():
            if text == "__ERROR__":
                logger.warning(f"[SummaryService] Pulando URL com erro de scraping: {url}")
                summaries[url] = "__ERROR__"
                continue

            logger.info(f"[SummaryService] Resumindo conteúdo de: {url}")
            summary = self._summarize(url, text)
            summaries[url] = summary

        return summaries

    def _summarize(self, url: str, text: str) -> str:
        """
        Resume um único texto. Retorna "__ERROR__" se falhar.
        """
        try:
            parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
            sentences = self.summarizer(parser.document, self.sentences_count)
            summary = " ".join(str(sentence) for sentence in sentences)

            if not summary.strip():
                logger.warning(f"[SummaryService] Resumo vazio para {url}, usando início do texto.")
                # Fallback: primeiras 500 chars do texto original
                summary = text[:500].rsplit(" ", 1)[0] + "..."

            return summary

        except Exception as exc:
            logger.error(f"[SummaryService] Erro ao resumir {url}: {exc}")
            return "__ERROR__"