# Frontend

UI code for the prototype IDE. The Tkinter app (`gui.py`) now
handles the first steps of setting up the project:

1. Select a Wii ISO and extract it with `wwt` into `tools/dtk-template/orig/GAMEID`.
2. Rename the placeholder `GAMEID` once the extraction succeeds.
3. Optionally run `stage1.py` to split the `main.dol` using `decomp-toolkit`.

Run it with:

```bash
python3 gui.py
```

The GUI will ask for your game ISO and (if needed) the path to
`decomp-toolkit`. After extracting the ISO you can rename the project
GameID and run Stage 1.
