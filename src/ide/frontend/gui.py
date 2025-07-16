#!/usr/bin/env python3
"""Stage 1 GUI.

The interface guides the user through the first setup steps:

1. Selecting a Wii ISO and extracting it using ``wwt`` to
   ``tools/dtk-template/orig/GAMEID``.
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
TEMPLATE = ROOT / "tools" / "dtk-template"
WBFS_DIR = TEMPLATE / "WBFS"
ORIG_DIR = TEMPLATE / "orig" / "GAMEID"
STAGE1 = ROOT / "src" / "scripts" / "stage1.py"


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

<<<<<<< Updated upstream
class Stage1GUI(tk.Tk):
=======

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
                "Save File": self.editor.save_current,  # <-- FIXED
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
>>>>>>> Stashed changes
    def __init__(self) -> None:
        super().__init__()
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
