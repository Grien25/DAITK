from assembly_parser import extract_functions_from_asm
from llm_interface import get_llm
from typing import List, Dict, Optional
from file_placement import place_decompiled_function

def decompile_asm_file(file_path: str, llm_backend: str, llm_kwargs: Optional[Dict] = None) -> List[Dict]:
    """
    Loads a .s file, extracts functions, sends each to the LLM, and returns decompiled results.
    Also places each decompiled function in the correct file.
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
        # Place the decompiled function in the correct file
        place_decompiled_function(func['name'], decompiled)
    return results 