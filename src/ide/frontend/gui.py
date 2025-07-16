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
from tkinter import filedialog, Text, Menu, Listbox, END, ACTIVE, Toplevel

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


def update_build_sha1(game_id: str = "GAMEID") -> None:
    """Regenerate ``build.sha1`` for *game_id* based on extracted binaries."""
    orig = TEMPLATE / "orig" / game_id
    build_sha = TEMPLATE / "config" / game_id / "build.sha1"
    if not orig.exists():
        return

    lines: list[str] = []

    main_dol = orig / "sys" / "main.dol"
    if main_dol.exists():
        lines.append(f"{sha1sum(main_dol)}  build/{game_id}/main.dol")

    files = orig / "files"
    if files.exists():
        for rel in sorted(files.glob("*.rel")):
            mod = rel.stem
            lines.append(f"{sha1sum(rel)}  build/{game_id}/{mod}/{mod}.rel")

    if lines:
        build_sha.parent.mkdir(parents=True, exist_ok=True)
        build_sha.write_text("\n".join(lines) + "\n")


class Sidebar(ttk.Frame):
    """Vertical sidebar with simple icon buttons."""

    def __init__(self, master, callback) -> None:
        super().__init__(master, width=40, padding=5, style="secondary.TFrame")
        self.pack_propagate(False)
        self.callback = callback
        items = [
            ("Explorer", "🗂"),
            ("Search", "🔍"),
            ("Source Control", "🌿"),
        ]
        for name, icon in items:
            btn = ttk.Button(
                self,
                text=icon,
                width=3,
                bootstyle="toolbutton",
                command=lambda n=name: self.callback(n),
            )
            btn.pack(pady=5)


