import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from decompiler import decompile_asm_file
from assembly_parser import extract_functions_from_asm

class DecompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Decompiler for Assembly Functions")
        self.file_path = tk.StringVar()
        self.backend = tk.StringVar(value='local')
        self.model_path = tk.StringVar()
        self.api_key = tk.StringVar()
        self.functions = []  # List of dicts from extract_functions_from_asm

        self.create_widgets()
        # Remove file_path trace for auto-scan
        # self.file_path.trace_add('write', self.on_file_path_change)

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Assembly (.s) file:").grid(row=0, column=0, sticky="w")
        file_entry = ttk.Entry(frm, textvariable=self.file_path, width=40)
        file_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(frm, text="Browse", command=self.browse_file).grid(row=0, column=2)
        ttk.Button(frm, text="Scan", command=self.scan_functions).grid(row=0, column=3, padx=(10,0))

        ttk.Label(frm, text="LLM Backend:").grid(row=1, column=0, sticky="w")
        backend_combo = ttk.Combobox(frm, textvariable=self.backend, values=["local", "gemini"], state="readonly", width=10)
        backend_combo.grid(row=1, column=1, sticky="w")
        backend_combo.bind('<<ComboboxSelected>>', self.update_backend_fields)

        self.model_path_label = ttk.Label(frm, text="Model Path:")
        self.model_path_entry = ttk.Entry(frm, textvariable=self.model_path, width=40)
        self.api_key_label = ttk.Label(frm, text="Gemini API Key:")
        self.api_key_entry = ttk.Entry(frm, textvariable=self.api_key, width=40, show="*")

        self.model_path_label.grid(row=2, column=0, sticky="w")
        self.model_path_entry.grid(row=2, column=1, sticky="ew")
        self.api_key_label.grid_forget()
        self.api_key_entry.grid_forget()

        ttk.Button(frm, text="Decompile", command=self.run_decompilation).grid(row=3, column=0, columnspan=4, pady=10)

        # Function list and assembly display
        bottom_frame = ttk.Frame(frm)
        bottom_frame.grid(row=4, column=0, columnspan=4, sticky="nsew", pady=5)
        bottom_frame.columnconfigure(1, weight=1)
        bottom_frame.rowconfigure(0, weight=1)

        # Listbox for function names
        self.func_listbox = tk.Listbox(bottom_frame, width=30, height=20)
        self.func_listbox.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        self.func_listbox.bind('<<ListboxSelect>>', self.display_selected_function)

        # Text area for assembly code
        self.asm_text = scrolledtext.ScrolledText(bottom_frame, width=60, height=20, font=("Courier", 10))
        self.asm_text.grid(row=0, column=1, sticky="nsew")

        # Output area for decompiled code (initially hidden)
        self.output = scrolledtext.ScrolledText(frm, width=80, height=10, font=("Courier", 10))
        self.output_is_visible = False

        frm.columnconfigure(1, weight=1)
        self.update_backend_fields()

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Assembly files", "*.s")])
        if path:
            self.file_path.set(path)

    def scan_functions(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showerror("Error", "Please select an assembly (.s) file.")
            return
        self.load_functions(file_path)

    def load_functions(self, file_path):
        try:
            self.functions = extract_functions_from_asm(file_path)
            self.func_listbox.delete(0, tk.END)
            for func in self.functions:
                self.func_listbox.insert(tk.END, func['name'])
            self.asm_text.delete(1.0, tk.END)
            if self.functions:
                self.func_listbox.selection_set(0)
                self.display_selected_function()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse functions: {e}")
            self.functions = []
            self.func_listbox.delete(0, tk.END)
            self.asm_text.delete(1.0, tk.END)

    def display_selected_function(self, event=None):
        selection = self.func_listbox.curselection()
        if not selection or not self.functions:
            self.asm_text.delete(1.0, tk.END)
            return
        idx = selection[0]
        func = self.functions[idx]
        self.asm_text.delete(1.0, tk.END)
        self.asm_text.insert(tk.END, func['code'])

    def update_backend_fields(self, event=None):
        if self.backend.get() == 'local':
            self.model_path_label.grid(row=2, column=0, sticky="w")
            self.model_path_entry.grid(row=2, column=1, sticky="ew")
            self.api_key_label.grid_forget()
            self.api_key_entry.grid_forget()
        else:
            self.model_path_label.grid_forget()
            self.model_path_entry.grid_forget()
            self.api_key_label.grid(row=2, column=0, sticky="w")
            self.api_key_entry.grid(row=2, column=1, sticky="ew")

    def run_decompilation(self):
        if not self.output_is_visible:
            self.output.grid(row=5, column=0, columnspan=4, pady=5)
            self.output_is_visible = True
        self.output.delete(1.0, tk.END)
        file_path = self.file_path.get()
        backend = self.backend.get()
        llm_kwargs = {}
        if backend == 'local' and self.model_path.get():
            llm_kwargs['model_path'] = self.model_path.get()
        if backend == 'gemini' and self.api_key.get():
            llm_kwargs['api_key'] = self.api_key.get()
        if not file_path:
            messagebox.showerror("Error", "Please select an assembly (.s) file.")
            return
        try:
            results = decompile_asm_file(file_path, backend, llm_kwargs)
            for func in results:
                self.output.insert(tk.END, f"\nFunction: {func['name']} (lines {func['start_line']}-{func['end_line']})\n")
                self.output.insert(tk.END, "Assembly:\n" + func['asm_code'] + "\n")
                self.output.insert(tk.END, "Decompiled:\n" + func['decompiled_code'] + "\n")
                self.output.insert(tk.END, "-"*60 + "\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            if self.output_is_visible:
                self.output.grid_remove()
                self.output_is_visible = False


def main():
    root = tk.Tk()
    app = DecompilerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main() 