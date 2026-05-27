# clipping_agent.spec
# Gerado para PyInstaller 6.x
# Uso: pyinstaller clipping_agent.spec

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Raiz do projeto ──────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(SPEC))
SRC  = os.path.join(ROOT, "src")

# ── Dados a empacotar ────────────────────────────────────────────────────────
datas = []

# NLTK data (punkt, punkt_tab, stopwords)
import nltk
for nltk_path in nltk.data.path:
    if os.path.isdir(nltk_path):
        for subdir in ("tokenizers", "corpora"):
            full = os.path.join(nltk_path, subdir)
            if os.path.isdir(full):
                datas.append((full, os.path.join("nltk_data", subdir)))
        break  # usa apenas o primeiro caminho que existir

# Dados de todos os pacotes que os requerem
datas += collect_data_files("sumy")
datas += collect_data_files("xhtml2pdf")
datas += collect_data_files("reportlab")
datas += collect_data_files("PIL")
datas += collect_data_files("google.genai")
datas += collect_data_files("bs4")
datas += collect_data_files("certifi")
datas += collect_data_files("charset_normalizer")

# ── Hidden imports ────────────────────────────────────────────────────────────
hidden_imports = [
    # sumy
    "sumy.parsers.plaintext",
    "sumy.nlp.tokenizers",
    "sumy.nlp.stemmers",
    "sumy.summarizers.lsa",
    "sumy.utils",
    # nltk internals
    "nltk.tokenize",
    "nltk.corpus",
    "nltk.stem",
    # google-genai
    "google.genai",
    "google.auth",
    # xhtml2pdf / reportlab
    "xhtml2pdf",
    "xhtml2pdf.pisa",
    "reportlab",
    "reportlab.pdfbase.pdfmetrics",
    "reportlab.pdfbase._fontdata",
    "reportlab.lib.styles",
    "reportlab.platypus",
    # lxml
    "lxml",
    "lxml.etree",
    "lxml._elementpath",
    # Pillow (dependência do reportlab)
    "PIL",
    "PIL.Image",
    "PIL.ImageFont",
    "PIL.ImageDraw",
    # outros
    "markdown2",
    "bs4",
    "requests",
    "dotenv",
    "tkinter",
    "tkinter.scrolledtext",
    # módulos do projeto
    "services.search_service",
    "services.scraper_service",
    "services.summary_service",
    "services.report_service",
    "services.gemini_service",
    "services.link_persistence_service",
    "orchestrator",
    "error_orchestrator",
    "main",
]

hidden_imports += collect_submodules("sumy")
hidden_imports += collect_submodules("nltk")
hidden_imports += collect_submodules("reportlab")
hidden_imports += collect_submodules("PIL")
hidden_imports += collect_submodules("google.genai")

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(ROOT, "app.py")],
    pathex=[ROOT, SRC],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "pandas", "scipy", "IPython", "jupyter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="clipping_agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX pode causar falsos positivos em antivírus no Windows
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # sem janela de console (app com GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
