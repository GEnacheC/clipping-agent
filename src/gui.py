"""
gui.py — Interface gráfica do Clipping Agent
Design: flat, claro, paleta azul e branco. Sem sombras pesadas, sem escuridão.
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import os
import sys
import subprocess
import queue
from datetime import datetime

# ── Paleta flat azul/branco ───────────────────────────────────────────────────
WHITE       = "#FFFFFF"
BG_APP      = "#F0F4F8"       # cinza-azulado muito suave (fundo geral)
BG_CARD     = "#FFFFFF"       # cards e painéis
BG_INPUT    = "#F7FAFC"       # campos de texto
BG_LOG      = "#F0F4F8"       # área de log
BORDER      = "#D0DCE8"       # bordas suaves
BLUE_PRI    = "#2563EB"       # azul primário (botão, labels ativos)
BLUE_HOV    = "#1D4ED8"       # hover do botão
BLUE_LIGHT  = "#DBEAFE"       # fundo dos pills selecionados
BLUE_MUTED  = "#93C5FD"       # pills não selecionados — texto
TEXT_DARK   = "#1E293B"       # texto principal
TEXT_MID    = "#475569"       # texto secundário
TEXT_MUTED  = "#94A3B8"       # texto desabilitado / timestamps
LOG_DEFAULT = "#334155"       # texto padrão do log
LOG_INFO    = "#2563EB"       # log info
LOG_SUCCESS = "#16A34A"       # log sucesso
LOG_WARN    = "#B45309"       # log aviso
LOG_ERROR   = "#DC2626"       # log erro

FONT_UI     = ("Segoe UI", 10)
FONT_LABEL  = ("Segoe UI", 9, "bold")
FONT_TITLE  = ("Segoe UI", 17, "bold")
FONT_SUB    = ("Segoe UI", 8)
FONT_MONO   = ("Consolas", 9)
FONT_BTN    = ("Segoe UI", 10, "bold")

PERIOD_OPTIONS = [
    ("Qualquer período", ""),
    ("Última hora",      "h"),
    ("Último dia",       "d"),
    ("Última semana",    "w"),
    ("Último mês",       "m"),
    ("Último ano",       "y"),
]


class PrintRedirector:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text.strip():
            self.q.put(text)

    def flush(self):
        pass


class ClippingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Clipping Agent")
        self.root.geometry("740x700")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_APP)

        self.log_queue = queue.Queue()
        self._build_ui()
        self.check_queue()

    # ── Construção ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Cabeçalho ──────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=WHITE, bd=0)
        header.pack(fill="x")

        # faixa azul lateral esquerda
        accent_bar = tk.Frame(header, bg=BLUE_PRI, width=4)
        accent_bar.pack(side="left", fill="y")

        inner_header = tk.Frame(header, bg=WHITE)
        inner_header.pack(side="left", fill="both", expand=True, padx=20, pady=14)

        title_row = tk.Frame(inner_header, bg=WHITE)
        title_row.pack(fill="x")

        tk.Label(title_row, text="Clipping Agent",
                 font=FONT_TITLE, bg=WHITE, fg=TEXT_DARK).pack(side="left")

        badge = tk.Label(title_row, text="  Serper API  ",
                         font=("Segoe UI", 8, "bold"),
                         bg=BLUE_LIGHT, fg=BLUE_PRI,
                         relief="flat", padx=2, pady=2)
        badge.pack(side="left", padx=(10, 0), pady=(4, 0))

        tk.Label(inner_header,
                 text="Monitoramento de menções na web com síntese via Gemini",
                 font=FONT_SUB, bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # separador
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # ── Corpo ──────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG_APP)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Card de configurações
        card = tk.Frame(body, bg=BG_CARD, bd=1, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x")

        card_inner = tk.Frame(card, bg=BG_CARD)
        card_inner.pack(fill="x", padx=20, pady=18)

        # Label da seção
        tk.Label(card_inner, text="CONFIGURAÇÃO DA BUSCA",
                 font=("Segoe UI", 8, "bold"), bg=BG_CARD, fg=BLUE_PRI).pack(anchor="w")
        tk.Frame(card_inner, bg=BORDER, height=1).pack(fill="x", pady=(6, 14))

        # Campo de termo
        tk.Label(card_inner, text="Termo de pesquisa",
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_DARK).pack(anchor="w")
        tk.Label(card_inner, text="Nome da empresa, assunto ou palavra-chave",
                 font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(1, 6))

        entry_frame = tk.Frame(card_inner, bg=BORDER, bd=0,
                               highlightthickness=1, highlightbackground=BORDER)
        entry_frame.pack(fill="x")

        self.term_entry = tk.Entry(
            entry_frame,
            font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_DARK,
            insertbackground=BLUE_PRI, relief="flat", bd=8,
            highlightthickness=0,
        )
        self.term_entry.pack(fill="x")
        self.term_entry.bind("<FocusIn>",  lambda e: entry_frame.config(highlightbackground=BLUE_PRI))
        self.term_entry.bind("<FocusOut>", lambda e: entry_frame.config(highlightbackground=BORDER))
        self._entry_frame = entry_frame

        # Período
        tk.Label(card_inner, text="Período de busca",
                 font=FONT_LABEL, bg=BG_CARD, fg=TEXT_DARK).pack(anchor="w", pady=(16, 0))
        tk.Label(card_inner, text="Filtrar resultados por data de publicação",
                 font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(1, 8))

        self.tbs_var = tk.StringVar(value="")
        pills_frame = tk.Frame(card_inner, bg=BG_CARD)
        pills_frame.pack(anchor="w")

        self._pills = []
        for label, value in PERIOD_OPTIONS:
            pill = tk.Label(
                pills_frame, text=label,
                font=("Segoe UI", 9),
                padx=12, pady=5,
                cursor="hand2",
                relief="flat", bd=0,
            )
            pill.pack(side="left", padx=(0, 6))
            pill.bind("<Button-1>", lambda e, v=value: self._select_period(v))
            self._pills.append((pill, value))

        self._select_period("")  # seleciona "Qualquer período" por padrão

        # Botão
        btn_outer = tk.Frame(body, bg=BG_APP)
        btn_outer.pack(fill="x", pady=(14, 0))

        self.btn_run = tk.Button(
            btn_outer,
            text="Gerar Relatório",
            font=FONT_BTN,
            bg=BLUE_PRI, fg=WHITE,
            activebackground=BLUE_HOV, activeforeground=WHITE,
            relief="flat", bd=0,
            padx=24, pady=10,
            cursor="hand2",
            command=self.start_processing,
        )
        self.btn_run.pack(side="left")

        self.status_label = tk.Label(
            btn_outer, text="Pronto",
            font=("Segoe UI", 9), bg=BG_APP, fg=TEXT_MUTED,
        )
        self.status_label.pack(side="left", padx=14)

        # Card do log
        log_card = tk.Frame(body, bg=BG_CARD, bd=0,
                            highlightthickness=1, highlightbackground=BORDER)
        log_card.pack(fill="both", expand=True, pady=(14, 0))

        log_header = tk.Frame(log_card, bg=BG_CARD)
        log_header.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(log_header, text="LOG DE EXECUÇÃO",
                 font=("Segoe UI", 8, "bold"), bg=BG_CARD, fg=BLUE_PRI).pack(side="left")

        self.log_status = tk.Label(log_header, text="● Aguardando",
                                   font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUTED)
        self.log_status.pack(side="right")

        tk.Frame(log_card, bg=BORDER, height=1).pack(fill="x", padx=0, pady=(8, 0))

        self.log_area = scrolledtext.ScrolledText(
            log_card,
            font=FONT_MONO, bg=BG_LOG, fg=LOG_DEFAULT,
            insertbackground=BLUE_PRI,
            relief="flat", bd=0,
            padx=16, pady=12,
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.log_area.pack(fill="both", expand=True)

        self.log_area.tag_config("ts",      foreground=TEXT_MUTED)
        self.log_area.tag_config("normal",  foreground=LOG_DEFAULT)
        self.log_area.tag_config("info",    foreground=LOG_INFO)
        self.log_area.tag_config("success", foreground=LOG_SUCCESS)
        self.log_area.tag_config("warn",    foreground=LOG_WARN)
        self.log_area.tag_config("error",   foreground=LOG_ERROR)

        self._append_log("Sistema pronto.", "normal")

    # ── Helpers de UI ────────────────────────────────────────────────────────

    def _select_period(self, value):
        self.tbs_var.set(value)
        for pill, v in self._pills:
            if v == value:
                pill.config(bg=BLUE_LIGHT, fg=BLUE_PRI)
            else:
                pill.config(bg=BG_APP, fg=TEXT_MUTED)

    def _append_log(self, text, tag="normal"):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, text + "\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def _classify_tag(self, text):
        lo = text.lower()
        if any(k in lo for k in ("erro", "error", "❌", "fatal", "traceback")):
            return "error"
        if any(k in lo for k in ("✅", "sucesso", "concluí", "gerado", "finalizado")):
            return "success"
        if any(k in lo for k in ("warning", "aviso", "⚠")):
            return "warn"
        if any(k in lo for k in ("buscando", "serper", "conectado", "iniciando", "pipeline", "▸")):
            return "info"
        return "normal"

    def log(self, message):
        self.log_queue.put(message.rstrip())

    def check_queue(self):
        while not self.log_queue.empty():
            text = self.log_queue.get()
            tag = self._classify_tag(text)
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, f"{ts}  ", "ts")
            self.log_area.insert(tk.END, text + "\n", tag)
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(100, self.check_queue)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def start_processing(self):
        term = self.term_entry.get().strip()
        if not term:
            self._entry_frame.config(highlightbackground="#DC2626")
            self.root.after(700, lambda: self._entry_frame.config(highlightbackground=BORDER))
            self.status_label.config(text="Informe o termo de pesquisa", fg=LOG_ERROR)
            return

        self.btn_run.config(state=tk.DISABLED, text="Processando…", bg="#93C5FD")
        self.status_label.config(text="Executando pipeline…", fg=TEXT_MID)
        self.log_status.config(text="● Executando", fg=BLUE_PRI)

        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        tbs = self.tbs_var.get()
        period_label = next(l for l, v in PERIOD_OPTIONS if v == tbs)
        self.log(f"▸ Termo: {term}")
        self.log(f"▸ Período: {period_label}")

        threading.Thread(target=self.run_backend, args=(term, tbs), daemon=True).start()

    def run_backend(self, term, tbs):
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            sys.stdout = PrintRedirector(self.log_queue)
            sys.stderr = sys.stdout

            os.environ["COMPANY_NAME"] = term
            os.environ["SEARCH_TBS"]   = tbs

            for mod in ["main", "services.search_service"]:
                if mod in sys.modules:
                    del sys.modules[mod]

            src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from main import build_orchestrator

            self.log("▸ Backend conectado. Executando pipeline…")
            orchestrator = build_orchestrator(tbs=tbs)
            synthesis = orchestrator.run()

            if synthesis:
                self.log("✅ Relatório gerado com sucesso!")
                self.log("─" * 48)
                self.log("SÍNTESE EXECUTIVA (Gemini):")
                self.log("─" * 48)
                self.log(synthesis)
                self.log("─" * 48)
            else:
                self.log("⚠️  Nenhum conteúdo novo encontrado neste ciclo.")

            self.open_report()

        except Exception as exc:
            self.log(f"❌ ERRO FATAL: {exc}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self.root.after(0, self._reset_button)

    def _reset_button(self):
        self.btn_run.config(state=tk.NORMAL, text="Gerar Relatório", bg=BLUE_PRI)
        self.status_label.config(text="Concluído", fg=LOG_SUCCESS)
        self.log_status.config(text="● Concluído", fg=LOG_SUCCESS)

    def open_report(self):
        report_path = os.getenv("OUTPUT_MD_FILE", os.path.join("data", "clipping_output.md"))
        if os.path.exists(report_path):
            self.log(f"▸ Abrindo relatório: {report_path}")
            if sys.platform == "win32":
                os.startfile(report_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", report_path])
            else:
                subprocess.call(["xdg-open", report_path])
        else:
            self.log("⚠️  Arquivo de relatório não encontrado.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    root = tk.Tk()
    app = ClippingGUI(root)
    root.mainloop()