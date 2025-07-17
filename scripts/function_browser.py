import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from threading import Thread
from queue import Queue, Empty


def parse_functions(path: Path):
    """Return a list of (name, start_idx, end_idx) for functions in the file."""
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

class FunctionBrowser(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Assembly Function Browser")
        self.geometry("800x500")
        self.directory = tk.StringVar()
        self.filter_var = tk.StringVar()
        self.functions = []
        self.lines = []
        self.queue: Queue = Queue()

        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(top_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT)
        ttk.Entry(top_frame, textvariable=self.directory, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        filter_entry.bind("<KeyRelease>", lambda e: self.start_file_scan())

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 2), pady=5)
        right = ttk.Frame(body)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 5), pady=5)

        self.files_tree = ttk.Treeview(left, columns=("file"), show="headings")
        self.files_tree.heading("file", text="ASM File")
        self.files_tree.pack(fill=tk.BOTH, expand=True)
        self.files_tree.bind("<<TreeviewSelect>>", self.on_file_select)

        self.func_tree = ttk.Treeview(right, columns=("func"), show="headings")
        self.func_tree.heading("func", text="Function")
        self.func_tree.pack(fill=tk.BOTH, expand=True)
        self.func_tree.bind("<Double-1>", self.open_function)

        # Progress indicator at the bottom
        self.progress = ttk.Label(self, text="")
        self.progress.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress_bar = ttk.Progressbar(self, mode="indeterminate")

        # Periodically process queued results from background threads
        self.after(100, self.process_queue)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.directory.set(path)
            self.start_file_scan()

    def start_file_scan(self):
        """Scan selected folder in a background thread."""
        self.files_tree.delete(*self.files_tree.get_children())
        self.func_tree.delete(*self.func_tree.get_children())
        folder = Path(self.directory.get())
        if not folder.is_dir():
            return
        self.progress.config(text="Scanning files...")
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress_bar.start()
        Thread(target=self._scan_files, args=(folder, self.filter_var.get().lower()), daemon=True).start()

    def _scan_files(self, folder: Path, filt: str):
        files = []
        for f in sorted(folder.glob("*.s")):
            name = f.name
            if filt and filt not in name.lower():
                continue
            files.append(name)
        self.queue.put(("files", files))

    def on_file_select(self, _event=None):
        sel = self.files_tree.selection()
        if not sel:
            return
        filename = self.files_tree.item(sel[0], "values")[0]
        file_path = Path(self.directory.get()) / filename
        self.progress.config(text="Parsing functions...")
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.progress_bar.start()
        Thread(target=self._parse_file, args=(file_path,), daemon=True).start()

    def _parse_file(self, file_path: Path):
        funcs, lines = parse_functions(file_path)
        self.queue.put(("functions", (funcs, lines)))

    def open_function(self, _event=None):
        sel = self.func_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        name, start, end = self.functions[idx]
        asm_text = "\n".join(self.lines[start:end])
        viewer = tk.Toplevel(self)
        viewer.title(name)
        viewer.geometry("900x600")
        text = ScrolledText(viewer, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", asm_text)
        text.configure(state="disabled")

    def process_queue(self):
        """Handle results from worker threads."""
        try:
            while True:
                msg, data = self.queue.get_nowait()
                if msg == "files":
                    self._update_files(data)
                elif msg == "functions":
                    self._update_functions(*data)
        except Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def _update_files(self, files):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress.config(text="")
        self.files_tree.delete(*self.files_tree.get_children())
        for name in files:
            self.files_tree.insert("", tk.END, values=(name,))

    def _update_functions(self, funcs, lines):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress.config(text="")
        self.functions = funcs
        self.lines = lines
        self.func_tree.delete(*self.func_tree.get_children())
        for i, (name, _s, _e) in enumerate(funcs):
            self.func_tree.insert("", tk.END, iid=str(i), values=(name,))

if __name__ == "__main__":
    FunctionBrowser().mainloop()
