from functools import cache, partial
from pathlib import Path
from simple_term_menu import TerminalMenu

from . import save_file, structure
from .enums import vanilla as e
from .utils import unenumify


def get_save_files(directory: str):
    return [
        file
        for file in Path(directory).iterdir()
        if file.suffix == ".CivBeyondSwordSave"
    ]


def make_civs_string(data) -> str:
    strings: list[str] = []
    for n, civ in enumerate(data.civs):
        if civ == "NO_CIVILIZATION":
            return "\n".join(strings)
        civ = unenumify(civ)
        leader = unenumify(data.leaders[n])
        score = data.ai_player_score[n]
        s = f"    {score=} {leader=} {civ=}"
        if n == 0:
            s += " (player)"
        strings.append(s)
    return ""


@cache
def read_file(filename, fmt, parent):
    try:
        save_bytes = save_file.read(parent / filename)
    except save_file.NotASaveFile:
        return "Not a save file"

    data = fmt.parse(save_bytes, max_players=19)

    vict_enabled = "\n".join(
        f"    {unenumify(e.VictoryType(n))}"
        for n, v in enumerate(data.victories)
        if v
    )
    s = (
        f"turn: {data.game_turn}\n"
        "settings:\n"
        f"  difficulty: {unenumify(data.handicap)}\n"
        f"  game_speed: {unenumify(data.game_speed)}\n"
        f"  map_script: {data.map_script_name}\n"
        f"  size: {unenumify(data.world_size)}\n"
        f"  climate: {unenumify(data.climate)}\n"
        f"  sea_level: {unenumify(data.sea_level)}\n"
        f"  victories_enabled:\n{vict_enabled}\n"
        "civs:\n"
        f"{make_civs_string(data)}"
    )
    return s


def browse(save_files, fmt):
    parent = save_files[0].parent
    title = f"Browsing: {parent}"
    terminal_menu = TerminalMenu(
        [f.name for f in save_files],
        title=title,
        preview_title="Civ4Save",
        preview_command=partial(read_file, fmt=fmt, parent=parent),
        preview_size=0.75,
        clear_screen=True,
    )
    menu_entry_index = terminal_menu.show()
