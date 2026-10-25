from collections import Counter
from pathlib import Path

import pytest

from civ4save import NotASaveFile, SaveFile

SAVE_DIR = Path(__file__).parent / "saves"


def test_bad_file():
    with pytest.raises(NotASaveFile) as exc_info:
        save = SaveFile(SAVE_DIR / "not-a-real.CivBeyondSwordSave")
        _ = save.current_turn
    assert isinstance(exc_info.value.__cause__, NotASaveFile)


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
    "filename,num_areas,areas_end,init_core_end,map_start",
    [
        ("bismark-emperor-turn86.CivBeyondSwordSave", 36, 1316822, 1527, 31108),
        ("churchill-random-roll.CivBeyondSwordSave", 13, 881418, 1501, 11158),
        ("mehmed-epic.CivBeyondSwordSave", 21, 2376410, 1511, 119882),
        ("Gandhi-culture-win-t331.CivBeyondSwordSave", 21, 1361972, 1491, 78966),
    ],
)
def test_plot_stream_is_complete_and_row_major(
    filename, num_areas, areas_end, init_core_end, map_start
):
    save = SaveFile(SAVE_DIR / filename)
    grid_width, grid_height = save.map_size

    assert save.raw._header_end_index == save.raw._init_core_start_index == 40
    assert save.raw._init_core_end_index == init_core_end
    assert save.raw._game_start_index == init_core_end + 8
    assert save.raw._game_end_index + 8 == save.raw._game_ai_end_index == map_start
    assert save.raw._map_start_index == map_start
    assert save.raw._map_end_index == areas_end

    assert len(save.raw.plots) == grid_width * grid_height
    assert [(plot.x, plot.y) for plot in save.raw.plots] == [
        (x, y) for y in range(grid_height) for x in range(grid_width)
    ]

    areas = save.raw.areas
    assert len(areas) == save.raw.sz_areas == num_areas
    assert save.raw._areas_end_index == areas_end
    assert len({area.area_id for area in areas}) == len(areas)
    assert Counter(plot.area_id for plot in save.raw.plots) == {
        area.area_id: area.num_tiles for area in areas
    }
    assert sum(area.num_tiles for area in areas) == grid_width * grid_height
    assert (
        sum(area.num_tiles for area in areas if not area.water) == save.raw.land_plots
    )
    assert sum(area.num_owned_tiles for area in areas) == save.raw.owned_plots
