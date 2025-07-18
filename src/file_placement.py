import os
import re

# Example mapping; expand as needed
FUNC_TO_FILE = {
    "memcpy": "sdk/PowerPC_EABI_Support/Runtime/__mem.c",
    "memset": "sdk/PowerPC_EABI_Support/Runtime/__mem.c",
    "__fill_mem": "sdk/PowerPC_EABI_Support/Runtime/__mem.c",
    # Add more mappings as needed
}

FUNC_TO_HEADER = {
    "memcpy": "sdk/PowerPC_EABI_Support/Runtime/__mem.h",
    "memset": "sdk/PowerPC_EABI_Support/Runtime/__mem.h",
    "__fill_mem": "sdk/PowerPC_EABI_Support/Runtime/__mem.h",
    # Add more mappings as needed
}

def place_decompiled_function(func_name, decompiled_code, base_dir="DecompReference/auto/src/"):
    rel_path = FUNC_TO_FILE.get(func_name)
    if not rel_path:
        # Fallback: put in a generic file or ask user
        rel_path = "misc/unknown.c"
    abs_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    # Insert or replace function in file
    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Replace if function exists, else append
        func_pattern = re.compile(rf"(void\s+{re.escape(func_name)}\s*\(.*?\)\s*\{{.*?^\}})", re.DOTALL | re.MULTILINE)
        if func_pattern.search(content):
            content = func_pattern.sub(decompiled_code, content)
        else:
            content += "\n\n" + decompiled_code
    else:
        # Add a basic include if new file
        header_rel = FUNC_TO_HEADER.get(func_name)
        if header_rel:
            include_line = f'#include "{os.path.basename(header_rel)}"\n\n'
        else:
            include_line = ''
        content = f'{include_line}{decompiled_code}\n'
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    # Optionally update header
    update_header(func_name, decompiled_code, base_dir)

def update_header(func_name, decompiled_code, base_dir):
    header_rel = FUNC_TO_HEADER.get(func_name)
    if not header_rel:
        return
    abs_header = os.path.join(base_dir, header_rel)
    os.makedirs(os.path.dirname(abs_header), exist_ok=True)
    # Extract prototype from decompiled_code (simple heuristic)
    proto_match = re.match(r"([\w\s\*]+\s+" + re.escape(func_name) + r"\s*\(.*?\))", decompiled_code, re.DOTALL)
    if not proto_match:
        return
    prototype = proto_match.group(1).strip()
    # Add semicolon if missing
    if not prototype.endswith(';'):
        prototype += ';'
    # Add to header if not present
    if os.path.exists(abs_header):
        with open(abs_header, "r", encoding="utf-8") as f:
            header_content = f.read()
        if prototype not in header_content:
            # Insert before #endif if present
            if '#endif' in header_content:
                header_content = header_content.replace('#endif', f'{prototype}\n\n#endif')
            else:
                header_content += f'\n{prototype}\n'
    else:
        guard = os.path.basename(abs_header).replace('.', '_').upper()
        header_content = f'#ifndef {guard}\n#define {guard}\n\n{prototype}\n\n#endif // {guard}\n'
    with open(abs_header, "w", encoding="utf-8") as f:
        f.write(header_content) 