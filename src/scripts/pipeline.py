#!/usr/bin/env python3
"""AI-assisted decompilation pipeline prototype (stage 1).

Stage 1 implements a very small batch pipeline.  The script iterates
over all ``.s`` files in :mod:`asm/` and performs the following steps
for each function:

``asm`` -> ``C`` (placeholder "LLM" generation) -> compile -> compare.

The real project will eventually hook an actual LLM and use the
CodeWarrior compiler.  For now the operations are mocked so that the
pipeline structure can be exercised in a self contained manner.
"""

import argparse
import os
import subprocess
from pathlib import Path

DEFAULT_ASM_DIR = Path(__file__).resolve().parent.parent / "asm"
DEFAULT_ORIG_OBJ_DIR = Path(__file__).resolve().parent.parent / "orig_obj"
DEFAULT_RECOMP_OBJ_DIR = Path(__file__).resolve().parent.parent / "recomp_obj"
DEFAULT_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def generate_c_from_asm(asm_path: Path) -> str:
    """Return placeholder C code for a given asm file."""
    return f"// TODO: decompiled {asm_path.name}\n"


def compile_c(c_file: Path, obj_file: Path, compiler: str) -> subprocess.CompletedProcess:
    """Compile C file into an object.  This is a thin wrapper around subprocess."""
    cmd = compiler.format(src=c_file, obj=obj_file)
    return subprocess.run(cmd, shell=True, capture_output=True)


def diff_obj(expected: Path, actual: Path) -> bool:
    """Return True if the two object files are byte-identical."""
    if not expected.exists() or not actual.exists():
        return False
    return expected.read_bytes() == actual.read_bytes()


def main(args: argparse.Namespace) -> None:
    asm_dir = Path(args.asm_dir)
    orig_obj_dir = Path(args.orig_obj_dir)
    recomp_obj_dir = Path(args.recomp_obj_dir)
    src_dir = Path(args.src_dir)
    log_dir = Path(args.log_dir)

    recomp_obj_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    summary_path = log_dir / "summary.log"
    summary_lines = []

    for asm_file in asm_dir.glob("*.s"):
        func = asm_file.stem
        c_file = src_dir / f"{func}.c"
        obj_file = recomp_obj_dir / f"{func}.o"

        # --- Generate C ---
        c_code = generate_c_from_asm(asm_file)
        c_file.write_text(c_code)

        # --- Compile ---
        result = compile_c(c_file, obj_file, args.compiler)
        if result.returncode != 0:
            summary_lines.append(f"{func},COMPILE_ERROR\n")
            continue

        # --- Diff ---
        orig_obj = orig_obj_dir / f"{func}.o"
        if diff_obj(orig_obj, obj_file):
            status = "VERIFIED"
        else:
            status = "MISMATCH"
        summary_lines.append(f"{func},{status}\n")

    if summary_lines:
        summary_path.write_text("".join(summary_lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1 decompilation pipeline")
    parser.add_argument("--asm-dir", default=DEFAULT_ASM_DIR, help="directory with .s files")
    parser.add_argument("--orig-obj-dir", default=DEFAULT_ORIG_OBJ_DIR, help="directory with original object files")
    parser.add_argument("--recomp-obj-dir", default=DEFAULT_RECOMP_OBJ_DIR, help="where to place recompiled objects")
    parser.add_argument("--src-dir", default=DEFAULT_SRC_DIR, help="where to place generated C")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR, help="where to write logs")
    parser.add_argument("--compiler", default="touch {obj}",
                        help="command to compile (use {src} and {obj} placeholders)")
    main(parser.parse_args())