class EditorTabs(ttk.Frame):
    """Tabbed editor with close buttons."""

    def __init__(self, master) -> None:
        super().__init__(master)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=YES)
        self.notebook.bind("<Button-1>", self.on_click)
        self.tabs: dict[Path, dict[str, object]] = {}

    def on_click(self, event: object) -> None:
        index = self.notebook.index(f"@{event.x},{event.y}")
        if index < 0:
            return
        bbox = self.notebook.bbox(index)
        if bbox and event.x > bbox[2] - 20:
            tab_id = self.notebook.tabs()[index]
            self.close_tab(tab_id)

    def open_file(self, path: Path) -> None:
        path = Path(path)
        if path in self.tabs:
            self.notebook.select(self.tabs[path]["frame"])
            return
        frame = ttk.Frame(self.notebook)
        text = Text(frame, wrap="none", undo=True, font=("Consolas", 11))
        text.pack(fill=BOTH, expand=YES)
        try:
            text.insert("1.0", path.read_text())
        except Exception as exc:
            Messagebox.show_error("Open failed", str(exc))
            return
        self.notebook.add(frame, text=f"{path.name} ✕")
        self.tabs[path] = {"frame": frame, "text": text}
        self.notebook.select(frame)

    def close_tab(self, tab_id: str) -> None:
        frame = self.notebook.nametowidget(tab_id)
        self.notebook.forget(frame)
        for p, tab in list(self.tabs.items()):
            if tab["frame"] == frame:
                del self.tabs[p]
                break

    def save_current(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        path, d = tab
        try:
            path.write_text(d["text"].get("1.0", "end-1c"))
        except Exception as exc:
            Messagebox.show_error("Save failed", str(exc))

    def current_tab(self) -> tuple[Path, dict[str, object]] | None:
        current = self.notebook.select()
        if not current:
            return None
        frame = self.notebook.nametowidget(current)
        for p, d in self.tabs.items():
            if d["frame"] == frame:
                return p, d
        return None


class StatusBar(ttk.Frame):
    """Simple status bar."""

    def __init__(self, master) -> None:
        super().__init__(master, style="secondary.TFrame")
        self.var = ttk.StringVar(value="")
        lbl = ttk.Label(self, textvariable=self.var, anchor=W)
        lbl.pack(fill=X, padx=5)

    def set(self, msg: str) -> None:
        self.var.set(msg)


class TerminalPanel(ttk.Frame):
    """Bottom panel for log/terminal output."""

    def __init__(self, master) -> None:
        super().__init__(master)
        self.text = Text(self, height=8, wrap="none", font=("Consolas", 10))
        self.text.pack(fill=BOTH, expand=YES)
        self.text.config(state="disabled")

        self.entry = ttk.Entry(self)
        self.entry.pack(fill=X)
        self.entry.bind("<Return>", self.on_enter)
        self.running = False

    def write(self, msg: str) -> None:
        self.text.config(state="normal")
        self.text.insert(END, msg)
        self.text.see(END)
        self.text.config(state="disabled")

    def on_enter(self, event: object) -> None:
        cmd = self.entry.get().strip()
        if cmd and not self.running:
            self.entry.delete(0, END)
            self.write(f"$ {cmd}\n")
            threading.Thread(target=self.run_command, args=(cmd,), daemon=True).start()

    def run_command(self, cmd: str) -> None:
        self.running = True
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=TEMPLATE,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert proc.stdout
            for line in proc.stdout:
                self.after(0, lambda l=line: self.write(l))
            proc.wait()
        except Exception as exc:
            self.after(0, lambda: self.write(f"Error: {exc}\n"))
        finally:
            self.running = False


class CommandPalette(ttk.Toplevel):
    """Basic command palette."""

    def __init__(self, master, commands: dict[str, callable]) -> None:
        super().__init__(master)
        self.withdraw()
        self.commands = commands
        self.entry = ttk.Entry(self)
        self.entry.pack(fill=X, padx=5, pady=5)
        self.listbox = Listbox(self, height=5)
        self.listbox.pack(fill=BOTH, expand=YES)
        self.entry.bind("<KeyRelease>", self.on_change)
        self.entry.bind("<Return>", lambda e: self.execute())
        self.listbox.bind("<Double-1>", lambda e: self.execute())

    def open(self) -> None:
        self.update_list("")
        self.entry.delete(0, END)
        self.deiconify()
        self.entry.focus_set()

    def on_change(self, event: object) -> None:
        self.update_list(self.entry.get())

    def update_list(self, filter_text: str) -> None:
        self.listbox.delete(0, END)
        for name in self.commands:
            if filter_text.lower() in name.lower():
                self.listbox.insert(END, name)

    def execute(self) -> None:
        sel = self.listbox.get(ACTIVE)
        if sel and sel in self.commands:
            self.commands[sel]()
        self.withdraw()


class TourGuide(Toplevel):
    """Simple tour guiding the user through initial files."""

    def __init__(self, master: "Stage1GUI") -> None:
        super().__init__(master)
        self.master = master
        self.steps = [
            (TEMPLATE / "config" / "GAMEID" / "config.yml", "Edit paths and compiler options in config.yml."),
            (TEMPLATE / "config" / "GAMEID" / "build.sha1", "Hashes for main.dol and RELs live in build.sha1."),
            (CONFIGURE, "configure.py generates build files. Run it after editing."),
        ]
        self.index = 0
        self.resizable(False, False)
        self.title("Welcome Tour")

        self.label = ttk.Label(self, wraplength=360, justify=LEFT)
        self.label.pack(padx=15, pady=15)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(0, 15))
        ttk.Button(btn_frame, text="Previous", command=self.prev).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Next", command=self.next).pack(side=LEFT, padx=5)

        self.update_step()

    def update_step(self) -> None:
        path, msg = self.steps[self.index]
        self.master.show_ide()
        self.master.ide.open_file(path)
        self.label.configure(text=msg)

    def prev(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.update_step()

    def next(self) -> None:
        self.index += 1
        if self.index >= len(self.steps):
            self.destroy()
        else:
            self.update_step()


class MiniIDE(ttk.Frame):
    """Minimal IDE attached to the main window."""

    def __init__(self, master: ttk.Frame, root_dir: Path = TEMPLATE) -> None:
        super().__init__(master)
        self.root_dir = root_dir
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.sidebar = Sidebar(self, lambda n: None)
        self.sidebar.grid(row=0, column=0, sticky=NS)

        main_pane = ttk.PanedWindow(self, orient=VERTICAL)
        main_pane.grid(row=0, column=1, sticky=NSEW)

        edit_frame = ttk.Frame(main_pane)
        edit_frame.columnconfigure(1, weight=1)
        edit_frame.rowconfigure(0, weight=1)
        main_pane.add(edit_frame, weight=3)

        self.tree = ttk.Treeview(edit_frame, show="tree")
        self.tree.grid(row=0, column=0, sticky=NS)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.tree.bind("<Double-1>", self.on_tree_double)

        self.editor = EditorTabs(edit_frame)
        self.editor.grid(row=0, column=1, sticky=NSEW)

        self.terminal = TerminalPanel(main_pane)
        main_pane.add(self.terminal, weight=1)

        self.status = StatusBar(self)
        self.status.grid(row=1, column=0, columnspan=2, sticky=EW)

        self.palette = CommandPalette(
            self,
            {
                "Open File": self.open_dialog,
                "Save File": self.save_current,
            },
        )

        accel = "<Command-Shift-P>" if sys.platform == "darwin" else "<Control-Shift-P>"
        self.bind_all(accel, lambda e: self.palette.open())

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
                if any(child.iterdir()):
                    self.tree.insert(node, "end")
            else:
                self.tree.insert(parent, "end", iid=iid, text=child.name)

    def on_tree_open(self, event: object) -> None:
        node = self.tree.focus()
        path = Path(node)
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
        self.editor.open_file(path)



class Stage1GUI(ttk.Window):
    def __init__(self) -> None:
        super().__init__(title="Stage 1 Launcher", themename="darkly", size=(1000, 700))
        ensure_template()

        self.iso_path = ttk.StringVar()
        self.game_id = ttk.StringVar()
        self.dtk_path = ttk.StringVar(value="dtk")
        self.status_var = ttk.StringVar()

        # Use a horizontal layout so the IDE can appear to the right
        self.paned = ttk.PanedWindow(self, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES)

        container = ttk.Frame(self.paned, padding=15)
        self.paned.add(container, weight=0)
        container.columnconfigure(1, weight=1)

        self.ide = MiniIDE(self.paned, TEMPLATE)
        # start hidden
        self.paned.add(self.ide, weight=1)
        self.paned.forget(self.ide)

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

        ttk.Button(container, text="Open IDE", command=self.show_ide, bootstyle="secondary")\
            .grid(row=4, column=0, columnspan=3)

        ttk.Button(container, text="Run configure.py", command=self.run_configure, bootstyle="primary")\
            .grid(row=5, column=0, columnspan=3, pady=10)

        ttk.Label(container, textvariable=self.status_var, foreground="cyan")\
            .grid(row=6, column=0, columnspan=3, sticky=W)

        # show an initial tour after the window appears
        self.after(1000, lambda: TourGuide(self))

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

        self.status_var.set("Extracting…")
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
                update_build_sha1("GAMEID")

            def finish() -> None:
                if sha1:
                    self.status_var.set(f"Extraction complete\nmain.dol sha1: {sha1}")
                elif any(ORIG_DIR.iterdir()):
                    self.status_var.set("Extraction complete")
                else:
                    self.status_var.set("Extraction produced no files")
                self.rename_btn.config(state="normal")

            self.after(0, finish)

        threading.Thread(target=task, daemon=True).start()

    def show_ide(self) -> None:
        panes = self.paned.panes()
        if str(self.ide) not in panes:
            self.paned.add(self.ide, weight=1)

    def rename_gameid(self) -> None:
        new_id = self.game_id.get().strip().upper()
        if not new_id:
            Messagebox.show_error("Error", "Enter a Game ID")
            return

        self.status_var.set("Renaming…")

        def task() -> None:
            try:
                rename_gameid(TEMPLATE, new_id)
                update_build_sha1(new_id)
            except Exception as exc:
                self.after(0, lambda: Messagebox.show_error("Rename failed", str(exc)))
                return
            self.after(0, lambda: self.status_var.set(f"Renamed to {new_id}"))

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

        self.status_var.set("Running Stage 1…")

        def task() -> None:
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as exc:
                self.after(0, lambda: Messagebox.show_error("Stage 1 failed", str(exc)))
                return
            self.after(0, lambda: self.status_var.set("Stage 1 completed"))

        threading.Thread(target=task, daemon=True).start()

    def edit_config(self) -> None:
        game_id = self.game_id.get().strip().upper() or "GAMEID"
        path = TEMPLATE / "config" / game_id / "config.yml"
        if os.environ.get("EDITOR") or os.environ.get("VISUAL"):
            open_file(path)
        else:
            self.show_ide()
            self.ide.open_file(path)

    def edit_sha1(self) -> None:
        game_id = self.game_id.get().strip().upper() or "GAMEID"
        path = TEMPLATE / "config" / game_id / "build.sha1"
        if os.environ.get("EDITOR") or os.environ.get("VISUAL"):
            open_file(path)
        else:
            self.show_ide()
            self.ide.open_file(path)

    def edit_configure(self) -> None:
        if os.environ.get("EDITOR") or os.environ.get("VISUAL"):
            open_file(CONFIGURE)
        else:
            self.show_ide()
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
            self.status_var.set("configure.py completed")
        except subprocess.CalledProcessError as exc:
            Messagebox.show_error("configure.py failed", str(exc))


if __name__ == "__main__":
    Stage1GUI().mainloop()
