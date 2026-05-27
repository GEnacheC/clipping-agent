"""
app.py — Entry point do executável.
Configura sys.path e BASE_DIR antes de qualquer import do projeto,
garantindo que tudo funcione tanto em modo script quanto frozen (PyInstaller).
"""

import os
import sys


def _setup_environment():
    """
    Resolve BASE_DIR e garante que src/ esteja no sys.path.

    - Frozen (PyInstaller onefile):  BASE_DIR = pasta onde o .exe está
    - Frozen (PyInstaller onedir):   BASE_DIR = pasta do bundle
    - Script normal:                 BASE_DIR = pasta deste arquivo
    """
    if getattr(sys, "frozen", False):
        # sys.executable aponta para o .exe; a pasta dele é BASE_DIR
        base_dir = os.path.dirname(sys.executable)
        # PyInstaller extrai os módulos em sys._MEIPASS
        bundle_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        bundle_dir = os.path.join(base_dir, "src")

    # Garante que imports como "from services.xxx" funcionem
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

    # BASE_DIR disponível globalmente para todo o projeto
    os.environ.setdefault("CLIPPING_BASE_DIR", base_dir)

    # Muda o CWD para BASE_DIR para que caminhos relativos ("data/...") funcionem
    os.chdir(base_dir)

    # Carrega .env de BASE_DIR (onde o usuário coloca o arquivo)
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=False)


if __name__ == "__main__":
    _setup_environment()

    import tkinter as tk
    from gui import ClippingGUI

    root = tk.Tk()
    app = ClippingGUI(root)
    root.mainloop()
