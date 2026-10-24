from pathlib import Path

import pytest

from civ4save import NotASaveFile, SaveFile

SAVE_DIR = Path(__file__).parent / "saves"


def test_bad_file():
    with pytest.raises(NotASaveFile):
        save = SaveFile(SAVE_DIR / "not-a-real.CivBeyondSwordSave")
        _ = save.current_turn


@pytest.mark.parametrize(
    "filename,speed,civ,leader",
    [
        ("bismark-emperor-turn86.CivBeyondSwordSave", "NORMAL", "GERMANY", "BISMARCK"),
        ("churchill-random-roll.CivBeyondSwordSave", "NORMAL", "ENGLAND", "CHURCHILL"),
        ("mehmed-epic.CivBeyondSwordSave", "EPIC", "OTTOMAN", "MEHMED"),
        ("Gandhi-culture-win-t331.CivBeyondSwordSave", "NORMAL", "INDIA", "GANDHI"),
    ],
)
def test_savefile(filename, speed, civ, leader):
    save = SaveFile(SAVE_DIR / filename)
    assert save.settings.game_speed.name == f"GAMESPEED_{speed}"

    player = save.get_player(0)
    assert player.civ.name == f"CIVILIZATION_{civ}"
    assert player.leader.name == f"LEADER_{leader}"


def test_completed_game():
    save = SaveFile(SAVE_DIR / "Gandhi-culture-win-t331.CivBeyondSwordSave")
    assert save.game_state.winner == 0
    assert save.game_state.victory.name == "VICTORY_CULTURAL"


@pytest.mark.parametrize(
    "filename",
    [
        "bismark-emperor-turn86.CivBeyondSwordSave",
        "churchill-random-roll.CivBeyondSwordSave",
        "mehmed-epic.CivBeyondSwordSave",
        "Gandhi-culture-win-t331.CivBeyondSwordSave",
    ],
)
def test_plot_stream_is_complete_and_row_major(filename):
    save = SaveFile(SAVE_DIR / filename)
    grid_width, grid_height = save.map_size

    assert len(save.raw.plots) == grid_width * grid_height
    assert [(plot.x, plot.y) for plot in save.raw.plots] == [
        (x, y) for y in range(grid_height) for x in range(grid_width)
    ]
