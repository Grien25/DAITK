import os
from typing import Optional
import requests
import re

class BaseLLM:
    def decompile(self, asm_code: str) -> str:
        raise NotImplementedError

class LocalLLM(BaseLLM):
    def __init__(self, model_path: str):
        self.model_path = model_path
        # TODO: Initialize local LLM (e.g., llama.cpp, ollama, etc.)

    def decompile(self, asm_code: str) -> str:
        # TODO: Implement local LLM inference
        return "[Local LLM decompilation not implemented]"

class GeminiLLM(BaseLLM):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        # Use Gemini 1.5 Flash (2.0) endpoint
        self.api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key={self.api_key}"

    def decompile(self, asm_code: str) -> str:
        fn_match = re.search(r'\.fn\s+([A-Za-z_][A-Za-z0-9_]*)', asm_code)
        func_name = fn_match.group(1) if fn_match else None
        reference_code = self._find_reference_code(func_name) if func_name else None
        prompt = self._build_prompt(asm_code, reference_code)
        response = self._call_gemini_api(prompt)
        return response

    def _find_reference_code(self, func_name):
        reference_code = ""
        for root, dirs, files in os.walk("DecompReference"):
            for file in files:
                if file.endswith(('.c', '.cpp', '.h', '.hpp')):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        pattern = re.compile(rf"[\w\*\s]+\b{re.escape(func_name)}\b\s*\(.*?\)", re.DOTALL)
                        matches = pattern.findall(content)
                        if matches:
                            for match in matches:
                                idx = content.find(match)
                                snippet = content[max(0, idx-100):idx+len(match)+100]
                                reference_code += f"// From {file} in DecompReference\n{snippet}\n\n"
                                if len(reference_code) > 1200:
                                    return reference_code[:1200]
                    except Exception:
                        continue
        return reference_code or None

    def _build_prompt(self, asm_code, reference_code=None):
        prompt = (
            "Decompile the following PowerPC assembly function to C. Use idiomatic C and standard library conventions if possible.\n\n"
            f"Assembly:\n{asm_code}\n\n"
        )
        if reference_code:
            prompt += f"Reference code from project:\n{reference_code}\n\n"
        prompt += "Please output only the C code, with a function signature and comments if helpful."
        return prompt

    def _call_gemini_api(self, prompt):
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        print("Sending request to Gemini API...")
        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            print("Response status code:", resp.status_code)
            print("Response text:", resp.text[:500])
            resp.raise_for_status()
            result = resp.json()
            candidates = result.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
            return "[No response from Gemini API]"
        except Exception as e:
            print("Gemini API error:", e)
            return f"[Gemini API error: {e}]"

def get_llm(backend: str, **kwargs) -> BaseLLM:
    if backend == 'local':
        return LocalLLM(kwargs.get('model_path', ''))
    elif backend == 'gemini':
        return GeminiLLM(kwargs.get('api_key'))
    else:
        raise ValueError(f"Unknown backend: {backend}") 