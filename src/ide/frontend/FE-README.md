# Frontend

UI code for the prototype IDE. The Tkinter app (`gui.py`) now
handles the first steps of setting up the project:

1. Select a Wii ISO and extract it with `wwt` into `Documents/DAITK-Data/dtk-template/orig/GAMEID`.
2. Rename the placeholder `GAMEID` once the extraction succeeds.
3. Optionally run `stage1.py` to split the `main.dol` using `decomp-toolkit`.
4. Open `config.yml` or `build.sha1` in your editor from the GUI to tweak paths
   or modules, then run `configure.py` to create `build.ninja`.

If the `EDITOR` environment variable is not set, the GUI will try to open
those files in VS Code or a basic editor like Wordpad/TextEdit.

Run it with:

```bash
python3 gui.py
```

The GUI will ask for your game ISO and (if needed) the path to
`decomp-toolkit`. Heavy operations such as extraction and Stage 1 run in
background threads so the window remains responsive. After extracting the
ISO you can rename the project GameID, view the SHA-1 of `main.dol`, edit
the configuration files, run Stage 1, and finally execute `configure.py`
to set up the build.
