import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from src2.ai_interface import DepositerAI
from src2.project_manager import ensure_project_dir, build_file_tree, read_file_content
from src2.prompts import build_placement_prompt, extract_file_from_suggestion, build_insert_prompt, build_code_checkbox_prompt, build_project_stability_prompt
from src2.threading_utils import run_in_thread
import os
import pathlib
import re
import difflib

class FunctionDepositerGUI:
    def __init__(self, root, api_key, model):
        self.root = root
        self.api_key = api_key
        self.model = model
        self.ai = DepositerAI(api_key, model)
        self.project_name = tk.StringVar()
        self.c_source = tk.StringVar()
        self.header_source = tk.StringVar()
        self.file_suggestion = tk.StringVar()
        self.insert_suggestion = tk.StringVar()
        self._build_widgets()

    def _build_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        self.root.title("Function Depositer (Wii)")

        ttk.Label(frm, text="Project Name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.project_name, width=30).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="C Source Code:").grid(row=1, column=0, sticky="nw", pady=(10,0))
        self.c_text = scrolledtext.ScrolledText(frm, width=80, height=10)
        self.c_text.grid(row=1, column=1, pady=(10,0), sticky="ew")

        ttk.Label(frm, text="Header Source (optional):").grid(row=2, column=0, sticky="nw", pady=(10,0))
        self.h_text = scrolledtext.ScrolledText(frm, width=80, height=5)
        self.h_text.grid(row=2, column=1, pady=(10,0), sticky="ew")

        self.deposit_btn = ttk.Button(frm, text="Deposit Function", command=self.start_deposit)
        self.deposit_btn.grid(row=3, column=1, pady=10, sticky="e")

        # Checkboxes for each AI step (remove project stability)
        self.var_deposit = tk.BooleanVar(value=False)
        self.var_checkbox = tk.BooleanVar(value=False)
        self.label_deposit = ttk.Checkbutton(frm, text="Function Deposited", variable=self.var_deposit, state='disabled')
        self.label_deposit.grid(row=4, column=0, sticky="w")
        self.label_checkbox = ttk.Checkbutton(frm, text="Code Checkbox Passed", variable=self.var_checkbox, state='disabled')
        self.label_checkbox.grid(row=4, column=1, sticky="w")
        self.status_label = ttk.Label(frm, text="")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="w")

        ttk.Label(frm, text="AI File Placement Suggestion:").grid(row=6, column=0, sticky="nw", pady=(10,0))
        self.file_suggestion_text = scrolledtext.ScrolledText(frm, width=80, height=4, state='disabled')
        self.file_suggestion_text.grid(row=6, column=1, pady=(10,0), sticky="ew")

        ttk.Label(frm, text="AI Insertion Suggestion:").grid(row=7, column=0, sticky="nw", pady=(10,0))
        self.insert_suggestion_text = scrolledtext.ScrolledText(frm, width=80, height=4, state='disabled')
        self.insert_suggestion_text.grid(row=7, column=1, pady=(10,0), sticky="ew")

        frm.columnconfigure(1, weight=1)

    def start_deposit(self):
        project = self.project_name.get().strip()
        c_source = self.c_text.get("1.0", tk.END).strip()
        h_source = self.h_text.get("1.0", tk.END).strip() or None
        self.var_deposit.set(False)
        self.var_checkbox.set(False)
        self.status_label.config(text="")
        if not project or not c_source:
            messagebox.showerror("Error", "Project name and C source code are required.")
            return
        self.deposit_btn.config(state='disabled')
        self.file_suggestion_text.config(state='normal')
        self.file_suggestion_text.delete("1.0", tk.END)
        self.file_suggestion_text.config(state='disabled')
        self.insert_suggestion_text.config(state='normal')
        self.insert_suggestion_text.delete("1.0", tk.END)
        self.insert_suggestion_text.config(state='disabled')
        project_dir = os.path.abspath(ensure_project_dir('DAITK_data', project))
        file_tree = build_file_tree(project_dir)
        prompt = build_placement_prompt(file_tree, c_source, h_source)
        def on_placement_suggestion(placement_suggestion):
            self.file_suggestion_text.config(state='normal')
            self.file_suggestion_text.delete("1.0", tk.END)
            self.file_suggestion_text.insert(tk.END, placement_suggestion)
            self.file_suggestion_text.config(state='disabled')
            user_file_choice = extract_file_from_suggestion(placement_suggestion)
            # --- ENFORCE FILE STRUCTURE ---
            project_dir = os.path.abspath(ensure_project_dir('DAITK_data', project))
            src_dir = os.path.join(project_dir, 'src')
            if not os.path.exists(src_dir):
                os.makedirs(src_dir)
            # Only allow .c, .h, .cpp extensions
            allowed_exts = ['.c', '.h', '.cpp']
            # Canonical grouping for standard functions
            std_func_to_file = {
                'memcpy': 'memory.c',
                'memset': 'memory.c',
                'memmove': 'memory.c',
                'memcmp': 'memory.c',
                'strcpy': 'string.c',
                'strncpy': 'string.c',
                'strcmp': 'string.c',
                'strncmp': 'string.c',
                'strcat': 'string.c',
                'strncat': 'string.c',
                'strlen': 'string.c',
                'strchr': 'string.c',
                'strrchr': 'string.c',
                'strstr': 'string.c',
                'strtok': 'string.c',
            }
            # Extract function names from c_source
            func_names = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s+\**([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', c_source)
            canonical_file = None
            for fn in func_names:
                if fn in std_func_to_file:
                    canonical_file = std_func_to_file[fn]
                    break
            # Always use canonical file for standard functions
            if canonical_file:
                file_path = os.path.join(src_dir, canonical_file)
                if user_file_choice != f'src/{canonical_file}':
                    messagebox.showwarning("File Path Corrected", f"AI suggested {user_file_choice}, but standard function(s) will be placed in src/{canonical_file}.")
            else:
                # Sanitize the file path to prevent directory traversal
                safe_file_choice = os.path.normpath(user_file_choice).lstrip(os.sep)
                # Ensure path starts with src/
                if not safe_file_choice.startswith('src/'):
                    messagebox.showwarning("File Path Corrected", f"AI suggested {user_file_choice}, but all code files must be under src/. Path will be corrected.")
                    safe_file_choice = os.path.join('src', os.path.basename(safe_file_choice))
                # Only allow allowed extensions
                ext = os.path.splitext(safe_file_choice)[1]
                if ext not in allowed_exts:
                    messagebox.showwarning("File Extension Corrected", f"AI suggested {user_file_choice} with extension {ext}. Only .c, .h, .cpp are allowed. Using .c.")
                    safe_file_choice = os.path.splitext(safe_file_choice)[0] + '.c'
                file_path = os.path.join(project_dir, safe_file_choice)
            # Ensure file_path is within project_dir/src
            if not os.path.commonpath([file_path, src_dir]) == src_dir:
                messagebox.showerror("Error", "Invalid file path after correction. Aborting.")
                self.deposit_btn.config(state='normal')
                return
            file_content = read_file_content(file_path)
            insert_prompt = build_insert_prompt(file_content, c_source, h_source)
            def on_insert_suggestion(insert_suggestion):
                self.insert_suggestion_text.config(state='normal')
                self.insert_suggestion_text.delete("1.0", tk.END)
                self.insert_suggestion_text.insert(tk.END, insert_suggestion)
                self.insert_suggestion_text.config(state='disabled')
                file_changed = False
                if not os.path.exists(file_path):
                    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(c_source + '\n')
                        if h_source:
                            f.write('\n' + h_source + '\n')
                    file_changed = True
                else:
                    # Try to parse for full file content
                    if '---START FILE---' in insert_suggestion and '---END FILE---' in insert_suggestion:
                        start = insert_suggestion.find('---START FILE---') + len('---START FILE---')
                        end = insert_suggestion.find('---END FILE---')
                        file_content_new = insert_suggestion[start:end].strip('\n')
                        # Check if the new content preserves all old function definitions
                        with open(file_path, 'r') as f:
                            file_content_old = f.read()
                        # Find all function names in the old file
                        old_funcs = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s+\**([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', file_content_old))
                        new_funcs = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s+\**([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', file_content_new))
                        if old_funcs.issubset(new_funcs):
                            with open(file_path, 'w') as f:
                                f.write(file_content_new + '\n')
                            file_changed = True
                        else:
                            # Warn user and fallback: append the new function(s) to the end if not already present
                            messagebox.showwarning("AI Output Warning", "AI's output would remove existing functions. Appending new function(s) to the end instead.")
                            # Only append if the full function definition is not present
                            def function_defined(func_name, file_content):
                                # Match function definition at start of line, allowing whitespace, return type, pointer, etc.
                                pattern = re.compile(rf"^\s*[\w\s\*]+\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{", re.MULTILINE)
                                return bool(pattern.search(file_content))
                            # Extract function names from c_source
                            func_names = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s+\**([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', c_source))
                            missing_funcs = [fn for fn in func_names if not function_defined(fn, file_content_old)]
                            if missing_funcs:
                                with open(file_path, 'a') as f:
                                    f.write('\n' + c_source.strip() + '\n')
                                file_changed = True
                    else:
                        file_lines = []
                        with open(file_path, 'r') as f:
                            file_lines = f.readlines()
                        inserted = False
                        match = re.search(r'line (\d+)', insert_suggestion)
                        if match:
                            line_num = int(match.group(1))
                            file_lines = file_lines[:line_num] + [c_source + '\n'] + file_lines[line_num:]
                            inserted = True
                        else:
                            for line in file_lines:
                                snippet = line.strip()
                                if snippet and snippet in insert_suggestion:
                                    idx = file_lines.index(line)
                                    file_lines = file_lines[:idx+1] + [c_source + '\n'] + file_lines[idx+1:]
                                    inserted = True
                                    break
                        if inserted:
                            with open(file_path, 'w') as f:
                                f.writelines(file_lines)
                            file_changed = True
                        else:
                            # Fallback: append to end if not already present
                            # Only append if the full function definition is not present
                            def function_defined(func_name, file_content):
                                pattern = re.compile(rf"^\s*[\w\s\*]+\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{", re.MULTILINE)
                                return bool(pattern.search(file_content))
                            func_names = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s+\**([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{', c_source))
                            missing_funcs = [fn for fn in func_names if not function_defined(fn, file_content_old)]
                            if missing_funcs:
                                with open(file_path, 'a') as f:
                                    f.write('\n' + c_source.strip() + '\n')
                                file_changed = True
                if file_changed:
                    # --- Move all #include lines to the top ---
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    includes = [line for line in lines if line.strip().startswith('#include')]
                    non_includes = [line for line in lines if not line.strip().startswith('#include')]
                    # Optionally, preserve a blank line after includes if present in original
                    if non_includes and non_includes[0].strip() == '':
                        includes.append(non_includes.pop(0))
                    with open(file_path, 'w') as f:
                        f.writelines(includes + non_includes)
                    # ---
                    self.var_deposit.set(True)
                    self.status_label.config(text=f"Function deposited in: {os.path.basename(file_path)}")
                    # --- AI Checked (Code Checkbox) ---
                    file_content = read_file_content(file_path)
                    checkbox_prompt = build_code_checkbox_prompt(file_content, os.path.basename(file_path))
                    def on_checkbox_suggestion(checkbox_suggestion):
                        if 'No changes needed' in checkbox_suggestion:
                            self.var_checkbox.set(True)
                            self.status_label.config(text=f"Code Checkbox passed for: {os.path.basename(file_path)}")
                        elif '---START FILE---' in checkbox_suggestion and '---END FILE---' in checkbox_suggestion:
                            start = checkbox_suggestion.find('---START FILE---') + len('---START FILE---')
                            end = checkbox_suggestion.find('---END FILE---')
                            file_content2 = checkbox_suggestion[start:end].strip('\n')
                            with open(file_path, 'w') as f:
                                f.write(file_content2 + '\n')
                            self.var_checkbox.set(True)
                            self.status_label.config(text=f"Code Checkbox updated: {os.path.basename(file_path)}")
                        else:
                            messagebox.showwarning("Code Checkbox Failed", "AI could not verify or improve the file. Please review.")
                    run_in_thread(self.ai.ask, args=(checkbox_prompt,), callback=on_checkbox_suggestion)
                else:
                    messagebox.showwarning("Deposit Failed", "Could not deposit function. Please review the AI suggestion.")
                self.deposit_btn.config(state='normal')
            run_in_thread(self.ai.ask, args=(insert_prompt,), callback=on_insert_suggestion)
        run_in_thread(self.ai.ask, args=(prompt,), callback=on_placement_suggestion)

if __name__ == '__main__':
    api_key = "AIzaSyDIkQe9MOnjVxcbF56bVASvXSNifdDGQlU"
    model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    root = tk.Tk()
    app = FunctionDepositerGUI(root, api_key, model)
    root.mainloop() 