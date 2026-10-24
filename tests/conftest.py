"""Synthetic installation fixtures; tests never discover the real game folders."""

from pathlib import Path
from textwrap import dedent

import pytest

from civ4save import utils


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(utils.platform, "system", lambda: "Linux")
    # The Windows installation candidate is a relative path on Unix.
    monkeypatch.chdir(tmp_path)
    return home


@pytest.fixture
def game_install(isolated_home):
    """Handwritten XML mirrors installed BTS shapes, without copying game data.

    Real files have namespaces, repeated Info/TEXT nodes, expansion overrides,
    and both plain and nested language values. Each tier has a unique text key
    as well as a shared key, making precedence and preservation observable.
    """
    game = (
        isolated_home
        / ".local/share/Steam/steamapps/common"
        / ("Sid Meier's Civilization IV Beyond the Sword")
    )
    for expansion, label, french in [
        ("", "Vanilla", "Original"),
        ("Warlords", "Warlords", "Extension"),
        ("Beyond the Sword", "BTS", "Français"),
    ]:
        xml = game / expansion / "Assets/XML"
        units = xml / "Units"
        units.mkdir(parents=True)
        (units / "CIV4UnitInfos.xml").write_text(
            dedent(f"""\
            <Civ4UnitInfos xmlns="x-schema:CIV4UnitSchema.xml">
              <UnitInfos>
                <UnitInfo><Type>UNIT_{label.upper()}_FIRST</Type></UnitInfo>
                <UnitInfo><Type>UNIT_{label.upper()}_SECOND</Type></UnitInfo>
              </UnitInfos>
            </Civ4UnitInfos>
            """),
            encoding="utf-8",
        )
        # Schema and text files must never become enum inputs.
        (units / "CIV4UnitSchema.xml").write_text("<Schema/>", encoding="utf-8")
        (units / "CIV4UnitText.xml").write_text("<Text/>", encoding="utf-8")
        text_dir = xml / "Text"
        text_dir.mkdir()
        (text_dir / "CIV4GameText.xml").write_text(
            dedent(f"""\
            <?xml version="1.0" encoding="ISO-8859-1"?>
            <Civ4GameText xmlns="http://www.firaxis.com">
              <TEXT>
                <Tag>TXT_KEY_SHARED</Tag>
                <English>{label} name</English>
                <French><Text>{french}</Text><Gender>Male</Gender><Plural>0</Plural></French>
              </TEXT>
              <TEXT>
                <Tag>TXT_KEY_{label.upper()}_ONLY</Tag>
                <English>{label} only</English>
                <French>{french} seul</French>
              </TEXT>
            </Civ4GameText>
            """),
            encoding="ISO-8859-1",
        )
    return game


@pytest.fixture
def saves_dir(isolated_home):
    saves = isolated_home / (
        ".local/share/Steam/steamapps/compatdata/8800/pfx/drive_c/users/steamuser/"
        "My Documents/My Games/Beyond the Sword/Saves/single"
    )
    saves.mkdir(parents=True)
    return saves
