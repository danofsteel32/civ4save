"""
xml_files.py
This module is responsible for reading the CivIV XML files.

Reads all of the things in and makes it whole again. 
an enum for each Type. The enums are then written out to cv_enums.py
using a jinja template.
"""

from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
# from functools import cache
from pathlib import Path
from typing import Optional

import xmltodict
from jinja2 import Template

from civ4save.enums.base import BASE_ENUMS
from civ4save.utils import get_game_dir


@dataclass
class XMLFile:
    name: str
    path: Path
    defaults: list[tuple[str, int]] = dc_field(default_factory=list)

    def read(self):
        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} does not exist!")
        with open(self.path, "r") as xml_file:
            parsed = xmltodict.parse(xml_file.read())
        return parsed

    def to_enum(self):
        contents = self.read()
        root_key = list(contents.keys())[0]
        root = contents[root_key]
        key = list(root.keys())[-1]
        names = []
        for n, entry in enumerate(root[key][key[:-1]]):
            names.append((entry["Type"], n))
        all_names = self.defaults + names
        return Enum(self.name, all_names)

    def create_mapping(self) -> dict:
        contents = self.read()
        root_key = list(contents.keys())[0]
        root = contents[root_key]
        key = list(root.keys())[-1]
        maps = {}
        if len(self.defaults) > 0:
            for d in self.defaults:
                k, v = d
                maps[k] = v

        for n, entry in enumerate(root[key][key[:-1]]):
            maps[entry["Type"]] = n
        return maps


# @cache
def get_xml_files(
    game_dir: Optional[Path] = None, ai_survivor: bool = False
) -> list[XMLFile]:

    game_dir = get_game_dir() if not game_dir else game_dir
    vanilla_xml = game_dir / "Assets" / "XML"
    warlords_xml = game_dir / "Warlords" / "Assets" / "XML"
    bts_xml = game_dir / "Beyond the Sword" / "Assets" / "XML"

    building_files = get_building_files(bts_xml)
    if ai_survivor:
        building_files[0] = get_ai_survivor()

    civ_files = get_civilization_files(bts_xml)
    event_files = get_event_files(bts_xml)
    gameinfo_files = get_gameinfo_files(vanilla_xml, bts_xml)
    unit_files = get_unit_files(bts_xml)
    terrain_files = get_terrain_files(vanilla_xml, bts_xml)

    return (
        building_files
        + civ_files
        + event_files
        + gameinfo_files
        + unit_files
        + terrain_files
    )


def get_ai_survivor() -> XMLFile:
    return XMLFile(
        name="BuildingType",
        path=Path("custom_xml") / "AiSurvivorBuildingInfos.xml",
        defaults=[("NO_BUILDING", -1)],
    )


def get_building_files(bts_xml: Path) -> list[XMLFile]:
    files = [
        XMLFile(
            name="BuildingType",
            path=bts_xml / "Buildings/CIV4BuildingInfos.xml",
            defaults=[("NO_BUILDING", -1)],
        ),
        XMLFile(
            name="BuildingClassType",
            path=bts_xml / "Buildings/CIV4BuildingClassInfos.xml",
            defaults=[("NO_BUILDINGCLASS", -1)],
        ),
        XMLFile(
            name="SpecialBuildingType",
            path=bts_xml / "Buildings/CIV4SpecialBuildingInfos.xml",
            defaults=[("NO_SPECIALBUILDING", -1)],
        ),
    ]
    return files


def get_civilization_files(bts_xml: Path) -> list[XMLFile]:
    files = [
        XMLFile(
            name="CivilizationType",
            path=bts_xml / "Civilizations/CIV4CivilizationInfos.xml",
            defaults=[("NO_CIVILIZATION", -1)],
        ),
        XMLFile(
            name="LeaderHeadType",
            path=bts_xml / "Civilizations/CIV4LeaderHeadInfos.xml",
            defaults=[("NO_LEADER", -1)],
        ),
    ]
    return files


def get_event_files(bts_xml: Path) -> list[XMLFile]:
    files = [
        XMLFile(
            name="EventType",
            path=bts_xml / "Events/CIV4EventInfos.xml",
            defaults=[("NO_EVENT", -1)],
        ),
        XMLFile(
            name="EventTriggerType",
            path=bts_xml / "Events/CIV4EventTriggerInfos.xml",
            defaults=[("NO_EVENTTRIGGER", -1)],
        ),
    ]
    return files


