import re
from typing import List, Dict

def extract_functions_from_asm(file_path: str) -> List[Dict]:
    """
    Parses a .s assembly file and extracts functions delimited by .fn and .endfn.
    Returns a list of dicts: { 'name': str, 'code': str, 'start_line': int, 'end_line': int }
    """
    functions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    func_start = None
    func_name = None
    for i, line in enumerate(lines):
        fn_match = re.match(r'\.fn\s+([A-Za-z_][A-Za-z0-9_]*)', line)
        endfn_match = re.match(r'\.endfn\s+([A-Za-z_][A-Za-z0-9_]*)', line)
        if fn_match:
            func_start = i
            func_name = fn_match.group(1)
        elif endfn_match and func_start is not None and func_name == endfn_match.group(1):
            # Include both .fn and .endfn lines
            functions.append({
                'name': func_name,
                'code': ''.join(lines[func_start:i+1]),
                'start_line': func_start + 1,
                'end_line': i + 1
            })
            func_start = None
            func_name = None
    return functions 