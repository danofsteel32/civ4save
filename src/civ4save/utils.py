import platform
from pathlib import Path


def unenumify(e) -> str:
    strip_leading = str(e).split("_")[1:]
    return " ".join(strip_leading).title()


def get_game_dir() -> Path:
    leaf = "Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword"
    possible_locations = [
        Path("C:\Program Files (x86)") / leaf,
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
        saves_dir = Path.home() / "Documents" / "My Games" / "beyond the sword" / "Saves" / sub_dir
    else:
        saves_dir =  Path.home().joinpath(
        ".local/share/Steam/steamapps/compatdata",
        "8800/pfx/drive_c/users/steamuser",
        "My Documents/My Games/Beyond the Sword/Saves",
        sub_dir
        )
    if not saves_dir.exists():
        raise FileNotFoundError("Could not locate saves directory.")
    return saves_dir


def clear_auto_saves():
    auto_saves = get_saves_dir() / "single/auto"
    for save in auto_saves.iterdir():
        print(save.name)
        save.unlink()
