import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path

class FunctionBrowser(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Assembly Function Browser")
        self.geometry("600x400")
        self.directory = tk.StringVar()
        self.filter_var = tk.StringVar()

        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(top_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT)
        ttk.Entry(top_frame, textvariable=self.directory, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        filter_entry.bind("<KeyRelease>", lambda e: self.update_list())

        self.tree = ttk.Treeview(self, columns=("file"), show="headings")
        self.tree.heading("file", text="Function File")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.directory.set(path)
            self.update_list()

    def update_list(self):
        self.tree.delete(*self.tree.get_children())
        folder = Path(self.directory.get())
        filt = self.filter_var.get().lower()
        if not folder.is_dir():
            return
        for f in sorted(folder.glob("*.s")):
            name = f.name
            if filt and filt not in name.lower():
                continue
            self.tree.insert("", tk.END, values=(name,))

if __name__ == "__main__":
    FunctionBrowser().mainloop()
