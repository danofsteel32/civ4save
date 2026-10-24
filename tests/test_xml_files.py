from enum import Enum

import pytest

from civ4save import xml_files


def test_unit_enum_from_xml(game_install):
    path = game_install / "Beyond the Sword/Assets/XML/Units/CIV4UnitInfos.xml"
    file = xml_files.Civ4XmlFile(path)
    assert file.name == "CIV4UnitInfos.xml"
    assert file.root_key == "Civ4UnitInfos"
    assert file.parent_category == "Units"
    assert file.enum_name == "UnitType"
    assert file.negative_one == "NO_UNIT"
    assert file.types() == [
        ("NO_UNIT", -1),
        ("UNIT_BTS_FIRST", 0),
        ("UNIT_BTS_SECOND", 1),
    ]
    enum = file.to_enum()
    assert issubclass(enum, Enum)
    assert enum.UNIT_BTS_FIRST.value == 0
    assert enum.NO_UNIT.value == -1


def test_enum_discovery_prefers_bts(game_install):
    files = list(xml_files.xml_files_iter())
    assert [file.path for file in files] == [
        game_install / "Beyond the Sword/Assets/XML/Units/CIV4UnitInfos.xml"
    ]


@pytest.mark.parametrize("expansion", ["Warlords", ""])
def test_enum_discovery_falls_back_to_earlier_expansion(game_install, expansion):
    (game_install / "Beyond the Sword/Assets/XML/Units/CIV4UnitInfos.xml").unlink()
    if not expansion:
        (game_install / "Warlords/Assets/XML/Units/CIV4UnitInfos.xml").unlink()
    files = list(xml_files.xml_files_iter())
    assert [file.path for file in files] == [
        game_install / expansion / "Assets/XML/Units/CIV4UnitInfos.xml"
    ]


def test_enum_discovery_preserves_unique_files_and_root_xml(game_install):
    vanilla = game_install / "Assets/XML"
    # Contents are irrelevant to discovery; no enum generation happens here.
    (vanilla / "CIV4EraInfos.xml").write_text("<Civ4EraInfos/>", encoding="utf-8")
    (vanilla / "Units/CIV4PromotionInfos.xml").write_text(
        "<Civ4PromotionInfos/>", encoding="utf-8"
    )
    (vanilla / "CIV4RootSchema.xml").write_text("<Schema/>", encoding="utf-8")
    files = {file.name: file for file in xml_files.xml_files_iter()}
    assert set(files) == {
        "CIV4UnitInfos.xml",
        "CIV4EraInfos.xml",
        "CIV4PromotionInfos.xml",
    }
    assert files["CIV4EraInfos.xml"].parent_category is None
    assert files["CIV4PromotionInfos.xml"].path.parent == vanilla / "Units"


def test_non_xml_file_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="not a xml file"):
        xml_files.Civ4XmlFile(tmp_path / "example.txt")


def test_missing_xml_file(tmp_path):
    file = xml_files.Civ4XmlFile(tmp_path / "CIV4UnitInfos.xml")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        file.types()


def test_xml_discovery_without_installation():
    with pytest.raises(FileNotFoundError, match="game directory"):
        list(xml_files.xml_files_iter())
