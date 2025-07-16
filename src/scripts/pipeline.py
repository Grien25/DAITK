#!/usr/bin/env python3
"""AI-assisted decompilation pipeline prototype.

This script iterates over assembly files in asm/ and attempts to
produce matching object files using an LLM and CodeWarrior.
Currently it only prints the steps that would be taken.
"""
import os
from pathlib import Path

# All generated data (asm, objects, logs, etc.) lives alongside the extracted
# game files in the user's Documents folder.
DATA_ROOT = Path.home() / "Documents" / "DAITK-Data"

ASM_DIR = DATA_ROOT / "asm"
ORIG_OBJ_DIR = DATA_ROOT / "orig_obj"
RECOMP_OBJ_DIR = DATA_ROOT / "recomp_obj"
SRC_DIR = DATA_ROOT / "src"
LOG_DIR = DATA_ROOT / "logs"


def main():
    for asm_file in ASM_DIR.glob("*.s"):
        func = asm_file.stem
        print(f"[TODO] decompile {func} -> {SRC_DIR/func}.c")
        # Placeholder for LLM call and compilation steps
        # Generated C would be saved to SRC_DIR / f"{func}.c"
        # Compile with CodeWarrior and place object in RECOMP_OBJ_DIR
        # Compare against ORIG_OBJ_DIR and log result to LOG_DIR


if __name__ == "__main__":
    RECOMP_OBJ_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    main()
