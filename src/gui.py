"""
gui.py — Interface gráfica do Clipping Agent
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import os
import sys
import subprocess
import queue
from datetime import datetime

# ── Paleta ────────────────────────────────────────────────────────────────────
BG_DARK    = "#0d0f14"
BG_PANEL   = "#13161e"
BG_INPUT   = "#1a1d27"
BG_BORDER  = "#252836"
ACCENT     = "#f0a500"
ACCENT_DIM = "#7a5200"
FG_PRIMARY = "#e8e8e8"
FG_MUTED   = "#6b7280"
FG_GREEN   = "#4ade80"
FG_RED     = "#f87171"
FG_BLUE    = "#60a5fa"
FG_LOG     = "#a8b5c8"
FONT_MONO  = ("Courier New", 10)
FONT_LABEL = ("Courier New", 9, "bold")
FONT_TITLE = ("Courier New", 18, "bold")
FONT_BTN   = ("Courier New", 11, "bold")

# Opções de período — label → valor tbs (vazio = qualquer período)
PERIOD_OPTIONS = [
    ("Qualquer período", ""),
    ("Última hora",      "h"),
    ("Último dia",       "d"),
    ("Última semana",    "w"),
    ("Último mês",       "m"),
    ("Último ano",       "y"),
]


class PrintRedirector:
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def write(self, text):
        if text.strip():
            self.log_queue.put(text)

    def flush(self):
        pass


class ClippingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CLIPPING AGENT")
        self.root.geometry("720x680")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self.log_queue = queue.Queue()
        self._build_ui()
        self.check_queue()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Cabeçalho
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=24, pady=(22, 0))
        tk.Label(header, text="▸ CLIPPING", font=FONT_TITLE, bg=BG_DARK, fg=ACCENT).pack(side="left")
        tk.Label(header, text="AGENT",      font=FONT_TITLE, bg=BG_DARK, fg=FG_PRIMARY).pack(side="left", padx=(4, 0))
        tk.Label(header, text=f"v3.0  //  Serper API  //  {datetime.now().year}",
                 font=("Courier New", 8), bg=BG_DARK, fg=FG_MUTED).pack(side="right", pady=(8, 0))

        self._divider()

        # Painel de inputs
        panel = tk.Frame(self.root, bg=BG_PANEL)
        panel.pack(fill="x", padx=24, pady=4)

        # Termo
        self._label(panel, "TERMO DE PESQUISA")
        self.term_entry = self._entry(panel, width=66)
        self.term_entry.pack(padx=14, pady=(0, 10))

        # Período
        period_row = tk.Frame(panel, bg=BG_PANEL)
        period_row.pack(fill="x", padx=14, pady=(0, 14))

        self._label(period_row, "PERÍODO DE BUSCA", inline=True)

        # Frame dos botões de rádio
        radio_frame = tk.Frame(period_row, bg=BG_PANEL)
        radio_frame.pack(anchor="w", pady=(4, 0))

        self.tbs_var = tk.StringVar(value="")  # vazio = qualquer período

        for label, value in PERIOD_OPTIONS:
            rb = tk.Radiobutton(
                radio_frame,
                text=label,
                variable=self.tbs_var,
                value=value,
                font=("Courier New", 9),
                bg=BG_PANEL, fg=FG_PRIMARY,
                selectcolor=BG_INPUT,
                activebackground=BG_PANEL,
                activeforeground=ACCENT,
                indicatoron=0,                  # botão estilo "pill"
                bd=0,
                padx=10, pady=5,
                relief="flat",
                cursor="hand2",
                command=lambda: self._refresh_radio_colors(),
            )
            rb.pack(side="left", padx=(0, 6))

        self._radio_buttons = radio_frame.winfo_children()
        self._refresh_radio_colors()

        self._divider()

        # Botão
        btn_frame = tk.Frame(self.root, bg=BG_DARK)
        btn_frame.pack(pady=10)
        self.btn_run = tk.Button(
            btn_frame, text="▶  GERAR RELATÓRIO",
            font=FONT_BTN, bg=ACCENT, fg=BG_DARK,
            activebackground=ACCENT_DIM, activeforeground=FG_PRIMARY,
            bd=0, padx=28, pady=10, cursor="hand2",
            command=self.start_processing,
        )
        self.btn_run.pack()

        # Status
        self._divider()
        status_bar = tk.Frame(self.root, bg=BG_DARK)
        status_bar.pack(fill="x", padx=24, pady=(0, 4))
        tk.Label(status_bar, text="OUTPUT  //  PIPELINE LOG",
                 font=("Courier New", 8, "bold"), bg=BG_DARK, fg=FG_MUTED).pack(side="left")
        self.status_dot = tk.Label(status_bar, text="●  IDLE",
                                   font=("Courier New", 8, "bold"), bg=BG_DARK, fg=FG_MUTED)
        self.status_dot.pack(side="right")

        # Log
        log_frame = tk.Frame(self.root, bg=BG_BORDER, bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            font=FONT_MONO, bg=BG_DARK, fg=FG_LOG,
            insertbackground=ACCENT, selectbackground=ACCENT_DIM,
            bd=0, padx=14, pady=12,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self.log_area.pack(fill="both", expand=True)

        self.log_area.tag_config("accent",  foreground=ACCENT)
        self.log_area.tag_config("success", foreground=FG_GREEN)
        self.log_area.tag_config("error",   foreground=FG_RED)
        self.log_area.tag_config("info",    foreground=FG_BLUE)
        self.log_area.tag_config("muted",   foreground=FG_MUTED)
        self.log_area.tag_config("normal",  foreground=FG_LOG)

        self._append_log("Sistema pronto. Configure os parâmetros e clique em Gerar Relatório.\n", "muted")

    def _divider(self):
        tk.Frame(self.root, bg=BG_BORDER, height=1).pack(fill="x", padx=24, pady=6)

    def _label(self, parent, text, inline=False):
        lbl = tk.Label(parent, text=text, font=FONT_LABEL,
                       bg=parent.cget("bg"), fg=ACCENT)
        lbl.pack(anchor="w", padx=14 if not inline else 0, pady=(8, 2))

    def _entry(self, parent, width=66):
        return tk.Entry(
            parent, font=FONT_MONO, width=width,
            bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=ACCENT,
            relief="flat", bd=0,
            highlightthickness=1,
            highlightcolor=ACCENT,
            highlightbackground=BG_BORDER,
        )

    def _refresh_radio_colors(self):
        selected = self.tbs_var.get()
        for rb in self._radio_buttons:
            val = rb.cget("value")
            if val == selected:
                rb.config(bg=ACCENT, fg=BG_DARK)
            else:
                rb.config(bg=BG_INPUT, fg=FG_MUTED)

    # ── Log ───────────────────────────────────────────────────────────────────

    def _append_log(self, text, tag="normal"):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, text, tag)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def _classify_tag(self, text):
        lo = text.lower()
        if any(k in lo for k in ("erro", "error", "❌", "fatal", "traceback")):
            return "error"
        if any(k in lo for k in ("✅", "sucesso", "concluí", "gerado", "finalizado")):
            return "success"
        if any(k in lo for k in ("[info]", "iniciando", "buscando", "conectado", "▸", "serper")):
            return "info"
        if any(k in lo for k in ("warning", "aviso", "⚠")):
            return "accent"
        return "normal"

    def log(self, message):
        self.log_queue.put(message if message.endswith("\n") else message + "\n")

    def check_queue(self):
        while not self.log_queue.empty():
            text = self.log_queue.get()
            tag = self._classify_tag(text)
            ts = datetime.now().strftime("%H:%M:%S")
            self._append_log(f"[{ts}] ", "muted")
            self._append_log(text, tag)
        self.root.after(100, self.check_queue)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def start_processing(self):
        term = self.term_entry.get().strip()
        if not term:
            self.term_entry.config(highlightbackground=FG_RED, highlightcolor=FG_RED)
            self.root.after(600, lambda: self.term_entry.config(
                highlightbackground=BG_BORDER, highlightcolor=ACCENT))
            return

        self.btn_run.config(state=tk.DISABLED, text="⏳  PROCESSANDO...")
        self.status_dot.config(text="●  RUNNING", fg=ACCENT)

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

            # Garante reimport com env atualizado
            for mod in ["main", "services.search_service"]:
                if mod in sys.modules:
                    del sys.modules[mod]

            src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from main import build_orchestrator

            self.log("▸ Backend conectado. Executando pipeline...\n")
            orchestrator = build_orchestrator(tbs=tbs)
            synthesis = orchestrator.run()

            if synthesis:
                self.log("\n✅ Relatório gerado com sucesso!")
                self.log(f"\n{'─' * 50}")
                self.log("SÍNTESE EXECUTIVA (Gemini):")
                self.log(f"{'─' * 50}")
                self.log(synthesis)
                self.log(f"{'─' * 50}\n")
            else:
                self.log("⚠️  Nenhum conteúdo novo encontrado neste ciclo.")

            self.open_report()

        except Exception as e:
            self.log(f"\n❌ ERRO FATAL: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self.root.after(0, self._reset_button)

    def _reset_button(self):
        self.btn_run.config(state=tk.NORMAL, text="▶  GERAR RELATÓRIO")
        self.status_dot.config(text="●  IDLE", fg=FG_MUTED)

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