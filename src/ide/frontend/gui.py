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
import sys
import os
import hashlib
import threading
from pathlib import Path
import shutil
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, Text, Menu

ROOT = Path(__file__).resolve().parents[2]
# User data lives outside the repository in Documents/DAITK-Data
DATA_ROOT = Path.home() / "Documents" / "DAITK-Data"
TEMPLATE_SRC = ROOT / "tools" / "dtk-template"
TEMPLATE = DATA_ROOT / "dtk-template"
WBFS_DIR = TEMPLATE / "WBFS"
ORIG_DIR = TEMPLATE / "orig" / "GAMEID"
STAGE1 = ROOT / "src" / "scripts" / "stage1.py"
CONFIGURE = TEMPLATE / "configure.py"


def open_file(path: Path) -> None:
    """Open *path* in a reasonable editor.

    The function prefers ``$EDITOR`` if set, otherwise tries common
    editors like VS Code or Wordpad so that files such as ``build.sha1``
    open even when no default application is registered.  This avoids
    the "no application knows how to open" error on macOS.
    """

    cmd: list[str] | None = None

    # Honour any explicit editor choice from the environment first
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        cmd = editor.split() + [str(path)]
    elif shutil.which("code"):
        cmd = ["code", str(path)]
    elif sys.platform.startswith("win"):
        # Wordpad ("write") is available on all Windows systems; fall back
        # to notepad if it fails
        cmd = ["write", str(path)] if shutil.which("write") else ["notepad", str(path)]
    elif sys.platform == "darwin":
        # Use TextEdit via ``open -a`` so files without a default handler open
        cmd = ["open", "-a", "TextEdit", str(path)]
    else:
        cmd = ["xdg-open", str(path)]

    try:
        subprocess.Popen(cmd)
    except Exception as exc:
        Messagebox.show_error("Open failed", str(exc))


def sha1sum(path: Path) -> str:
    """Return the SHA-1 hex digest of the given file."""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


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


