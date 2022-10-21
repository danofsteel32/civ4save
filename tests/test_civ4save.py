import pytest

from civ4save import Context, SaveFile, __version__

MAX_PLAYERS = 19


def test_version():
    assert __version__ == "0.6.3"


@pytest.mark.parametrize("file", [
    "tests/saves/Gandhi-culture-win-t331.CivBeyondSwordSave",
])
def test_parse(file):
    context = Context(max_players=19)
    save = SaveFile(file, context)
    save.parse()

    assert save.settings.start_year == -4000
    assert save.settings.game_options["GAMEOPTION_NO_VASSAL_STATES"]
    assert save.settings.game_speed.name == "GAMESPEED_NORMAL"

    assert save.game_state.winner == 0
    assert save.game_state.victory.name == "VICTORY_CULTURAL"
    assert len(save.game_state.scores) == save.settings.num_civs
    assert "Plato" in save.game_state.great_people_born

    player = save.get_player(0)
    assert player.civ.name == "CIVILIZATION_INDIA"
    assert player.leader.name == "LEADER_GANDHI"
    assert "Hollywood" in player.cities[0].wonders
