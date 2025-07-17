from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext


def parse_functions(path: Path):
    """Return list of (name, start_idx, end_idx) tuples and file lines."""
    lines = path.read_text().splitlines()
    funcs = []
    name = None
    start = 0
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('.fn '):
            if name is not None:
                funcs.append((name, start, idx))
            parts = stripped.split()
            name = parts[1].rstrip(',') if len(parts) > 1 else f'func_{idx}'
            start = idx
        elif stripped.startswith('.endfn') and name is not None:
            funcs.append((name, start, idx + 1))
            name = None
    if name is not None:
        funcs.append((name, start, len(lines)))
    return funcs, lines


class Browser(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Assembly Browser")
        self.geometry("900x600")

        self.folder_var = tk.StringVar()
        self.filter_var = tk.StringVar()

        top = tk.Frame(self)
        top.pack(fill='x', padx=5, pady=5)
        tk.Label(top, text="ASM folder:").pack(side='left')
        tk.Entry(top, textvariable=self.folder_var, width=50).pack(side='left', fill='x', expand=True)
        tk.Button(top, text="Browse", command=self.browse).pack(side='left', padx=2)
        tk.Button(top, text="Scan", command=self.scan).pack(side='left')

        filt = tk.Frame(self)
        filt.pack(fill='x', padx=5, pady=5)
        tk.Label(filt, text="Filter:").pack(side='left')
        tk.Entry(filt, textvariable=self.filter_var).pack(side='left', fill='x', expand=True)
        tk.Button(filt, text="Apply", command=self.scan).pack(side='left', padx=2)

        self.progress = tk.Label(self, text="")
        self.progress.pack(pady=2)

        lists = tk.Frame(self)
        lists.pack(fill='both', expand=True, padx=5, pady=5)

        self.file_list = ttk.Treeview(lists, columns=("file",), show='headings', selectmode='browse')
        self.file_list.heading('file', text='ASM File')
        self.file_list.pack(side='left', fill='both', expand=True)
        self.file_list.bind('<<TreeviewSelect>>', self.load_file)

        self.func_list = ttk.Treeview(lists, columns=("func",), show='headings', selectmode='browse')
        self.func_list.heading('func', text='Function')
        self.func_list.pack(side='left', fill='both', expand=True)
        self.func_list.bind('<Double-1>', self.show_function)

        self.functions = []
        self.lines = []

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_var.set(path)

    def scan(self):
        folder = Path(self.folder_var.get())
        if not folder.is_dir():
            messagebox.showerror("Error", "Invalid folder")
            return
        self.progress.config(text="Scanning...")
        thread = threading.Thread(target=self._scan_files, args=(folder, self.filter_var.get().lower()))
        thread.start()

    def _scan_files(self, folder: Path, filt: str):
        files = [f.name for f in sorted(folder.glob('*.s')) if not filt or filt in f.name.lower()]
        self.after(0, self._update_file_list, files)

    def _update_file_list(self, files):
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        for i, name in enumerate(files):
            self.file_list.insert('', 'end', iid=str(i), values=(name,))
        for item in self.func_list.get_children():
            self.func_list.delete(item)
        self.functions = []
        self.lines = []
        self.progress.config(text="")

    def load_file(self, event=None):
        sel = self.file_list.selection()
        if not sel:
            return
        filename = self.file_list.item(sel[0])['values'][0]
        file_path = Path(self.folder_var.get()) / filename
        self.progress.config(text="Parsing...")
        threading.Thread(target=self._parse_file, args=(file_path,)).start()

    def _parse_file(self, path: Path):
        funcs, lines = parse_functions(path)
        self.after(0, self._update_func_list, funcs, lines)

    def _update_func_list(self, funcs, lines):
        for item in self.func_list.get_children():
            self.func_list.delete(item)
        for i, (name, _s, _e) in enumerate(funcs):
            self.func_list.insert('', 'end', iid=str(i), values=(name,))
        self.functions = funcs
        self.lines = lines
        self.progress.config(text="")

    def show_function(self, event=None):
        sel = self.func_list.selection()
        if not sel:
            return
        idx = int(sel[0])
        name, start, end = self.functions[idx]
        asm_text = '\n'.join(self.lines[start:end])
        win = tk.Toplevel(self)
        win.title(name)
        text = scrolledtext.ScrolledText(win, width=100, height=40)
        text.pack(fill='both', expand=True)
        text.insert('1.0', asm_text)
        text.configure(state='disabled')


if __name__ == '__main__':
    Browser().mainloop()
