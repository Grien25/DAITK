from src.llm_interface import get_llm

class DepositerAI:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.llm = get_llm('gemini', api_key=api_key, model=model)

    def ask(self, prompt):
        # Use the Gemini LLM for all calls
        return self.llm._call_gemini_api(prompt) 