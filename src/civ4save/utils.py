import json
import platform
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path

import xmltodict


class CustomJsonEncoder(json.JSONEncoder):
    """
    Enables serializing dataclasses and Enums
    """

    def default(self, obj):  # type: ignore
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, Enum):
            return obj.name
        return super().default(obj)


def renderable_filepath(path: Path) -> str:
    return f"[repr.path]{str(path)}[/repr.path]"


def calc_plot_index(grid_width: int, x: int, y: int) -> int:
    index = (grid_width * y) + x
    return index


def next_plot(
    x: int, y: int, grid_width: int, grid_height: int
) -> tuple[int, int]:
    next_x, next_y = x + 1, y

    if x == grid_width - 1:
        next_x = 0
        next_y = y + 1
    return next_x, next_y


def get_enum_length(e: Enum) -> int:
    """
    Ignores the negative value members of the enum because we don't want to
    count the NO_<something> = -1
    """
    return len([m for m in e.__members__ if e[m].value >= 0])  # type: ignore


def unenumify(name: str) -> str:
    strip_leading = str(name).split("_")[1:]
    return " ".join(strip_leading).title()


def get_game_dir() -> Path:
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
    game_dir = get_game_dir()
    bts_xml = game_dir / "Beyond the Sword" / "Assets" / "XML"
    if not bts_xml.exists():
        raise FileNotFoundError("Could not locate XML directory")
    return bts_xml


def clear_auto_saves() -> None:
    auto_saves = get_saves_dir() / "single/auto"
    for save in auto_saves.iterdir():
        print(save.name)
        save.unlink()


def make_text_map(files: list[Path], lang: str = "English") -> dict[str, str]:
    """
    Read these files and create a mapping of the TXT_KEY -> <lang> value.
        CIV4GameTextInfos_Cities.xml
        CIV4GameText_Cities_BTS.xml
        CIV4GameTextInfos_Objects.xml
        CIV4GameText_Warlords_Objects.xml
        CIV4GameText_Objects_BTS.xml
    """

    text_map = {}
    for file in files:
        with open(file, mode="r", encoding="ISO-8859-1") as f:
            data = xmltodict.parse(f.read(), encoding="ISO-8859-1")
        for text in data["Civ4GameText"]["TEXT"]:
            tag, name = text["Tag"], text[lang]
            try:
                new_name = name.get("Text", None)
            except AttributeError:
                text_map[tag] = name
                continue
            text_map[tag] = new_name
    return text_map


# if __name__ == "__main__":
#     files = [f for f in Path("xml").iterdir() if "Text" in f.name]
#     text_map = make_text_map(files)
#     print(json.dumps(text_map, indent=4))
