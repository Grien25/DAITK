import os
from src2.ai_interface import DepositerAI
from src2.project_manager import ensure_project_dir, build_file_tree, read_file_content
from src2.prompts import build_placement_prompt, extract_file_from_suggestion, build_insert_prompt
from src2.threading_utils import run_in_thread

class FunctionDepositer:
    def __init__(self, api_key, model):
        self.ai = DepositerAI(api_key, model)

    def deposit_function(self, project_name, c_source, header_source=None):
        project_dir = ensure_project_dir('DAITK_data', project_name)
        file_tree = build_file_tree(project_dir)
        prompt = build_placement_prompt(file_tree, c_source, header_source)
        
        def on_placement_suggestion(placement_suggestion):
            print('AI file placement suggestion:')
            print(placement_suggestion)
            user_file_choice = input('Enter the file path to use (or press Enter to accept AI suggestion): ').strip()
            if not user_file_choice:
                user_file_choice = extract_file_from_suggestion(placement_suggestion)
            file_path = os.path.join(project_dir, user_file_choice)
            file_content = read_file_content(file_path)
            insert_prompt = build_insert_prompt(file_content, c_source, header_source)
            def on_insert_suggestion(insert_suggestion):
                print('AI insertion suggestion:')
                print(insert_suggestion)
                # User can confirm or edit placement here
                # (File writing can be added later)
            run_in_thread(self.ai.ask, args=(insert_prompt,), callback=on_insert_suggestion)
        run_in_thread(self.ai.ask, args=(prompt,), callback=on_placement_suggestion)

if __name__ == '__main__':
    api_key = "AIzaSyDIkQe9MOnjVxcbF56bVASvXSNifdDGQlU"
    model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    depositer = FunctionDepositer(api_key, model)
    print('--- Function Depositer ---')
    project = input('Enter project name: ').strip()
    print('Paste C source code (end with a line containing only ".end"):')
    c_lines = []
    while True:
        line = input()
        if line.strip() == '.end':
            break
        c_lines.append(line)
    c_source = '\n'.join(c_lines)
    header_source = None
    if input('Do you have a header file to deposit? (y/n): ').strip().lower() == 'y':
        print('Paste header source code (end with a line containing only ".end"):')
        h_lines = []
        while True:
            line = input()
            if line.strip() == '.end':
                break
            h_lines.append(line)
        header_source = '\n'.join(h_lines)
    depositer.deposit_function(project, c_source, header_source) 