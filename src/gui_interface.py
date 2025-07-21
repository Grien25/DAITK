import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from tkinter.scrolledtext import ScrolledText
from decompiler import decompile_asm_file
from assembly_parser import extract_functions_from_asm
import threading
import os

GEMINI_API_KEY = "AIzaSyDIkQe9MOnjVxcbF56bVASvXSNifdDGQlU"
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

        ttk.Button(frm, text="Decompile", command=self.run_decompilation).grid(row=1, column=0, pady=10)
        ttk.Button(frm, text="Target", command=self.target_file_placement).grid(row=1, column=1, pady=10)
        ttk.Button(frm, text="Print", command=self.print_filesystem).grid(row=1, column=2, pady=10)
        ttk.Button(frm, text="Manual Target", command=self.manual_target).grid(row=1, column=3, pady=10)
        ttk.Button(frm, text="Manual Print", command=self.manual_print).grid(row=1, column=4, pady=10)

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
        # Save decompiled code to ~/Documents/DAITK_Data
        # self.save_decompiled_to_data_dir(text)

    def save_decompiled_to_data_dir(self, output_text):
        import os
        data_dir = os.path.expanduser("~/Documents/DAITK_Data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        import re
        func_blocks = re.split(r"-+\n", output_text)
        new_files = []
        for block in func_blocks:
            match = re.search(r"Function: (\w+)", block)
            code_match = re.search(r"Decompiled:\n(.+)", block, re.DOTALL)
            if match and code_match:
                func_name = match.group(1)
                decompiled_code = code_match.group(1).strip()
                file_path = os.path.join(data_dir, f"{func_name}.c")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(decompiled_code)
                new_files.append((func_name, decompiled_code))
        # After saving, send file tree and new code to AI for placement suggestions
        file_tree_str = self.build_data_dir_tree(data_dir)
        self.ask_ai_file_placement(file_tree_str, new_files)

    def build_data_dir_tree(self, data_dir):
        file_tree = []
        for root, dirs, files in os.walk(data_dir):
            level = root.replace(data_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                file_tree.append(f"{subindent}{f}")
        return '\n'.join(file_tree) if file_tree else '(Empty)'

    def target_file_placement(self):
        # Send file tree and new decompiled code to AI for file placement suggestions
        import os
        data_dir = os.path.expanduser("~/Documents/DAITK_Data")
        file_tree_str = self.build_data_dir_tree(data_dir)
        new_files = self.get_new_decompiled_files(data_dir)
        ai_suggestion = self.ask_ai_file_placement(file_tree_str, new_files, show_result=True)
        # Store the AI suggestion for use in Print
        self.last_ai_suggestion = ai_suggestion

    def get_new_decompiled_files(self, data_dir):
        # Get all .c files in DAITK_Data as new decompiled files
        import os
        new_files = []
        for f in os.listdir(data_dir):
            if f.endswith('.c'):
                with open(os.path.join(data_dir, f), 'r', encoding='utf-8') as file:
                    code = file.read()
                func_name = os.path.splitext(f)[0]
                new_files.append((func_name, code))
        return new_files

    def ask_ai_file_placement(self, file_tree_str, new_files, show_result=False):
        # This is the file destination prompt
        from llm_interface import GeminiLLM
        import json
        prompt = f"""
You are an expert C/C++ project architect. Here is the current file and folder structure under ~/Documents/DAITK_Data:

{file_tree_str}

Here are new decompiled functions (with their code):
"""
        for func_name, code in new_files:
            prompt += f"\nFunction: {func_name}\n{code}\n"
        prompt += """
For each function, suggest:
- The most appropriate .c/.cpp file (and .h file, if needed) and folder to place it in, based on the function's name, purpose, and the existing structure.
- If a new file or folder should be created, specify its name and location.
- If a header file is needed for declarations, specify its name and location.

Respond in JSON format like:
[
  {
    \"function\": \"<FUNC_NAME>\",
    \"c_file\": \"<relative/path/to/file.c>\",
    \"h_file\": \"<relative/path/to/file.h>\", // or null if not needed
    \"folder\": \"<relative/path/to/folder>\"
  },
  ...
]
"""
        # Call Gemini LLM
        llm = GeminiLLM()
        ai_response = llm.decompile(prompt)
        # Try to parse JSON from the response
        try:
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            ai_json = ai_response[json_start:json_end]
            ai_suggestion = json.loads(ai_json)
        except Exception as e:
            ai_suggestion = ai_response
        if show_result:
            from tkinter import messagebox
            messagebox.showinfo("AI File Placement Suggestion", str(ai_suggestion))
        return ai_suggestion

    def print_filesystem(self):
        # Show the current file system under ~/Documents/DAITK_Data and, if available, the last AI suggestion
        import os
        from tkinter import messagebox
        data_dir = os.path.expanduser("~/Documents/DAITK_Data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        file_tree = []
        for root, dirs, files in os.walk(data_dir):
            level = root.replace(data_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                file_tree.append(f"{subindent}{f}")
        tree_str = '\n'.join(file_tree) if file_tree else '(Empty)'
        msg = f"DAITK_Data File System:\n{tree_str}"
        # Show AI suggestion summary and offer to apply changes
        if hasattr(self, 'last_ai_suggestion') and self.last_ai_suggestion:
            msg += "\n\nAI File Placement Plan:\n"
            if isinstance(self.last_ai_suggestion, list):
                for entry in self.last_ai_suggestion:
                    msg += f"Function: {entry.get('function')}\n  C file: {entry.get('c_file')}\n  H file: {entry.get('h_file')}\n  Folder: {entry.get('folder')}\n---\n"
                msg += "\nApply this plan to move/create files?"
                if messagebox.askyesno("Apply AI File Placement?", msg):
                    self.apply_ai_file_placement(self.last_ai_suggestion)
                    messagebox.showinfo("Placement Applied", "Files have been moved/created as suggested.")
                    return
            else:
                msg += str(self.last_ai_suggestion)
        messagebox.showinfo("DAITK_Data File System", msg)

    def apply_ai_file_placement(self, ai_suggestion):
        import os
        data_dir = os.path.expanduser("~/Documents/DAITK_Data")
        for entry in ai_suggestion:
            folder = os.path.join(data_dir, entry.get('folder', ''))
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            # Move or create C file
            c_file = entry.get('c_file')
            if c_file:
                src = os.path.join(data_dir, f"{entry['function']}.c")
                dst = os.path.join(data_dir, c_file)
                if os.path.exists(src):
                    os.rename(src, dst)
            # Create header file if needed
            h_file = entry.get('h_file')
            if h_file:
                h_path = os.path.join(data_dir, h_file)
                if not os.path.exists(h_path):
                    with open(h_path, 'w', encoding='utf-8') as f:
                        f.write(f"// Header for {entry['function']}\n")

    def manual_target(self):
        # Let user pick a decompiled function and a file to place it in
        import os
        from tkinter import simpledialog, messagebox, filedialog
        data_dir = os.path.expanduser("~/Documents/DAITK_Data")
        # List available decompiled functions
        c_files = [f for f in os.listdir(data_dir) if f.endswith('.c')]
        if not c_files:
            messagebox.showerror("No Decompiled Functions", "No decompiled .c files found in DAITK_Data.")
            return
        func_choice = simpledialog.askstring("Manual Target", f"Available functions: {', '.join(c_files)}\nEnter function file name to move (e.g., myfunc.c):")
        if not func_choice or func_choice not in c_files:
            messagebox.showerror("Invalid Choice", "Function not found.")
            return
        # Let user pick a target file
        target_file = filedialog.asksaveasfilename(initialdir=data_dir, title="Select or create target file", defaultextension=".c", filetypes=[("C files", "*.c"), ("All files", "*.*")])
        if not target_file:
            return
        # Append function code to the chosen file
        with open(os.path.join(data_dir, func_choice), 'r', encoding='utf-8') as src:
            code = src.read()
        with open(target_file, 'a', encoding='utf-8') as dst:
            dst.write(f"\n\n// Manually inserted function from {func_choice}\n{code}\n")
        messagebox.showinfo("Manual Target", f"Function {func_choice} appended to {target_file}.")

    def manual_print(self):
        # Let user pick a file in DAITK_Data to open in the system's default editor
        import os
        import subprocess
        from tkinter import filedialog, messagebox
        data_dir = os.path.expanduser("~/Documents/DAITK_Data")
        file_path = filedialog.askopenfilename(initialdir=data_dir, title="Select file to open", filetypes=[("All files", "*.*")])
        if not file_path:
            return
        # Open with VSCode if available, else TextEdit (mac), WordPad (win), or xdg-open (linux)
        try:
            if self._is_command_available('code'):
                subprocess.Popen(['code', file_path])
            elif os.name == 'posix':
                if self._is_command_available('open'):
                    subprocess.Popen(['open', file_path])  # macOS TextEdit
                else:
                    subprocess.Popen(['xdg-open', file_path])  # Linux
            elif os.name == 'nt':
                subprocess.Popen(['write', file_path])  # WordPad
            else:
                messagebox.showerror("No Editor", "No suitable editor found.")
        except Exception as e:
            messagebox.showerror("Error Opening File", str(e))

    def _is_command_available(self, cmd):
        import shutil
        return shutil.which(cmd) is not None


def main():
    root = tk.Tk()
    app = DecompilerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main() 