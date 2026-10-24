from enum import Enum

import pytest

from civ4save import utils


class MyEnum(Enum):
    NEG_VALUE = -1
    SIMPLE_CASE = 1
    MORE_COMPLEX_CASE = 2


def test_get_enum_length():
    assert utils.get_enum_length(MyEnum) == 2


def test_unenumify():
    simple = utils.unenumify(MyEnum.SIMPLE_CASE)
    complex = utils.unenumify(MyEnum.MORE_COMPLEX_CASE)
    assert simple == "Case"
    assert complex == "Complex Case"


def test_next_plot():
    assert (1, 0) == utils.next_plot(0, 0, 84, 52)
    assert (0, 1) == utils.next_plot(83, 0, 84, 52)


@pytest.mark.parametrize(
    "location", [".local/share", ".var/app/com.valvesoftware.Steam/data"]
)
def test_get_game_dir(isolated_home, location):
    game = (
        isolated_home
        / location
        / "Steam/steamapps/common"
        / ("Sid Meier's Civilization IV Beyond the Sword")
    )
    game.mkdir(parents=True)
    assert utils.get_game_dir() == game


def test_game_discovery_prefers_flatpak(game_install, isolated_home):
    flatpak = (
        isolated_home
        / ".var/app/com.valvesoftware.Steam/data/Steam/steamapps/common"
        / game_install.name
    )
    flatpak.mkdir(parents=True)
    assert utils.get_game_dir() == flatpak


def test_missing_game_directory():
    with pytest.raises(FileNotFoundError, match="game directory"):
        utils.get_game_dir()


def test_get_xml_dir(game_install):
    assert utils.get_xml_dir() == game_install / "Beyond the Sword/Assets/XML"


def test_missing_xml_directory(game_install):
    xml_dir = game_install / "Beyond the Sword/Assets/XML"
    # Keep the game directory while making its XML directory unavailable.
    xml_dir.rename(xml_dir.with_name("XML-unavailable"))
    with pytest.raises(FileNotFoundError, match="XML directory"):
        utils.get_xml_dir()


@pytest.mark.parametrize("system", ["Linux", "Windows"])
@pytest.mark.parametrize("sub_dir", ["single", "multi"])
def test_get_saves_dir(isolated_home, monkeypatch, system, sub_dir):
    monkeypatch.setattr(utils.platform, "system", lambda: system)
    if system == "Windows":
        path = isolated_home / "Documents/My Games/beyond the sword/Saves" / sub_dir
    else:
        path = (
            isolated_home
            / (
                ".local/share/Steam/steamapps/compatdata/8800/pfx/drive_c/users/steamuser/"
                "My Documents/My Games/Beyond the Sword/Saves"
            )
            / sub_dir
        )
    path.mkdir(parents=True)
    assert utils.get_saves_dir(sub_dir) == path


@pytest.mark.parametrize("system", ["Linux", "Windows"])
def test_missing_saves_directory(monkeypatch, system):
    monkeypatch.setattr(utils.platform, "system", lambda: system)
    with pytest.raises(FileNotFoundError, match="saves directory"):
        utils.get_saves_dir()


def test_text_file_discovery_orders_expansions(game_install):
    assert list(utils.get_xml_text_files()) == [
        game_install / expansion / "Assets/XML/Text/CIV4GameText.xml"
        for expansion in ["", "Warlords", "Beyond the Sword"]
    ]


@pytest.mark.parametrize(
    "lang,shared,vanilla,warlords,bts",
    [
        ("English", "BTS name", "Vanilla only", "Warlords only", "BTS only"),
        ("French", "Français", "Original seul", "Extension seul", "Français seul"),
    ],
)
def test_text_map_expansion_overrides(
    game_install, lang, shared, vanilla, warlords, bts
):
    assert utils.make_text_map(lang) == {
        "TXT_KEY_SHARED": shared,
        "TXT_KEY_VANILLA_ONLY": vanilla,
        "TXT_KEY_WARLORDS_ONLY": warlords,
        "TXT_KEY_BTS_ONLY": bts,
    }


def test_text_discovery_with_missing_expansion(game_install):
    bts_text = game_install / "Beyond the Sword/Assets/XML/Text"
    bts_text.rename(bts_text.with_name("Text-unavailable"))
    assert utils.make_text_map()["TXT_KEY_SHARED"] == "Warlords name"


def test_text_map_ignores_other_xml_roots(game_install):
    unrelated = game_install / "Assets/XML/Text/unrelated.xml"
    unrelated.write_text("<OtherRoot/>", encoding="utf-8")
    assert utils.make_text_map()["TXT_KEY_SHARED"] == "BTS name"
