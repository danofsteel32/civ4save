"""Misc. classes and functions that are used by other modules."""

import json
import platform
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterator, Tuple

import xmltodict


class CustomJsonEncoder(json.JSONEncoder):
    """Enable serializing dataclasses and Enums."""

    def default(self, obj):
        """Override default."""
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, Enum):
            return obj.name
        return super().default(obj)


def renderable_filepath(path: Path) -> str:
    """Wrap the path so can be pretty-printed by `rich` even if spaces in path.

    Args:
        path (Path): Path to make renderable.

    Returns:
        str: The string representation of `path` with `repr.path` formatting.
    """
    return f"[repr.path]{str(path)}[/repr.path]"


def calc_plot_index(grid_width: int, x: int, y: int) -> int:
    """Calculate array index of a coordinate pair (x, y) based on grid size.

    Args:
        grid_width (int): Width of the map.
        x (int): X coordinate
        y (int): Y coordinate

    Returns:
        int: The array index of the coordinate.
    """
    index = (grid_width * y) + x
    return index


def next_plot(
    x: int, y: int, grid_width: int, grid_height: int
) -> Tuple[int, int]:
    """Return the next coordinate pair (x, y) taking into account grid size.

    Args:
        x (int): X coordinate
        y (int): Y coordinate
        grid_width (int): Width of the map.
        grid_height (int): Height of the map.

    Returns:
        tuple[int, int]: (x, y) pair of the next plot in array.
    """
    next_x, next_y = x + 1, y

    if x == grid_width - 1:
        next_x = 0
        next_y = y + 1
    return next_x, next_y


def get_enum_length(e: Enum) -> int:
    """Ignore the negative value member of the enum when getting member count.

    Args:
        e (Enum): The enum to calculate number of members of.

    Returns:
        int: Number of members.
    """
    return len([m for m in e.__members__ if e[m].value >= 0])  # type: ignore


def unenumify(name: str) -> str:
    """Transform enum member name to titlized string.

    Args:
        name (str): Enum member name.

    Returns:
        str: Titlized string with underscores replaced by spaces.
    """
    strip_leading = str(name).split("_")[1:]
    return " ".join(strip_leading).title()


def get_game_dir() -> Path:
    """Look in various places for the Civ4 BTS game directory.

    Returns:
        Path: The found game directory.

    Raises:
        FileNotFoundError: If no game directory could be found.
    """
    leaf = "Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword"
    possible_locations = [
        Path(r"C:\Program Files (x86)") / leaf,
        Path.home() / ".var/app/com.valvesoftware.Steam/data" / leaf,
        Path.home() / ".local/share" / leaf,
    ]
    for p in possible_locations:
        if p.exists():
            return p
    else:
        raise FileNotFoundError("Could not locate BTS game directory")


def get_saves_dir(sub_dir: str = "single") -> Path:
    """Look in various places for the Civ4 BTS saves directory.

    Returns:
        Path: The found saves directory.

    Raises:
        FileNotFoundError: If no saves directory could be found.
    """
    if platform.system() == "Windows":
        saves_dir = (
            Path.home()
            / "Documents"
            / "My Games"
            / "beyond the sword"
            / "Saves"
            / sub_dir
        )
    else:
        saves_dir = Path.home().joinpath(
            ".local/share/Steam/steamapps/compatdata",
            "8800/pfx/drive_c/users/steamuser",
            "My Documents/My Games/Beyond the Sword/Saves",
            sub_dir,
        )
    if not saves_dir.exists():
        raise FileNotFoundError("Could not locate saves directory.")
    return saves_dir


def get_xml_dir() -> Path:
    """Look in various places for the Civ4 BTS XML directory.

    Returns:
        Path: The found XML directory.

    Raises:
        FileNotFoundError: If no XML directory could be found.
    """
    game_dir = get_game_dir()
    bts_xml = game_dir / "Beyond the Sword" / "Assets" / "XML"
    if not bts_xml.exists():
        raise FileNotFoundError("Could not locate XML directory")
    return bts_xml


def clear_auto_saves() -> None:
    """Delete all autosaves."""
    auto_saves = get_saves_dir() / "single/auto"
    for save in auto_saves.iterdir():
        print(save.name)
        save.unlink()


def get_xml_text_files() -> Iterator[Path]:
    """Iterator of all XML/Text files."""
    game_dir = get_game_dir()
    expansions = ["", "Warlords", "Beyond the Sword"]
    stem = "Assets/XML/Text"
    for expansion in expansions:
        text_dir = game_dir / expansion / stem
        if text_dir.exists():
            for file in text_dir.iterdir():
                yield file


def make_text_map(lang: str = "English") -> Dict[str, str]:
    """Create a Dict mapping TEXT_KEY* to human readable text in language `lang`.

    Works from vanilla to Warlords to BTS so the most recent occurence of a
    TEXT_KEY will be the one in the mapping.

    Args:
        lang (str): Language to map. Defaults to 'English'.

    Returns:
        Dict[str, str]: Dictionary of TEXT_KEY* to text.
    """
    text_map = {}
    for file in get_xml_text_files():
        with open(file, mode="r", encoding="ISO-8859-1") as f:
            data = xmltodict.parse(f.read(), encoding="ISO-8859-1")
        try:
            data["Civ4GameText"]["TEXT"]
        except KeyError:
            continue
        for text in data["Civ4GameText"]["TEXT"]:
            tag, name = text["Tag"], text[lang]
            try:
                new_name = name.get("Text", None)
            except AttributeError:
                text_map[tag] = name
                continue
            text_map[tag] = new_name
    return text_map