def get_gameinfo_files(vanilla_xml: Path, bts_xml: Path) -> list[XMLFile]:
    files = [
        XMLFile(
            name="ClimateType",
            path=vanilla_xml / "GameInfo/CIV4ClimateInfo.xml",
            defaults=[("NO_CLIMATE", -1)],
        ),
        XMLFile(
            name="CivicType",
            path=bts_xml / "GameInfo/CIV4CivicInfos.xml",
            defaults=[("NO_CIVIC", -1)],
        ),
        XMLFile(
            name="CommerceType",
            path=bts_xml / "GameInfo/CIV4CommerceInfo.xml",
            defaults=[("NO_COMMERCE", -1)],
        ),
        XMLFile(
            name="CorporationType",
            path=bts_xml / "GameInfo/CIV4CorporationInfo.xml",
            defaults=[("NO_CORPORATION", -1)],
        ),
        XMLFile(
            name="CultureLevelType",
            path=vanilla_xml / "GameInfo/CIV4CultureLevelInfo.xml",
            defaults=[("NO_CULTURELEVEL", -1)],
        ),
        XMLFile(
            name="DiploCommentType",
            path=bts_xml / "GameInfo/CIV4DiplomacyInfos.xml",
            defaults=[("NO_DIPLOCOMMENT", -1)],
        ),
        XMLFile(
            name="EraType",
            path=bts_xml / "GameInfo/CIV4EraInfos.xml",
            defaults=[("NO_ERA", -1)],
        ),
        XMLFile(
            name="EspionageMissionType",
            path=bts_xml / "GameInfo/CIV4EspionageMissionInfo.xml",
            defaults=[("NO_ESPIONAGEMISSION", -1)],
        ),
        XMLFile(
            name="GameOptionType",
            path=bts_xml / "GameInfo/CIV4GameOptionInfos.xml",
            defaults=[("NO_GAMEOPTION", -1)],
        ),
        XMLFile(
            name="GameSpeedType",
            path=bts_xml / "GameInfo/CIV4GameSpeedInfo.xml",
            defaults=[("NO_GAMESPEED", -1)],
        ),
        XMLFile(
            name="HandicapType",
            path=bts_xml / "GameInfo/CIV4HandicapInfo.xml",
            defaults=[("NO_HANDICAP", -1)],
        ),
        XMLFile(
            name="MultiplayerOptionType",
            path=bts_xml / "GameInfo/CIV4MPOptionInfos.xml",
            defaults=[("NO_MPOPTION", -1)],
        ),
        XMLFile(
            name="ProjectType",
            path=bts_xml / "GameInfo/CIV4ProjectInfo.xml",
            defaults=[("NO_PROJECT", -1)],
        ),
        XMLFile(
            name="ReligionType",
            path=bts_xml / "GameInfo/CIV4ReligionInfo.xml",
            defaults=[("NO_RELIGION", -1)],
        ),
        XMLFile(
            name="SeaLevelType",
            path=vanilla_xml / "GameInfo/CIV4SeaLevelInfo.xml",
            defaults=[("NO_SEALEVEL", -1)],
        ),
        XMLFile(
            name="SpecialistType",
            path=bts_xml / "GameInfo/CIV4SpecialistInfos.xml",
            defaults=[("NO_SPECIALIST", -1)],
        ),
        XMLFile(
            name="VictoryType",
            path=bts_xml / "GameInfo/CIV4VictoryInfo.xml",
            defaults=[("NO_VICTORY", -1)],
        ),
        XMLFile(
            name="VoteType",
            path=bts_xml / "GameInfo/CIV4VoteInfo.xml",
            defaults=[("NO_VOTE", -1)],
        ),
        XMLFile(
            name="VoteSourceType",
            path=bts_xml / "GameInfo/CIV4VoteSourceInfos.xml",
            defaults=[("NO_VOTESOURCE", -1)],
        ),
        XMLFile(
            name="WorldSizeType",
            path=bts_xml / "GameInfo/CIV4WorldInfo.xml",
            defaults=[("NO_WORLDSIZE", -1)],
        ),
    ]
    return files


def get_unit_files(bts_xml: Path) -> list[XMLFile]:
    files = [
        XMLFile(
            name="BuildType",
            path=bts_xml / "Units/CIV4BuildInfos.xml",
            defaults=[("NO_BUILD", -1)],
        ),
        XMLFile(
            name="MissionType",
            path=bts_xml / "Units/CIV4MissionInfos.xml",
            defaults=[("NO_MISSION", -1)],
        ),
        XMLFile(
            name="PromotionType",
            path=bts_xml / "Units/CIV4PromotionInfos.xml",
            defaults=[("NO_PROMOTION", -1)],
        ),
        XMLFile(
            name="SpecialUnitType",
            path=bts_xml / "Units/CIV4SpecialUnitInfos.xml",
            defaults=[("NO_SPECIALUNIT", -1)],
        ),
        XMLFile(
            name="UnitType",
            path=bts_xml / "Units/CIV4UnitInfos.xml",
            defaults=[("NO_UNIT", -1)],
        ),
        XMLFile(
            name="UnitClassType",
            path=bts_xml / "Units/CIV4UnitClassInfos.xml",
            defaults=[("NO_UNITCLASS", -1)],
        ),
    ]
    return files


def get_terrain_files(vanilla_xml: Path, bts_xml: Path) -> list[XMLFile]:
    files = [
        XMLFile(
            name="BonusType",
            path=vanilla_xml / "Terrain/CIV4BonusInfos.xml",
            defaults=[("NO_BONUS", -1)],
        ),
        XMLFile(
            name="FeatureType",
            path=bts_xml / "Terrain/CIV4FeatureInfos.xml",
            defaults=[("NO_FEATURE", -1)],
        ),
        XMLFile(
            name="ImprovementType",
            path=bts_xml / "Terrain/CIV4ImprovementInfos.xml",
            defaults=[("NO_IMPROVEMENT", -1)],
        ),
        XMLFile(
            name="TerrainType",
            path=bts_xml / "Terrain/CIV4TerrainInfos.xml",
            defaults=[("NO_TERRAIN", -1)],
        ),
    ]
    return files


def write_out_enum(e) -> None:
    # header = "from enum import Enum\n"
    data = {
        "enum_name": e.__name__,
        "members": [{"name": m, "value": e[m].value} for m in e.__members__],
    }
    template = """
class {{ enum_name }}(Enum):
    {%- for m in members %}
    {{ m.name }} = {{ m.value }}
    {%- endfor -%}
{{ '\n' }}
"""

    j2_template = Template(template)
    print(j2_template.render(data))


def write_all_enums(xml_files: list[XMLFile]):
    print("from enum import Enum")
    print()
    for en in BASE_ENUMS:
        write_out_enum(en)
    for file in xml_files:
        e = file.to_enum()
        write_out_enum(e)


def make_enums(ai_survivor: bool = False):
    game_dir = get_game_dir()
    xml_files = get_xml_files(game_dir, ai_survivor)
    write_all_enums(xml_files)


if __name__ == "__main__":
    make_enums()
