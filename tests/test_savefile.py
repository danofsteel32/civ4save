import pytest

from civ4save import Context, NotASaveFile, SaveFile, __version__


def test_version():
    assert __version__ == "0.6.3"


def test_bad_file():
    with pytest.raises(NotASaveFile):
        save = SaveFile("tests/saves/not-a-real.CivBeyondSwordSave")


@pytest.mark.parametrize(
    "filename,speed,civ,leader,ai_survivor",
    [
        ("bismark-emperor-turn86.CivBeyondSwordSave", "NORMAL", "GERMANY", "BISMARCK", False),
        ("survivor-6-wildcard.CivBeyondSwordSave", "NORMAL", "NATIVE_AMERICA", "SITTING_BULL", True),
        ("churchill-random-roll.CivBeyondSwordSave", "NORMAL", "ENGLAND", "CHURCHILL", False),
        ("mehmed-epic.CivBeyondSwordSave", "EPIC", "OTTOMAN", "MEHMED", False),
        ("Gandhi-culture-win-t331.CivBeyondSwordSave", "NORMAL", "INDIA", "GANDHI", False)
    ]
)
def test_savefile(filename, speed, civ, leader, ai_survivor):
    context = Context(ai_survivor=True) if ai_survivor else None
    save = SaveFile(f"tests/saves/{filename}", context=context)
    assert save.settings.game_speed.name == f"GAMESPEED_{speed}"

    player = save.get_player(0)
    assert player.civ.name == f"CIVILIZATION_{civ}"
    assert player.leader.name == f"LEADER_{leader}"


def test_completed_game():
    save = SaveFile("tests/saves/Gandhi-culture-win-t331.CivBeyondSwordSave")
    assert save.game_state.winner == 0
    assert save.game_state.victory.name == "VICTORY_CULTURAL"
