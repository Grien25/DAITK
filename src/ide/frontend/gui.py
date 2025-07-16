#!/usr/bin/env python3
"""Stage 1 GUI.

The interface guides the user through the first setup steps:

1. Selecting a Wii ISO and extracting it using ``wwt`` to
   ``Documents/DAITK-Data/dtk-template/orig/GAMEID``.
2. Optionally renaming ``GAMEID`` throughout the template once the
   extraction succeeds.

It can still run ``stage1.py`` to generate ``asm/`` and ``orig_obj/``
using ``decomp-toolkit``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

ROOT = Path(__file__).resolve().parents[2]
# User data lives outside the repository in Documents/DAITK-Data
DATA_ROOT = Path.home() / "Documents" / "DAITK-Data"
TEMPLATE_SRC = ROOT / "tools" / "dtk-template"
TEMPLATE = DATA_ROOT / "dtk-template"
WBFS_DIR = TEMPLATE / "WBFS"
ORIG_DIR = TEMPLATE / "orig" / "GAMEID"
STAGE1 = ROOT / "src" / "scripts" / "stage1.py"


def ensure_template() -> None:
    """Copy the dtk-template tools to the user's data directory if needed."""
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE.exists():
        shutil.copytree(TEMPLATE_SRC, TEMPLATE)


def rename_gameid(root: Path, new_id: str) -> None:
    """Replace GAMEID placeholder with ``new_id`` throughout the template."""
    placeholder = "GAMEID"

    for path in root.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if placeholder in text:
                path.write_text(text.replace(placeholder, new_id))

    # rename files and directories containing the placeholder
    for path in sorted(root.rglob("*GAMEID*"), key=lambda p: -len(str(p))):
        if placeholder in path.name and path.exists():
            path.rename(path.with_name(path.name.replace(placeholder, new_id)))

class Stage1GUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        ensure_template()
        self.title("Stage 1 Launcher")
        self.geometry("450x250")

        self.iso_path = tk.StringVar()
        self.game_id = tk.StringVar()
        self.dtk_path = tk.StringVar(value="dtk")
        self.status = tk.StringVar()

        tk.Label(self, text="Game ISO:").pack(anchor="w", padx=10, pady=5)
        iso_frame = tk.Frame(self)
        iso_frame.pack(fill="x", padx=10)
        tk.Entry(iso_frame, textvariable=self.iso_path).pack(side="left", fill="x", expand=True)
        tk.Button(iso_frame, text="Browse", command=self.select_iso).pack(side="left", padx=5)

        tk.Button(self, text="Extract ISO", command=self.extract_iso).pack(pady=5)

        rename_frame = tk.Frame(self)
        rename_frame.pack(pady=5)
        tk.Label(rename_frame, text="Game ID:").pack(side="left")
        tk.Entry(rename_frame, textvariable=self.game_id, width=10).pack(side="left")
        self.rename_btn = tk.Button(rename_frame, text="Rename GameID", command=self.rename_gameid, state="disabled")
        self.rename_btn.pack(side="left", padx=5)

        tk.Button(self, text="Run Stage 1", command=self.run_stage1).pack(pady=5)

        tk.Label(self, textvariable=self.status, fg="blue").pack(padx=10)

    def select_iso(self) -> None:
        path = filedialog.askopenfilename(title="Select Wii ISO or WBFS", filetypes=[("Wii ISO/WBFS", "*.iso *.wbfs"), ("All files", "*")])
        if path:
            self.iso_path.set(path)

    def extract_iso(self) -> None:
        iso = Path(self.iso_path.get())
        if not iso.is_file():
            messagebox.showerror("Error", "Invalid ISO/WBFS path")
            return
        WBFS_DIR.mkdir(parents=True, exist_ok=True)
        dest_iso = WBFS_DIR / iso.name
        try:
            shutil.copy2(iso, dest_iso)
        except OSError as exc:
            messagebox.showerror("Copy failed", str(exc))
            return
        ORIG_DIR.mkdir(parents=True, exist_ok=True)
        if dest_iso.suffix.lower() == ".wbfs":
            # Extract the full filesystem (main.dol, .rel, etc. will be present in output)
            cmd = ["wit", "extract", "--overwrite", str(dest_iso), str(ORIG_DIR)]
        else:
            cmd = ["wwt", "extract", str(dest_iso), "--dest", str(ORIG_DIR)]
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            messagebox.showerror("Tool not found", "Install Wiimms ISO Tools and ensure 'wit' and 'wwt' are in PATH")
            return
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("Extraction failed", str(exc))
            return

        if any(ORIG_DIR.iterdir()):
            self.status.set("Extraction complete")
            self.rename_btn.config(state="normal")
        else:
            self.status.set("Extraction produced no files")

    def rename_gameid(self) -> None:
        new_id = self.game_id.get().strip().upper()
        if not new_id:
            messagebox.showerror("Error", "Enter a Game ID")
            return
        try:
            rename_gameid(TEMPLATE, new_id)
        except Exception as exc:
            messagebox.showerror("Rename failed", str(exc))
            return
        self.status.set(f"Renamed to {new_id}")

    def run_stage1(self) -> None:
        cmd = ["python3", str(STAGE1), str(ORIG_DIR / "sys" / "main.dol"), "--dtk", self.dtk_path.get()]
        try:
            subprocess.run(cmd, check=True)
            self.status.set("Stage 1 completed")
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("Stage 1 failed", str(exc))


if __name__ == "__main__":
    Stage1GUI().mainloop()