class MiniIDE(ttk.Toplevel):
    """Minimal IDE window with a VSCode-style layout."""

    def __init__(self, master: ttk.Window, root_dir: Path = TEMPLATE) -> None:
        super().__init__(master)
        self.title("DAITK IDE")
        self.geometry("950x600")

        self.root_dir = root_dir

        paned = ttk.PanedWindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=YES)

        sidebar = ttk.Frame(paned, width=200)
        paned.add(sidebar, weight=0)

        self.tree = ttk.Treeview(sidebar, show="tree")
        self.tree.pack(fill=BOTH, expand=YES)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.tree.bind("<Double-1>", self.on_tree_double)

        self.notebook = ttk.Notebook(paned)
        paned.add(self.notebook, weight=1)

        self.tabs: dict[Path, tuple[ttk.Frame, Text]] = {}

        menubar = Menu(self)
        file_menu = Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open…", command=self.open_dialog)
        file_menu.add_command(label="Save", command=self.save_current)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        self.populate_root()

    def populate_root(self) -> None:
        self.tree.delete(*self.tree.get_children(""))
        node = self.tree.insert("", "end", iid=str(self.root_dir), text=self.root_dir.name, open=True)
        self.populate_tree(node, self.root_dir)

    def populate_tree(self, parent: str, path: Path) -> None:
        for child in sorted(path.iterdir()):
            iid = str(child)
            if child.is_dir():
                node = self.tree.insert(parent, "end", iid=iid, text=child.name)
                # placeholder child for expandable indicator
                if any(child.iterdir()):
                    self.tree.insert(node, "end")
            else:
                self.tree.insert(parent, "end", iid=iid, text=child.name)

    def on_tree_open(self, event: object) -> None:
        node = self.tree.focus()
        path = Path(node)
        # populate directory if not yet expanded
        children = self.tree.get_children(node)
        if len(children) == 1 and not self.tree.item(children[0], "text"):
            self.tree.delete(children[0])
            self.populate_tree(node, path)

    def on_tree_double(self, event: object) -> None:
        item = self.tree.focus()
        path = Path(item)
        if path.is_file():
            self.open_file(path)

    def open_dialog(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self.open_file(Path(path))

    def open_file(self, path: Path) -> None:
        if path in self.tabs:
            frame, _ = self.tabs[path]
            self.notebook.select(frame)
            return

        frame = ttk.Frame(self.notebook)
        text = Text(frame, wrap="none", undo=True)
        text.pack(fill=BOTH, expand=YES)

        try:
            text.insert("1.0", path.read_text())
        except Exception as exc:
            Messagebox.show_error("Open failed", str(exc))
            return

        self.notebook.add(frame, text=path.name)
        self.tabs[path] = (frame, text)
        self.notebook.select(frame)

    def save_current(self) -> None:
        current = self.notebook.select()
        if not current:
            return
        frame = self.notebook.nametowidget(current)
        for path, (fr, text) in self.tabs.items():
            if fr == frame:
                try:
                    path.write_text(text.get("1.0", "end-1c"))
                    self.title(f"DAITK IDE – {path.name} saved")
                except Exception as exc:
                    Messagebox.show_error("Save failed", str(exc))

class Stage1GUI(ttk.Window):
    def __init__(self) -> None:
        super().__init__(title="Stage 1 Launcher", themename="darkly", size=(500, 320))
        ensure_template()

        self.iso_path = ttk.StringVar()
        self.game_id = ttk.StringVar()
        self.dtk_path = ttk.StringVar(value="dtk")
        self.status = ttk.StringVar()
        self.ide: MiniIDE | None = None

        container = ttk.Frame(self, padding=15)
        container.pack(fill=BOTH, expand=YES)
        container.columnconfigure(1, weight=1)

        ttk.Label(container, text="Game ISO:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Entry(container, textvariable=self.iso_path).grid(row=0, column=1, sticky=EW, padx=(0, 5))
        ttk.Button(container, text="Browse", command=self.select_iso, bootstyle="secondary").grid(row=0, column=2)

        ttk.Button(container, text="Extract ISO", command=self.extract_iso, bootstyle="success")\
            .grid(row=1, column=0, columnspan=3, pady=10)

        ttk.Label(container, text="Game ID:").grid(row=2, column=0, sticky=W)
        ttk.Entry(container, textvariable=self.game_id, width=10).grid(row=2, column=1, sticky=W, padx=(0, 5))
        self.rename_btn = ttk.Button(container, text="Rename GameID", command=self.rename_gameid,
                                     state=DISABLED, bootstyle="secondary")
        self.rename_btn.grid(row=2, column=2)

        ttk.Button(container, text="Run Stage 1", command=self.run_stage1, bootstyle="primary")\
            .grid(row=3, column=0, columnspan=3, pady=10)

        edit_frame = ttk.Frame(container)
        edit_frame.grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(edit_frame, text="Edit config.yml", command=self.edit_config, bootstyle="light")\
            .pack(side=LEFT, padx=5)
        ttk.Button(edit_frame, text="Edit build.sha1", command=self.edit_sha1, bootstyle="light")\
            .pack(side=LEFT, padx=5)
        ttk.Button(edit_frame, text="Edit configure.py", command=self.edit_configure, bootstyle="light")\
            .pack(side=LEFT, padx=5)
        ttk.Button(container, text="Open IDE", command=self.show_ide, bootstyle="secondary")\
            .grid(row=5, column=0, columnspan=3)

        ttk.Button(container, text="Run configure.py", command=self.run_configure, bootstyle="primary")\
            .grid(row=6, column=0, columnspan=3, pady=10)

        ttk.Label(container, textvariable=self.status, foreground="cyan")\
            .grid(row=7, column=0, columnspan=3, sticky=W)

    def select_iso(self) -> None:
        path = filedialog.askopenfilename(title="Select Wii ISO or WBFS", filetypes=[("Wii ISO/WBFS", "*.iso *.wbfs"), ("All files", "*")])
        if path:
            self.iso_path.set(path)

    def extract_iso(self) -> None:
        """Extract the selected ISO in a background thread.

        Heavy operations like file copying and invoking Wiimms tools can block
        the Tk event loop. By running them in ``threading.Thread`` we keep the
        UI responsive. All widget updates are scheduled back on the main thread
        using ``self.after``.
        """

        iso = Path(self.iso_path.get())
        if not iso.is_file():
            Messagebox.show_error("Error", "Invalid ISO/WBFS path")
            return

        self.status.set("Extracting…")
        self.rename_btn.config(state="disabled")

        def task() -> None:
            WBFS_DIR.mkdir(parents=True, exist_ok=True)
            dest_iso = WBFS_DIR / iso.name
            try:
                shutil.copy2(iso, dest_iso)
            except OSError as exc:
                self.after(0, lambda: Messagebox.show_error("Copy failed", str(exc)))
                return

            ORIG_DIR.mkdir(parents=True, exist_ok=True)
            if dest_iso.suffix.lower() == ".wbfs":
                cmd = ["wit", "extract", "--overwrite", str(dest_iso), str(ORIG_DIR)]
            else:
                cmd = ["wwt", "extract", str(dest_iso), "--dest", str(ORIG_DIR)]

            try:
                subprocess.run(cmd, check=True)
            except FileNotFoundError:
                self.after(0, lambda: Messagebox.show_error(
                    "Tool not found",
                    "Install Wiimms ISO Tools and ensure 'wit' and 'wwt' are in PATH",
                ))
                return
            except subprocess.CalledProcessError as exc:
                self.after(0, lambda: Messagebox.show_error("Extraction failed", str(exc)))
                return

            sha1 = None
            if any(ORIG_DIR.iterdir()):
                main_dol = ORIG_DIR / "sys" / "main.dol"
                if main_dol.exists():
                    sha1 = sha1sum(main_dol)

            def finish() -> None:
                if sha1:
                    self.status.set(f"Extraction complete\nmain.dol sha1: {sha1}")
                elif any(ORIG_DIR.iterdir()):
                    self.status.set("Extraction complete")
                else:
                    self.status.set("Extraction produced no files")
                self.rename_btn.config(state="normal")

            self.after(0, finish)

        threading.Thread(target=task, daemon=True).start()

    def show_ide(self) -> None:
        if self.ide is None or not self.ide.winfo_exists():
            self.ide = MiniIDE(self, TEMPLATE)
        else:
            self.ide.deiconify()
            self.ide.lift()

    def rename_gameid(self) -> None:
        new_id = self.game_id.get().strip().upper()
        if not new_id:
            Messagebox.show_error("Error", "Enter a Game ID")
            return

        self.status.set("Renaming…")

        def task() -> None:
            try:
                rename_gameid(TEMPLATE, new_id)
            except Exception as exc:
                self.after(0, lambda: Messagebox.show_error("Rename failed", str(exc)))
                return
            self.after(0, lambda: self.status.set(f"Renamed to {new_id}"))

        threading.Thread(target=task, daemon=True).start()

    def run_stage1(self) -> None:
        game_id = self.game_id.get().strip().upper() or "GAMEID"
        binary = TEMPLATE / "orig" / game_id / "sys" / "main.dol"
        cmd = [
            "python3",
            str(STAGE1),
            str(binary),
            "--dtk",
            self.dtk_path.get(),
        ]

        self.status.set("Running Stage 1…")

        def task() -> None:
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as exc:
                self.after(0, lambda: Messagebox.show_error("Stage 1 failed", str(exc)))
                return
            self.after(0, lambda: self.status.set("Stage 1 completed"))

        threading.Thread(target=task, daemon=True).start()

    def edit_config(self) -> None:
        game_id = self.game_id.get().strip().upper() or "GAMEID"
        path = TEMPLATE / "config" / game_id / "config.yml"
        if os.environ.get("EDITOR") or os.environ.get("VISUAL"):
            open_file(path)
        else:
            self.show_ide()
            if self.ide:
                self.ide.open_file(path)

    def edit_sha1(self) -> None:
        game_id = self.game_id.get().strip().upper() or "GAMEID"
        path = TEMPLATE / "config" / game_id / "build.sha1"
        if os.environ.get("EDITOR") or os.environ.get("VISUAL"):
            open_file(path)
        else:
            self.show_ide()
            if self.ide:
                self.ide.open_file(path)

    def edit_configure(self) -> None:
        if os.environ.get("EDITOR") or os.environ.get("VISUAL"):
            open_file(CONFIGURE)
        else:
            self.show_ide()
            if self.ide:
                self.ide.open_file(CONFIGURE)

    def run_configure(self) -> None:
        game_id = self.game_id.get().strip().upper() or "GAMEID"
        try:
            subprocess.run([
                "python3",
                str(CONFIGURE),
                "--version",
                game_id,
            ], cwd=TEMPLATE, check=True)
            self.status.set("configure.py completed")
        except subprocess.CalledProcessError as exc:
            Messagebox.show_error("configure.py failed", str(exc))


if __name__ == "__main__":
    Stage1GUI().mainloop()
