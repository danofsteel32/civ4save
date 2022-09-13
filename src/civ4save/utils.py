from pathlib import Path


def get_game_dir() -> Path:
    leaf = "Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword"
    possible_locations = [
        Path.home() / ".var/app/com.valvesoftware.Steam/data" / leaf,
        Path.home() / ".local/share" / leaf,
    ]
    for p in possible_locations:
        if p.exists():
            return p
    else:
        raise FileNotFoundError("Could not locate XML files")


def get_saves_dir() -> Path:
    return Path.home().joinpath(
        ".local/share/Steam/steamapps/compatdata",
        "8800/pfx/drive_c/users/steamuser",
        "My Documents/My Games/Beyond the Sword/Saves"
    )


def clear_auto_saves():
    auto_saves = get_saves_dir() / "single/auto"
    for save in auto_saves.iterdir():
        print(save.name)
        save.unlink()
