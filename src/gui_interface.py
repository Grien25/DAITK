import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from tkinter.scrolledtext import ScrolledText
from decompiler import decompile_asm_file
from assembly_parser import extract_functions_from_asm
import threading
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

class DecompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Decompiler for Assembly Functions")
        self.file_path = tk.StringVar()
        self.functions = []  # List of dicts from extract_functions_from_asm
        self.loading_var = tk.StringVar(value="")
        self.output_text = None

        self.create_widgets()
        # Remove file_path trace for auto-scan
        # self.file_path.trace_add('write', self.on_file_path_change)

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Button(frm, text="Browse", command=self.browse_file).grid(row=0, column=2)
        ttk.Button(frm, text="Scan", command=self.scan_functions).grid(row=0, column=3, padx=(10,0))

        # Remove backend and model path fields

        ttk.Button(frm, text="Decompile", command=self.run_decompilation).grid(row=1, column=0, columnspan=4, pady=10)

        # Loading indicator
        self.loading_label = ttk.Label(frm, textvariable=self.loading_var, foreground="blue")
        self.loading_label.grid(row=2, column=0, columnspan=4, pady=(5,0))

        # Output box for results/errors
        self.output_text = ScrolledText(self.root, width=100, height=25)
        self.output_text.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

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
        # self.update_backend_fields() # Removed

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

    # def update_backend_fields(self, event=None): # Removed
    #     if self.backend.get() == "local": # Removed
    #         self.model_path_label.grid() # Removed
    #         self.model_path_entry.grid() # Removed
    #         # self.api_key_label.grid_remove()  # Removed
    #         # self.api_key_entry.grid_remove()  # Removed
    #     elif self.backend.get() == "gemini": # Removed
    #         self.model_path_label.grid_remove() # Removed
    #         self.model_path_entry.grid_remove() # Removed
    #         # self.api_key_label.grid()  # Removed
    #         # self.api_key_entry.grid()  # Removed

    def run_decompilation(self):
        file_path = self.file_path.get()
        llm_kwargs = {'api_key': GEMINI_API_KEY, 'model': GEMINI_MODEL}
        if not file_path:
            messagebox.showerror("Error", "Please select an assembly (.s) file.")
            return
        # Show loading
        self.loading_var.set("Decompiling... Please wait.")
        self.root.update_idletasks()
        # Run decompilation in a thread to avoid blocking the GUI
        threading.Thread(target=self._decompile_thread, args=(file_path, llm_kwargs), daemon=True).start()

    def _decompile_thread(self, file_path, llm_kwargs):
        try:
            print("Starting decompilation...")  # Debug print
            selection = self.func_listbox.curselection()
            target = [self.functions[selection[0]]['name']] if selection else None
            results = decompile_asm_file(file_path, 'gemini', llm_kwargs, target)
            print("Decompilation results:", results)  # Debug print
            output = ""
            for func in results:
                output += f"\nFunction: {func['name']} (lines {func['start_line']}-{func['end_line']})\n"
                output += "Assembly:\n" + func['asm_code'] + "\n"
                output += "Decompiled:\n" + func['decompiled_code'] + "\n"
                output += "-"*60 + "\n"
            self.root.after(0, self._update_output, output)
        except Exception as e:
            self.loading_var.set("")
            print("Error during decompilation:", e)  # Debug print
            self.root.after(0, self._update_output, f"Error: {e}")
            return
        self.loading_var.set("")

    def _update_output(self, text):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)


def main():
    root = tk.Tk()
    app = DecompilerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main() 