# IDE Prototype

A lightweight interface for running the first steps of the
decompilation workflow.
The GUI can extract a Wii ISO with `wwt`, rename the project
`GAMEID`, and run the Stage 1 disassembly using `decomp-toolkit`.

See `frontend/gui.py` for the Tkinter-based launcher. Future stages
will expand this GUI to show diff views and integrate the AI backend.
