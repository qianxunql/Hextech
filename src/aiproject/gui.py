from __future__ import annotations

import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk

from aiproject.main import run


BG = "#ffffff"
PANEL = "#f3f3f3"
TEXT = "#151515"
MUTED = "#8b8b8b"
ACCENT = "#111111"


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        if (bundle_dir / "data").exists():
            return bundle_dir
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


class HextechAssistantApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        os.chdir(app_dir())
        os.environ.setdefault("AI_MODEL_PROVIDER", "ollama")
        os.environ.setdefault("OLLAMA_MODEL", "qwen3:4b")

        self.queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.is_generating = False

        self.title("Hextech")
        self.geometry("1190x900")
        self.minsize(860, 680)
        self.configure(bg=BG)

        self._build_style()
        self._build_header()
        self._build_body()
        self._build_prompt()
        self.after(120, self._poll_queue)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Model.TCombobox",
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground=TEXT,
            borderwidth=0,
            arrowsize=14,
            padding=(14, 8),
        )

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=BG, height=54)
        header.pack(fill="x")

        brand = tk.Label(
            header,
            text="⬡  Hextech",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 12),
        )
        brand.pack(side="left", padx=10, pady=10)

        left_tools = tk.Frame(self, bg=BG)
        left_tools.place(x=28, y=64)
        for label in ("☰", "✎"):
            tk.Button(
                left_tools,
                text=label,
                bg=BG,
                fg="#777777",
                activebackground=BG,
                activeforeground=TEXT,
                borderwidth=0,
                font=("Segoe UI Symbol", 22),
                cursor="hand2",
            ).pack(side="left", padx=(0, 24))

    def _build_body(self) -> None:
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=48, pady=(24, 0))

        self.answer = tk.Text(
            self.body,
            bg=BG,
            fg=TEXT,
            relief="flat",
            borderwidth=0,
            wrap="word",
            font=("Microsoft YaHei UI", 13),
            padx=18,
            pady=18,
            state="disabled",
            insertbackground=TEXT,
        )
        self.answer.pack(fill="both", expand=True)

        self.answer.tag_configure("user", foreground=TEXT, spacing1=12, spacing3=8)
        self.answer.tag_configure("assistant", foreground="#303030", spacing1=8, spacing3=18)
        self.answer.tag_configure("hint", foreground=MUTED, justify="center", font=("Segoe UI", 18))

        self._append("hint", "\n\n\n\n\n\n⬡\n\n")

    def _build_prompt(self) -> None:
        prompt_outer = tk.Frame(self, bg=BG)
        prompt_outer.pack(fill="x", padx=48, pady=(10, 48))

        prompt = tk.Frame(prompt_outer, bg=PANEL, height=146)
        prompt.pack(fill="x")
        prompt.pack_propagate(False)

        self.input = tk.Text(
            prompt,
            bg=PANEL,
            fg=TEXT,
            relief="flat",
            borderwidth=0,
            height=3,
            wrap="word",
            font=("Microsoft YaHei UI", 16),
            insertbackground=TEXT,
            padx=30,
            pady=25,
        )
        self.input.pack(side="left", fill="both", expand=True)
        self.input.insert("1.0", "海克斯大乱斗里亚索适合拿什么强化？")
        self.input.bind("<Return>", self._on_return)
        self.input.bind("<Shift-Return>", lambda _event: None)

        controls = tk.Frame(prompt, bg=PANEL)
        controls.pack(side="right", padx=16, pady=28)

        self._round_button(controls, "+", self._focus_input).pack(side="left", padx=6)
        self._round_button(controls, "◎", self._focus_input).pack(side="left", padx=6)

        self.model = ttk.Combobox(
            controls,
            style="Model.TCombobox",
            values=["qwen3:4b"],
            width=11,
            state="readonly",
            font=("Segoe UI", 15),
        )
        self.model.set("qwen3:4b")
        self.model.pack(side="left", padx=8, ipady=10)

        self.send_button = self._round_button(controls, "↑", self._submit, large=True)
        self.send_button.pack(side="left", padx=(8, 0))

    def _round_button(
        self,
        parent: tk.Widget,
        label: str,
        command,
        large: bool = False,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=label,
            command=command,
            bg="#ffffff" if not large else "#dddddd",
            fg="#777777",
            activebackground="#eeeeee",
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            width=3 if large else 2,
            height=1,
            font=("Segoe UI Symbol", 22 if large else 20),
            cursor="hand2",
        )

    def _focus_input(self) -> None:
        self.input.focus_set()

    def _on_return(self, event: tk.Event) -> str | None:
        if event.state & 0x0001:
            return None
        self._submit()
        return "break"

    def _submit(self) -> None:
        if self.is_generating:
            return

        question = self.input.get("1.0", "end").strip()
        if not question:
            return

        self.input.delete("1.0", "end")
        self._clear_hint()
        self._append("user", f"你：{question}\n")
        self._append("assistant", "助手：正在检索知识库并思考...\n")
        self.is_generating = True
        self.send_button.configure(state="disabled")

        thread = threading.Thread(target=self._ask_worker, args=(question,), daemon=True)
        thread.start()

    def _ask_worker(self, question: str) -> None:
        try:
            answer = run(question)
        except Exception as exc:  # noqa: BLE001 - show GUI-friendly error
            answer = f"出错了：{exc}"
        self.queue.put(("answer", answer))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "answer":
                    self._replace_last_assistant(payload)
                    self.is_generating = False
                    self.send_button.configure(state="normal")
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _append(self, tag: str, text: str) -> None:
        self.answer.configure(state="normal")
        self.answer.insert("end", text, tag)
        self.answer.see("end")
        self.answer.configure(state="disabled")

    def _clear_hint(self) -> None:
        self.answer.configure(state="normal")
        content = self.answer.get("1.0", "end").strip()
        if content == "⬡":
            self.answer.delete("1.0", "end")
        self.answer.configure(state="disabled")

    def _replace_last_assistant(self, text: str) -> None:
        self.answer.configure(state="normal")
        content = self.answer.get("1.0", "end-1c")
        marker = "助手：正在检索知识库并思考...\n"
        index = content.rfind(marker)
        if index >= 0:
            start = f"1.0+{index}c"
            end = f"1.0+{index + len(marker)}c"
            self.answer.delete(start, end)
            self.answer.insert(start, f"助手：{text}\n\n", "assistant")
        else:
            self.answer.insert("end", f"助手：{text}\n\n", "assistant")
        self.answer.see("end")
        self.answer.configure(state="disabled")


def main() -> None:
    app = HextechAssistantApp()
    app.mainloop()


if __name__ == "__main__":
    main()
