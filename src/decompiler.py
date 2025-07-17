from assembly_parser import extract_functions_from_asm
from llm_interface import get_llm
from typing import List, Dict, Optional

def decompile_asm_file(file_path: str, llm_backend: str, llm_kwargs: Optional[Dict] = None) -> List[Dict]:
    """
    Loads a .s file, extracts functions, sends each to the LLM, and returns decompiled results.
    Returns a list of dicts: { 'name': str, 'asm_code': str, 'decompiled_code': str, 'start_line': int, 'end_line': int }
    """
    llm_kwargs = llm_kwargs or {}
    llm = get_llm(llm_backend, **llm_kwargs)
    functions = extract_functions_from_asm(file_path)
    results = []
    for func in functions:
        decompiled = llm.decompile(func['code'])
        results.append({
            'name': func['name'],
            'asm_code': func['code'],
            'decompiled_code': decompiled,
            'start_line': func['start_line'],
            'end_line': func['end_line']
        })
    return results 