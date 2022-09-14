from pathlib import Path

import pytest

from civ4save import __version__, organize, save_file
from civ4save.structure import get_format

MAX_PLAYERS = 19


def test_version():
    assert __version__ == "0.4.0"


def vanilla(file):
    save_bytes = save_file.read(file)
    fmt = get_format()
    try:
        data = fmt.parse(save_bytes, max_players=MAX_PLAYERS)
    except Exception:
        return False
    return True

    organize.default(data, MAX_PLAYERS)
    organize.just_settings(data)
    organize.just_players(data, MAX_PLAYERS)
    for p in organize.player_list(data, MAX_PLAYERS):
        organize.player(data, MAX_PLAYERS, p["idx"])


def vanilla_with_plots(file):
    save_bytes = save_file.read(file)
    fmt = get_format(plots=True)
    try:
        data = fmt.parse(save_bytes, max_players=MAX_PLAYERS)
    except Exception:
        return False
    organize.with_plots(data, MAX_PLAYERS)
    return True


def test_vanilla():
    for f in Path("tests/saves").iterdir():
        if f.name == "not-a-real.CivBeyondSwordSave":
            continue
        if not vanilla(f):
            print(f"FAIL {f.name}")
            pytest.fail()


def test_vanilla_with_plots():
    for f in Path("tests/saves").iterdir():
        if f.name == "not-a-real.CivBeyondSwordSave":
            continue
        if not vanilla_with_plots(f):
            print(f"FAIL {f.name}")
            pytest.fail()


def ai_survivor(file):
    save_bytes = save_file.read(file)
    fmt = get_format(ai_survivor=True)
    try:
        data = fmt.parse(save_bytes, max_players=MAX_PLAYERS)
    except Exception:
        return False

    organize.default(data, MAX_PLAYERS)
    organize.just_settings(data)
    for p in organize.player_list(data, MAX_PLAYERS):
        organize.player(data, MAX_PLAYERS, p["idx"])
    return True


def ai_survivor_with_plots(file):
    save_bytes = save_file.read(file)
    fmt = get_format(ai_survivor=True, plots=True)
    try:
        data = fmt.parse(save_bytes, max_players=MAX_PLAYERS)
    except Exception:
        return False
    organize.with_plots(data, MAX_PLAYERS)
    return True


def test_ai_survivor():
    for f in Path("tests/S6_Saves").iterdir():
        if f.suffix != ".CivBeyondSwordSave":
            continue
        if not ai_survivor(f):
            print(f"FAIL {f.name}")
            pytest.fail()


def test_ai_survivor_with_plots():
    for f in Path("tests/S6_Saves").iterdir():
        if f.suffix != ".CivBeyondSwordSave":
            continue
        if not ai_survivor_with_plots(f):
            print(f"FAIL {f.name}")
            pytest.fail()


def test_not_save_file():
    with pytest.raises(Exception):
        save_file.read("tests/saves/not-a-real.CivBeyondSwordSave")
