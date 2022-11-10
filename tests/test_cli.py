import json

from click.testing import CliRunner

from civ4save import __version__
from civ4save.cli import cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"cli, version {__version__}\n"


def test_parse():
    file = "tests/saves/bismark-emperor-turn86.CivBeyondSwordSave"

    runner = CliRunner()

    result = runner.invoke(cli, ["parse"])
    assert result.exit_code == 2  # ERROR no file given

    result = runner.invoke(cli, ["parse", "--settings", file])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["parse", "--spoilers", file])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["parse", "--player", 0, file])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["parse", "--list-players", file])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["parse", "--json", file])
    assert result.exit_code == 0


def test_gamefiles():
    runner = CliRunner()
    result = runner.invoke(cli, ["gamefiles"])
    assert result.exit_code == 0


def test_xml():
    runner = CliRunner()

    result = runner.invoke(cli, ["xml"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["xml", "--enums"])
    assert result.exit_code == 0
    assert "class UnitType(IntEnum):\n" in result.output

    result = runner.invoke(cli, ["xml", "--text-map"])
    assert result.exit_code == 0
    assert "TXT_KEY" in result.output

    result = runner.invoke(cli, ["xml", "--text-map", "--lang", "French"])
    assert result.exit_code == 0
    assert "TXT_KEY" in result.output


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