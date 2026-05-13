# 🗞️ Clipping Agent

Agente de clipping de notícias em Python. Monitora menções de uma empresa na web, extrai artigos, resume com algoritmos clássicos de NLP e gera uma síntese executiva com Google Gemini.

---

## 📐 Arquitetura

```
main.py / worker.py
       │
       ▼
ClippingOrchestrator (orchestrator.py)
       │
       ├── [0] LinkPersistenceService  → lê links já visitados (data/visited_links.txt)
       ├── [1] SearchService           → busca novos links no Google
       ├── [2] ScraperService          → faz webscraping de cada link
       ├── [3] SummaryService          → resume textos com LSA (sem IA)
       ├── [0b] LinkPersistenceService → persiste links com status OK/ERROR
       ├── [4] ReportService           → gera relatório .md (data/clipping_output.md)
       └── [5] GeminiService           → síntese executiva via Google Gemini
```

Cada serviço é **completamente independente** — recebe dados, processa, retorna. Nenhum serviço conhece os outros.

---

## 🚀 Instalação

```bash
# 1. Clone o repositório
git clone <repo-url>
cd clipping_agent

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com seu editor preferido
```

---

## ⚙️ Configuração (`.env`)

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `COMPANY_NAME` | ✅ | Nome da empresa a monitorar |
| `GEMINI_API_KEY` | ✅ | Chave da API do Google Gemini ([obter aqui](https://aistudio.google.com)) |
| `SEARCH_RESULTS_COUNT` | ❌ | Qtd. de resultados por busca (padrão: `10`) |
| `VISITED_LINKS_FILE` | ❌ | Caminho do arquivo de links (padrão: `data/visited_links.txt`) |
| `OUTPUT_MD_FILE` | ❌ | Caminho do relatório .md (padrão: `data/clipping_output.md`) |

---

## ▶️ Uso

### Execução manual (testes)
```bash
python main.py
```

### Worker com loop automático a cada 24h
```bash
python worker.py
```

### Worker — execução única (ideal para cron externo)
```bash
WORKER_MODE=once python worker.py
```

### Cron job (todo dia às 8h)
```bash
0 8 * * * cd /caminho/do/projeto && .venv/bin/python worker.py >> data/worker.log 2>&1
```

### Intervalo customizado (ex: a cada 6h)
```bash
WORKER_INTERVAL_HOURS=6 python worker.py
```

---

## 📁 Estrutura de arquivos

```
clipping_agent/
├── main.py                          # Entrada principal / testes manuais
├── worker.py                        # Worker para execução agendada
├── orchestrator.py                  # Orquestrador do pipeline
├── requirements.txt
├── .env.example
├── services/
│   ├── search_service.py            # Etapa 1: busca de links
│   ├── scraper_service.py           # Etapa 2: webscraping
│   ├── summary_service.py           # Etapa 3: sumarização (LSA)
│   ├── report_service.py            # Etapa 4: geração de .md
│   ├── gemini_service.py            # Etapa 5: síntese com Gemini
│   └── link_persistence_service.py  # Persistência de links visitados
└── data/                            # Gerado automaticamente
    ├── visited_links.txt            # Histórico: STATUS|URL
    ├── clipping_output.md           # Relatório acumulado
    └── clipping.log                 # Log de execução
```

---

## 🔒 Formato do arquivo de links (`visited_links.txt`)

```
OK|https://www.exemplo.com.br/noticia-1
OK|https://www.portal.com/artigo-2
ERROR|https://www.site-bloqueado.com/post-3
```

- `OK` → processado com sucesso
- `ERROR` → falhou no scraping ou sumarização (não será retentado)

---

## 🧩 Como adicionar um novo serviço

1. Crie `services/meu_servico.py` com uma classe independente
2. Adicione a instância em `main.py` > `build_orchestrator()`
3. Injete e chame no `orchestrator.py` na sequência correta

---

## 📦 Dependências principais

| Biblioteca | Uso |
|------------|-----|
| `googlesearch-python` | Busca de links (Etapa 1) |
| `requests` + `beautifulsoup4` | Webscraping (Etapa 2) |
| `sumy` + `nltk` | Sumarização LSA sem IA (Etapa 3) |
| `google-generativeai` | Síntese Gemini (Etapa 5) |
| `python-dotenv` | Gerenciamento de variáveis de ambiente |