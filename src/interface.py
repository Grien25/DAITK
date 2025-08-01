import argparse
from decompiler import decompile_asm_file

def main():
    parser = argparse.ArgumentParser(description="AI Decompiler for Assembly Functions")
    parser.add_argument('asm_file', help="Path to the .s assembly file")
    parser.add_argument('--backend', choices=['local', 'gemini'], default='local', help="LLM backend to use")
    parser.add_argument('--model-path', help="Path to local LLM model (if using local backend)")
    parser.add_argument('--api-key', help="Gemini API key (if using Gemini backend)")
    parser.add_argument('--model', default='gemini-pro', help="Gemini model to use")
    parser.add_argument('--function', help="Only decompile the specified function")
    args = parser.parse_args()

    llm_kwargs = {}
    if args.backend == 'local' and args.model_path:
        llm_kwargs['model_path'] = args.model_path
    if args.backend == 'gemini':
        if args.api_key:
            llm_kwargs['api_key'] = args.api_key
        llm_kwargs['model'] = args.model

    target_funcs = [args.function] if args.function else None
    results = decompile_asm_file(args.asm_file, args.backend, llm_kwargs, target_funcs)
    for func in results:
        print(f"\nFunction: {func['name']} (lines {func['start_line']}-{func['end_line']})")
        print("Assembly:\n" + func['asm_code'])
        print("Decompiled:\n" + func['decompiled_code'])

if __name__ == '__main__':
    main() 