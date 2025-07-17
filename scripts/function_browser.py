from __future__ import annotations

from pathlib import Path
import asyncio

from nicegui import ui


def parse_functions(path: Path):
    """Return a list of (name, start_idx, end_idx) for functions in the file."""
    lines = path.read_text().splitlines()
    funcs = []
    name = None
    start = 0
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('.fn '):
            if name is not None:
                funcs.append((name, start, idx))
            parts = stripped.split()
            name = parts[1].rstrip(',') if len(parts) > 1 else f'func_{idx}'
            start = idx
        elif stripped.startswith('.endfn') and name is not None:
            funcs.append((name, start, idx + 1))
            name = None
    if name is not None:
        funcs.append((name, start, len(lines)))
    return funcs, lines


class Browser:
    def __init__(self) -> None:
        self.folder = ui.input('ASM folder').props('dense')
        ui.button('Scan', on_click=self.scan)
        self.filter = ui.input('Filter files').props('dense').on('keydown.enter', self.scan)
        self.message = ui.label('')
        self.spinner = ui.spinner().props('size=md').props('color=primary')
        self.spinner.set_visibility(False)

        with ui.row():
            self.file_table = ui.table(columns=[{'name': 'file', 'label': 'ASM File', 'field': 'file'}],
                                       rows=[], row_key='id', selection='single').on('select', self.load_file)
            self.func_table = ui.table(columns=[{'name': 'func', 'label': 'Function', 'field': 'func'}],
                                        rows=[], row_key='id', selection='single').on('select', self.show_function)

        self.functions: list[tuple[str, int, int]] = []
        self.lines: list[str] = []

    async def _scan_files(self, folder: Path, filt: str):
        files = [f.name for f in sorted(folder.glob('*.s')) if not filt or filt in f.name.lower()]
        return [{'id': i, 'file': name} for i, name in enumerate(files)]

    async def scan(self) -> None:
        folder = Path(self.folder.value)
        if not folder.is_dir():
            self.message.text = 'Invalid folder'
            return
        self.message.text = 'Scanning files...'
        self.spinner.set_visibility(True)
        files = await asyncio.get_event_loop().run_in_executor(None, self._scan_files, folder, self.filter.value.lower())
        self.file_table.rows = files
        self.func_table.rows = []
        self.spinner.set_visibility(False)
        self.message.text = ''

    async def _parse_file(self, path: Path):
        funcs, lines = parse_functions(path)
        rows = [{'id': i, 'func': name} for i, (name, _s, _e) in enumerate(funcs)]
        return rows, funcs, lines

    async def load_file(self, e):
        sel = e.selection
        if not sel:
            return
        filename = sel[0]['file']
        file_path = Path(self.folder.value) / filename
        self.message.text = 'Parsing functions...'
        self.spinner.set_visibility(True)
        rows, funcs, lines = await asyncio.get_event_loop().run_in_executor(None, self._parse_file, file_path)
        self.func_table.rows = rows
        self.functions = funcs
        self.lines = lines
        self.spinner.set_visibility(False)
        self.message.text = ''

    async def show_function(self, e):
        sel = e.selection
        if not sel:
            return
        idx = int(sel[0]['id'])
        name, start, end = self.functions[idx]
        asm_text = '\n'.join(self.lines[start:end])
        with ui.dialog() as dialog:
            with ui.card():
                ui.label(name)
                ui.textarea(asm_text).props('readonly autogrow').classes('w-full')
                ui.button('Close', on_click=dialog.close)
        dialog.open()


if __name__ == '__main__':
    Browser()
    ui.run(title='Assembly Browser')
