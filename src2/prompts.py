def build_placement_prompt(file_tree, c_source, header_source=None):
    prompt = (
        "You are an expert C programmer working on a Nintendo Wii (PowerPC, 2006) codebase. "
        "All code and file organization should follow conventions for Nintendo Wii development.\n\n"
        "STRICT REQUIREMENT: All code files must be placed under the <projectname>/src/ directory. Files may be organized into subfolders inside src, but must always be within the src directory. The file extension should be .c, .h, or .cpp as appropriate. Do NOT place files outside the src directory.\n\n"
        "Given the following project file tree and a new C function (and optional header), "
        "suggest the most appropriate file for this function, considering Wii-specific conventions, file organization, and C code style.\n\n"
        "If the function is a standard library function (e.g., memcpy, memset, strcpy), place it in a canonical location such as 'src/', 'src/string/', or 'src/runtime/'. Strongly prefer general, descriptive file names (e.g., 'memory.c', 'string.c') for related functions. Do NOT create a new file for a single standard function if a general file exists or is appropriate. Do NOT create a header file for these functions unless there is a clear, project-specific reason. "
        "If multiple standard functions are provided, always group them in a general file unless there is a strong project-specific reason to split. "
        "Do NOT rewrite, reformat, or restyle the user's code. Only suggest truly trivial fixes such as missing semicolons, duplicate terms, or typos. Do NOT change whitespace, indentation, comments, or function order. If there are no such issues, respond with 'No changes needed.' Do not change logic, structure, or style unless it is a trivial fix. "
        f"Project file tree:\n{file_tree}\n\n"
        f"C source code:\n{c_source}\n\n"
    )
    if header_source:
        prompt += f"Header source code:\n{header_source}\n\n"
    prompt += (
        "Suggest the best file path (relative to the project root) to place the function(s). "
        "If no suitable file exists, suggest a new file name that fits Wii project conventions. "
        "Respond with only the file path and a brief reason."
    )
    return prompt

def extract_file_from_suggestion(suggestion):
    for line in suggestion.splitlines():
        line = line.strip()
        if line.endswith(('.c', '.h')):
            # Handle cases where the AI puts file path and reason on same line
            # Look for the first word that ends with .c or .h
            words = line.split()
            for word in words:
                if word.endswith(('.c', '.h')):
                    return word
    return 'new_file.c'

def build_insert_prompt(file_content, c_source, header_source=None):
    prompt = (
        "You are an expert C programmer working on a Nintendo Wii (PowerPC, 2006) codebase.\n"
        "Given the following file content (if any):\n" + file_content + "\n\n"
        "And the function(s) to insert:\n" + c_source + "\n\n"
    )
    if header_source:
        prompt += "Header function(s):\n" + header_source + "\n\n"
    prompt += (
        "Append the new function(s) to the end of the file, after all existing code. Do NOT remove, replace, or duplicate any existing code. Only add the new function(s) if they do not already exist. "
        "If the function already exists in the file, do not add it again. "
        "If you provide the full updated file, clearly mark the start and end of the file content with '---START FILE---' and '---END FILE---'. "
        "Always provide a brief reason for your choice."
    )
    return prompt

def build_code_checkbox_prompt(file_content, filename):
    prompt = (
        f"You are an expert C programmer and code reviewer for a Nintendo Wii (PowerPC, 2006) project. "
        f"Review the following file ('{filename}') for correctness, style, and integration after a recent function insertion. "
        f"You must NOT rewrite, reformat, or restyle the code. Only fix truly trivial issues:\n"
        f"- Missing semicolons\n"
        f"- Duplicate includes or declarations\n"
        f"- Missing closing braces\n"
        f"- Simple typos or syntax errors\n"
        f"- Logic errors in loop conditions or pointer arithmetic\n"
        f"- Unused variables or unreachable code\n"
        f"Do NOT change whitespace, indentation, comments, or function order unless fixing a syntax error. "
        f"If there are no such issues, respond with 'No changes needed.' Do not change logic, structure, or style unless it is a trivial fix. "
        f"If you find any issues or improvements, return the full updated file between ---START FILE--- and ---END FILE---. "
        f"If no changes are needed, respond with 'No changes needed.'\n\n"
        f"File content:\n{file_content}\n"
    )
    return prompt


def build_project_stability_prompt(file_tree, file_summaries):
    prompt = (
        "You are an expert C project architect for a Nintendo Wii (PowerPC, 2006) codebase. "
        "All code and file organization should follow conventions for Nintendo Wii development.\n\n"
        "Review the following project file tree and file summaries. "
        "You may move, rename, delete, or rewrite any file for better organization, clarity, or convention. Strongly prefer general, descriptive file names (e.g., 'memory.c', 'string.c') for related functions. Do NOT create a new file for a single standard function if a general file exists or is appropriate. Do NOT create a header file for these functions unless there is a clear, project-specific reason. If multiple standard functions are provided, always group them in a general file unless there is a strong project-specific reason to split. "
        "For any file you want to change, provide the full new file content between ---FILE: <relative/path>--- and ---END FILE---. "
        "For moves/renames, specify the old and new paths. For deletions, specify the file to delete. "
        "If no changes are needed, respond with 'No changes needed.'\n\n"
        f"Project file tree:\n{file_tree}\n\n"
        f"File summaries:\n{file_summaries}\n"
    )
    return prompt 