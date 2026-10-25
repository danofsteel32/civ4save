import json
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from click.testing import CliRunner

from civ4save import SaveFile, __version__
from civ4save.cli import cli
from civ4save.objects import OrderType, ProductionOrder
from civ4save.objects.player import City, Civics, Trade, TradeDeal
from civ4save.vanilla import enums as e


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def parsed_save(tmp_path, monkeypatch):
    file = tmp_path / "example.CivBeyondSwordSave"
    file.touch()
    save = MagicMock(spec=SaveFile)
    save.__str__.return_value = "Synthetic save"
    save.settings = {"settings_marker": "NORMAL"}
    save.game_state = {"state_marker": 86}
    save.plots = [{"plot_marker": 1}]
    save.players = {0: {"player_marker": "Human"}}
    save.get_player.return_value = {"selected_marker": "Human"}
    constructor = Mock(return_value=save)
    monkeypatch.setattr("civ4save.cli.SaveFile", constructor)
    return file, constructor, save


def test_version(runner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"cli, version {__version__}\n"


def test_parse_requires_file(runner):
    result = runner.invoke(cli, ["parse"])
    assert result.exit_code == 2
    assert "Missing argument" in result.output


def test_parse_rejects_missing_file(runner):
    result = runner.invoke(cli, ["parse", "missing.CivBeyondSwordSave"])
    assert result.exit_code == 2
    assert "does not exist" in result.output


@pytest.mark.parametrize(
    "options,markers",
    [
        ([], ["settings_marker"]),
        (["--settings"], ["settings_marker"]),
        (["--spoilers"], ["state_marker", "plot_marker"]),
        (["--player", "0"], ["selected_marker"]),
        (["--list-players"], ["player_marker"]),
    ],
)
def test_parse_output(runner, parsed_save, options, markers):
    file, constructor, save = parsed_save
    result = runner.invoke(cli, ["parse", *options, str(file)])
    assert result.exit_code == 0, result.output
    constructor.assert_called_once_with(file=file)
    for marker in markers:
        assert marker in result.output
    if "--player" in options:
        save.get_player.assert_called_once_with(0)
        assert "settings_marker" not in result.output
    else:
        save.get_player.assert_not_called()


@pytest.mark.parametrize(
    "options,expected",
    [
        ([], {"settings": {"settings_marker": "NORMAL"}}),
        (["--settings"], {"settings": {"settings_marker": "NORMAL"}}),
        (["--player", "0"], {"player": {"selected_marker": "Human"}}),
        (["--list-players"], {"players": {"0": {"player_marker": "Human"}}}),
        (
            ["--settings", "--list-players", "--player", "0"],
            {"player": {"selected_marker": "Human"}},
        ),
    ],
)
@pytest.mark.parametrize("spoilers", [False, True])
def test_parse_json(runner, parsed_save, options, expected, spoilers):
    file, constructor, save = parsed_save
    if spoilers:
        options = [*options, "--spoilers"]
        expected = {
            **expected,
            "state": {"state_marker": 86},
            "plots": [{"plot_marker": 1}],
        }
    result = runner.invoke(cli, ["parse", "--json", *options, str(file)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == expected
    constructor.assert_called_once_with(file=file)
    if "--player" in options:
        save.get_player.assert_called_once_with(0)
    else:
        save.get_player.assert_not_called()


def test_parse_json_nested_models(runner, parsed_save):
    file, _, save = parsed_save
    save.get_player.return_value = {
        "cities": [City("München [bold]", 3, 4, 12, ["Stonehenge"])],
        "civics": Civics(),
        "trades": [TradeDeal(0, 1, 20, [Trade(e.TradeableItem.TRADE_GOLD, 50)], [])],
        "religion": e.ReligionType.NO_RELIGION,
    }
    result = runner.invoke(cli, ["parse", "--json", "--player", "0", str(file)])
    assert result.exit_code == 0, result.output
    player = json.loads(result.output)["player"]
    assert player["cities"] == [
        {
            "name": "München [bold]",
            "x": 3,
            "y": 4,
            "turn_founded": 12,
            "wonders": ["Stonehenge"],
            "idx": -1,
            "owner": -1,
            "population": 0,
            "turn_acquired": -1,
            "buildings": [],
            "religions": [],
            "corporations": [],
            "production_queue": [],
            "base_production_per_turn": 0,
            "gold_per_turn": 0.0,
            "science_per_turn": 0.0,
            "culture_per_turn": 0.0,
            "espionage_per_turn": 0.0,
        }
    ]
    assert player["civics"]["government"] == "CIVIC_DESPOTISM"
    assert player["trades"] == [
        {
            "first_player": 0,
            "second_player": 1,
            "initial_turn": 20,
            "first_trades": [{"item": "TRADE_GOLD", "amount": 50}],
            "second_trades": [],
        }
    ]
    assert player["religion"] == "NO_RELIGION"


def test_parse_json_city_production(runner, parsed_save):
    file, _, save = parsed_save
    save.get_player.return_value = {
        "cities": [
            City(
                "Capital",
                1,
                2,
                0,
                production_queue=[
                    ProductionOrder(
                        OrderType.ORDER_TRAIN, e.UnitType(0), True, 17, e.UnitAIType(2)
                    ),
                    ProductionOrder(
                        OrderType.ORDER_MAINTAIN,
                        e.ProcessType.PROCESS_WEALTH,
                        False,
                        None,
                    ),
                ],
                base_production_per_turn=7,
                gold_per_turn=12.5,
                science_per_turn=23.75,
                culture_per_turn=6.8,
                espionage_per_turn=1.99,
            )
        ]
    }
    result = runner.invoke(cli, ["parse", "--json", "--player", "0", str(file)])
    assert result.exit_code == 0, result.output
    city = json.loads(result.output)["player"]["cities"][0]
    assert city["production_queue"] == [
        {
            "order_type": "ORDER_TRAIN",
            "item": e.UnitType(0).name,
            "repeat": True,
            "invested_production": 17,
            "unit_ai": e.UnitAIType(2).name,
        },
        {
            "order_type": "ORDER_MAINTAIN",
            "item": "PROCESS_WEALTH",
            "repeat": False,
            "invested_production": None,
            "unit_ai": None,
        },
    ]
    assert city["base_production_per_turn"] == 7
    assert city["gold_per_turn"] == 12.5
    assert city["science_per_turn"] == 23.75
    assert city["culture_per_turn"] == 6.8
    assert city["espionage_per_turn"] == 1.99


@pytest.mark.parametrize(
    "filename,leader",
    [
        ("bismark-emperor-turn86.CivBeyondSwordSave", "LEADER_BISMARCK"),
        ("churchill-random-roll.CivBeyondSwordSave", "LEADER_CHURCHILL"),
    ],
)
def test_parse_json_real_save(runner, monkeypatch, filename, leader):
    file = Path(__file__).parent / "saves" / filename
    save = SaveFile(file)
    monkeypatch.setattr("civ4save.cli.SaveFile", Mock(return_value=save))

    result = runner.invoke(cli, ["parse", "--json", "--spoilers", str(file)])
    assert result.exit_code == 0, result.output
    output = json.loads(result.output)
    assert set(output) == {"settings", "state", "plots"}
    assert output["settings"]["game_speed"] == "GAMESPEED_NORMAL"
    assert isinstance(output["settings"]["wrap_x"], bool)
    assert isinstance(output["state"]["total_cities"], int)
    assert output["state"]["victory"] == "NO_VICTORY"
    width = output["settings"]["grid_width"]
    height = output["settings"]["grid_height"]
    assert len(output["plots"]) == width * height
    assert [(p["x"], p["y"]) for p in output["plots"]] == [
        (x, y) for y in range(height) for x in range(width)
    ]
    assert output["plots"][0]["terrain_type"].startswith("TERRAIN_")

    result = runner.invoke(cli, ["parse", "--json", "--list-players", str(file)])
    assert result.exit_code == 0, result.output
    players = json.loads(result.output)["players"]
    assert players["0"]["leader"] == leader
    assert players["0"]["civics"]["government"].startswith("CIVIC_")
    assert players["0"]["cities"]
    assert isinstance(players["0"]["gold"], int)
    assert isinstance(players["0"]["alive"], bool)
    assert players["0"]["current_era"].startswith("ERA_")
    assert players["0"]["cities"][0]["owner"] == 0
    assert players["0"]["cities"][0]["population"] > 0
    assert all(
        building.startswith("BUILDING_")
        for city in players["0"]["cities"]
        for building in city["buildings"]
    )
    assert players["0"]["units"]
    assert all(unit["unit_type"].startswith("UNIT_") for unit in players["0"]["units"])
    assert all(
        promotion.startswith("PROMOTION_")
        for unit in players["0"]["units"]
        for promotion in unit["promotions"]
    )

    result = runner.invoke(cli, ["parse", "--json", "--player", "0", str(file)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"player": players["0"]}


def test_gamefiles(runner, game_install, saves_dir):
    result = runner.invoke(cli, ["gamefiles"])
    assert result.exit_code == 0
    # Rich may wrap long paths across lines.
    sections = [
        ("Game Folder", game_install),
        ("Saves Folder", saves_dir),
        ("XML Folder", game_install / "Beyond the Sword/Assets/XML"),
    ]
    for index, (heading, path) in enumerate(sections):
        output = result.output.split(heading, 1)[1]
        if index + 1 < len(sections):
            output = output.split(sections[index + 1][0], 1)[0]
        assert "".join(str(path).split()) in "".join(output.split())


def test_gamefiles_without_installation(runner):
    result = runner.invoke(cli, ["gamefiles"])
    assert result.exit_code == 0
    assert "Game Folder" in result.output
    assert "Saves Folder" in result.output
    assert "XML Folder" in result.output
    assert "Sid Meier" not in result.output


def test_xml_no_options(runner):
    result = runner.invoke(cli, ["xml"])
    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.parametrize("option", ["--enums", "--text-map"])
def test_xml_without_installation(runner, option):
    result = runner.invoke(cli, ["xml", option])
    assert result.exit_code == 1
    assert isinstance(result.exception, FileNotFoundError)


def test_xml_enums(runner, game_install):
    result = runner.invoke(cli, ["xml", "--enums"])
    assert result.exit_code == 0, result.output
    # Execute only code generated from our synthetic, controlled XML fixture.
    namespace = {}
    exec(result.output, namespace)  # noqa: S102
    unit = namespace["UnitType"]
    assert [(member.name, member.value) for member in unit] == [
        ("NO_UNIT", -1),
        ("UNIT_BTS_FIRST", 0),
        ("UNIT_BTS_SECOND", 1),
    ]


@pytest.mark.parametrize(
    "options,shared,unique",
    [
        ([], "BTS name", "Vanilla only"),
        (["--lang", "French"], "Français", "Original seul"),
    ],
)
def test_xml_text_map(runner, game_install, options, shared, unique):
    result = runner.invoke(cli, ["xml", "--text-map", *options])
    assert result.exit_code == 0, result.output
    mapping = json.loads(result.output)
    assert mapping["TXT_KEY_SHARED"] == shared
    assert mapping["TXT_KEY_VANILLA_ONLY"] == unique
    assert set(mapping) == {
        "TXT_KEY_SHARED",
        "TXT_KEY_VANILLA_ONLY",
        "TXT_KEY_WARLORDS_ONLY",
        "TXT_KEY_BTS_ONLY",
    }


def test_xml_invalid_language(runner):
    result = runner.invoke(cli, ["xml", "--text-map", "--lang", "Klingon"])
    assert result.exit_code == 2
    assert "Invalid value" in result.output


def test_civs():
    runner = CliRunner()

    result = runner.invoke(cli, ["civs"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["civs", "-l"])
    assert result.exit_code == 0
    assert "Germany\n" in result.output

    result = runner.invoke(cli, ["civs", "Germany"])
    assert result.exit_code == 0
    assert "description='German Empire',\n" in result.output


def test_leaders():
    runner = CliRunner()

    result = runner.invoke(cli, ["leaders"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["leaders", "-l"])
    assert result.exit_code == 0
    assert "Genghis Khan\n" in result.output

    result = runner.invoke(cli, ["leaders", "Genghis Khan"])
    assert result.exit_code == 0
    assert "description='Genghis Khan',\n" in result.output

    result = runner.invoke(cli, ["leaders", "-a"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["leaders", "--sort-by", "base_peace_weight"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["leaders", "--sort-by", "base_peace_weight", "-r"])
    assert result.exit_code == 0
