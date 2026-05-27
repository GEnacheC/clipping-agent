#!/usr/bin/env bash
# build.sh — Gera o executável clipping_agent
# Uso: bash build.sh (na raiz do projeto)

set -e

echo "[1/3] Instalando dependencias..."
pip install -r requirements.txt pyinstaller --quiet

echo "[2/3] Baixando dados do NLTK..."
python3 -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)"

echo "[3/3] Compilando executavel..."
pyinstaller clipping_agent.spec --noconfirm

echo ""
echo "============================================================"
echo "Executavel gerado em: dist/clipping_agent"
echo "Copie o arquivo .env para a mesma pasta do executavel."
echo "============================================================"
