#!/usr/bin/env python3
"""Stage 1 – Dtk Template Integration helper.

This script wraps ``decomp-toolkit`` to generate the initial ``asm/`` and
``orig_obj/`` folders used by later stages of the pipeline. The
disassembly output lives in the user's ``Documents/DAITK-Data`` folder so
the data is kept alongside the extracted game files. The script simply
runs ``dtk elf disasm`` on the provided game binary and copies the
resulting assembly and objects into those directories.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


# All disassembly output is placed in the user's Documents folder so it can live
# alongside the extracted game files and template tools.
DATA_ROOT = Path.home() / "Documents" / "DAITK-Data"
ASM_DIR = DATA_ROOT / "asm"
ORIG_OBJ_DIR = DATA_ROOT / "orig_obj"


def run_disasm(dtk: Path, binary: Path, out: Path) -> None:
    """Invoke `dtk elf disasm` to split the binary."""
    cmd = [str(dtk), "elf", "disasm", str(binary), str(out)]
    subprocess.run(cmd, check=True)


def copy_results(temp: Path) -> None:
    asm_src = temp / "asm"
    obj_src = temp / "obj"
    ASM_DIR.mkdir(parents=True, exist_ok=True)
    ORIG_OBJ_DIR.mkdir(parents=True, exist_ok=True)

    if asm_src.exists():
        for asm_file in asm_src.glob("*.s"):
            shutil.copy2(asm_file, ASM_DIR / asm_file.name)
    if obj_src.exists():
        for obj_file in obj_src.glob("*.o"):
            shutil.copy2(obj_file, ORIG_OBJ_DIR / obj_file.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run decomp-toolkit disassembly")
    parser.add_argument("binary", help="Path to the game's DOL or ELF file")
    parser.add_argument("--dtk", default="dtk", help="Path to decomp-toolkit executable")
    args = parser.parse_args()

    dtk = Path(args.dtk)
    binary = Path(args.binary)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        run_disasm(dtk, binary, tmp_path)
        copy_results(tmp_path)



if __name__ == "__main__":
    main()
