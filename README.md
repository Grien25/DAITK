# AI-Assisted Decompilation Pipeline

## Architecture Overview

The pipeline sequentially transforms PowerPC assembly into C code and verifies correctness:

```
[ Decomp-Toolkit (.s ASM + .o object per function) ]
                │
                ▼
[ LLM Decompiler (ASM to C) ]
                │
                ▼
[ MWCC PPC Compiler ]
                │
                ▼
[ objdiff Comparison ]
    ├── Identical → Verified ✅
    └── Mismatch → Log Differences 🔍
```

Each function from the binary is decompiled and recompiled individually. A verified match requires byte-for-byte equivalence.

## Toolchain Setup

### Required Tools

1. **Decomp-Toolkit (dtk)**

   * Version: 1.6.1+
   * Install: `cargo install decomp-toolkit` or GitHub binary.
   * Usage: `dtk elf disasm --out asm_folder game.dol`

2. **Metrowerks CodeWarrior PPC Compiler (MWCC)**

   * Version: Wii 1.7 (CodeWarrior 4.3 build 213)
   * Files: `mwcceppc.exe`, `mwldeppc.exe`
   * Location: Place in a known directory (`compilers/mwcc_43_213/`)

3. **LLM Model & Runtime** (local)

   * GPT4All: `pip install gpt4all`, download a compatible model.
   * StarCoder/Transformers: `pip install transformers accelerate`
   * Alternative: OpenAI API (requires API key)

4. **objdiff**

   * Version: 3.0.0-beta.8+
   * Download CLI: GitHub releases (`objdiff-cli.exe`)

5. **Additional Tools**

   * Python 3.10+
   * Standard libraries: subprocess, filecmp
   * Optional: Ninja, sjiswrap (if Shift-JIS encoding required)

### Installation Steps Summary

1. Install `decomp-toolkit`
2. Obtain and set up MWCC compiler
3. Install `objdiff-cli`
4. Set up LLM (local or API)
5. Create a working directory structure:

```
asm/         (DTK output)
orig_obj/    (original objects)
recomp_obj/  (recompiled objects)
src/         (AI-generated C)
logs/        (diff/build logs)
scripts/     (automation scripts)
```

## Prompt Templates

### Template 1: Basic Prompt

````
You are an expert C programmer and decompiler. Convert the PowerPC assembly below into equivalent C. Ensure identical compilation by MWCC. Keep readable structure.

Assembly:
============ ASM BEGIN ============
<INSERT ASM TEXT>
============ ASM END ==============

```C
// Output valid C code here
````

### Template 2: Enhanced Context

```
Function: foo_bar
Likely signature: int foo_bar(int count, float value)

Context:
- Calls OSReport
- Accesses global GameState

Assembly:
<ASM instructions>

Preserve exact control flow and semantics.
```

## Orchestration Script

### Python Workflow

````python
import os, subprocess, filecmp
from pathlib import Path
from gpt4all import GPT4All

MWCC_PATH = r"C:\path\to\mwcceppc.exe"
COMPILER_FLAGS = ["-proc", "gekko", "-O4,p", "-nodefaults"]
INCLUDE_DIRS = [r"C:\path\to\include"]

llm = GPT4All("gpt4all-model.bin")

asm_dir, orig_obj_dir = Path("asm"), Path("orig_obj")
recomp_obj_dir, src_dir, log_path = Path("recomp_obj"), Path("src"), Path("logs/mismatch_log.txt")

os.makedirs(recomp_obj_dir, exist_ok=True)
os.makedirs(src_dir, exist_ok=True)
os.makedirs(log_path.parent, exist_ok=True)

summary = {"verified": 0, "mismatch": 0, "compile_error": 0}

with open(log_path, "w") as log_file:
    for asm_file in asm_dir.glob("*.s"):
        func_name = asm_file.stem
        orig_obj = orig_obj_dir / f"{func_name}.o"
        if not orig_obj.exists(): continue

        prompt = f"Convert PowerPC assembly to C:\nFunction: {func_name}\nAssembly:\n{asm_file.read_text()}\n```C\n"
        generated_c = llm.generate(prompt, max_tokens=500, temp=0.2).strip()

        c_path = src_dir / f"{func_name}.c"
        c_path.write_text(generated_c)

        obj_path = recomp_obj_dir / f"{func_name}.o"
        compile_cmd = [MWCC_PATH] + COMPILER_FLAGS + ["-c", str(c_path), "-o", str(obj_path)]
        for inc in INCLUDE_DIRS: compile_cmd += ["-i", inc]
        result = subprocess.run(compile_cmd, capture_output=True)

        if result.returncode or not obj_path.exists():
            log_file.write(f"{func_name}: COMPILE_ERROR {result.stderr}\n")
            summary["compile_error"] += 1
            continue

        if filecmp.cmp(orig_obj, obj_path):
            summary["verified"] += 1
        else:
            log_file.write(f"{func_name}: MISMATCH\n")
            summary["mismatch"] += 1

print(summary)
````

## Parallelization Tips

* **Multi-process:** Spawn multiple LLM instances
* **Async API:** Concurrent requests (if API-based)
* **Batching & Filtering:** Skip trivial functions, batch requests

## Validation and Logging

* **Diff Verification:** Byte-exact match required
* **Logging:** Mismatches, compile errors, prompt output
* **Manual Review:** objdiff GUI for detailed inspection
* **Continuous Integration:** Integrate verified C files into codebase

## Directory Summary

```
asm/
orig_obj/
recomp_obj/
src/
logs/
scripts/
```

This structured pipeline enables robust and verified assembly-to-C decompilation leveraging automated AI-assisted tools and detailed verification processes.
