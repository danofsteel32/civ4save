import json
from unittest.mock import MagicMock, Mock

import pytest
from click.testing import CliRunner

from civ4save import SaveFile, __version__
from civ4save.cli import cli


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


def test_parse_json_is_unimplemented(runner, parsed_save):
    file, _, _ = parsed_save
    result = runner.invoke(cli, ["parse", "--json", str(file)])
    assert result.exit_code == 1
    assert isinstance(result.exception, NotImplementedError)
    assert str(result.exception) == "Sorry no json yet"


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
