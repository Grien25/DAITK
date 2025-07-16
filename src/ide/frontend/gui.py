#!/usr/bin/env python3
"""Simple Stage 1 GUI.

This Tkinter-based interface lets users run the Stage 1 disassembly
process from the GUI. It wraps ``stage1.py`` to invoke decomp-toolkit
on a chosen binary and shows status output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

ROOT = Path(__file__).resolve().parents[2]
STAGE1 = ROOT / "src" / "scripts" / "stage1.py"

class Stage1GUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Stage 1 Launcher")
        self.geometry("400x200")

        self.binary_path = tk.StringVar()
        self.dtk_path = tk.StringVar(value="dtk")
        self.output = tk.StringVar()

        tk.Label(self, text="Game Binary:").pack(anchor="w", padx=10, pady=5)
        frm = tk.Frame(self)
        frm.pack(fill="x", padx=10)
        tk.Entry(frm, textvariable=self.binary_path).pack(side="left", fill="x", expand=True)
        tk.Button(frm, text="Browse", command=self.select_binary).pack(side="left", padx=5)

        tk.Label(self, text="decomp-toolkit path:").pack(anchor="w", padx=10, pady=5)
        tk.Entry(self, textvariable=self.dtk_path).pack(fill="x", padx=10)

        tk.Button(self, text="Run Stage 1", command=self.run_stage1).pack(pady=10)
        tk.Label(self, textvariable=self.output, fg="blue").pack(padx=10)

    def select_binary(self) -> None:
        path = filedialog.askopenfilename(title="Select DOL/ELF")
        if path:
            self.binary_path.set(path)

    def run_stage1(self) -> None:
        binary = self.binary_path.get()
        if not binary:
            messagebox.showerror("Error", "No binary selected")
            return
        cmd = [
            "python3",
            str(STAGE1),
            binary,
            "--dtk",
            self.dtk_path.get(),
        ]
        try:
            subprocess.run(cmd, check=True)
            self.output.set("Stage 1 completed")
        except subprocess.CalledProcessError as exc:
            self.output.set(f"Error: {exc}")
            messagebox.showerror("Stage 1 failed", str(exc))


if __name__ == "__main__":
    Stage1GUI().mainloop()
