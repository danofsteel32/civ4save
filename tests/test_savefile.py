import pytest

from civ4save import NotASaveFile, SaveFile


def test_bad_file():
    with pytest.raises(NotASaveFile):
        save = SaveFile("tests/saves/not-a-real.CivBeyondSwordSave")
        save.current_turn


@pytest.mark.parametrize(
    "filename,speed,civ,leader",
    [
        ("bismark-emperor-turn86.CivBeyondSwordSave", "NORMAL", "GERMANY", "BISMARCK"),
        ("churchill-random-roll.CivBeyondSwordSave", "NORMAL", "ENGLAND", "CHURCHILL"),
        ("mehmed-epic.CivBeyondSwordSave", "EPIC", "OTTOMAN", "MEHMED"),
        ("Gandhi-culture-win-t331.CivBeyondSwordSave", "NORMAL", "INDIA", "GANDHI")
    ]
)
def test_savefile(filename, speed, civ, leader):
    save = SaveFile(f"tests/saves/{filename}")
    assert save.settings.game_speed.name == f"GAMESPEED_{speed}"

    player = save.get_player(0)
    assert player.civ.name == f"CIVILIZATION_{civ}"
    assert player.leader.name == f"LEADER_{leader}"


def test_completed_game():
    save = SaveFile("tests/saves/Gandhi-culture-win-t331.CivBeyondSwordSave")
    assert save.game_state.winner == 0
    assert save.game_state.victory.name == "VICTORY_CULTURAL"
