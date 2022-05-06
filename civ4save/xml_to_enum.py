"""
xml_to_enum.py
This module is responsible for reading the CivIV XML files and building
an enum for each Type. The enums are then written out to cv_enums.py
using a jinja template.
"""

from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
from jinja2 import Template
from pathlib import Path
import xmltodict


# TODO: Detect Windows/Linux/Mac and set GAME_DIR accordingly

# Linux Steam flatpak location
GAME_DIR = Path.home() / ".var/app/com.valvesoftware.Steam/data/Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword"

VANILLA_XML = GAME_DIR / 'Assets' / 'XML'
WARLORDS_XML = GAME_DIR / 'Warlords' / 'Assets' / 'XML'
BTS_XML = GAME_DIR / 'Beyond the Sword' / 'Assets' / 'XML'


@dataclass
class XMLFile:
    name: str
    path: Path
    defaults: list[tuple[str, int]] = dc_field(default_factory=list)

    def read(self):
        if not self.path.exists():
            raise FileNotFoundError(f'{self.path} does not exist!')
        with open(self.path, 'r') as xml_file:
            parsed = xmltodict.parse(xml_file.read())
        return parsed

    def to_enum(self):
        contents = self.read()
        root_key = list(contents.keys())[0]
        root = contents[root_key]
        key = list(root.keys())[-1]
        names = []
        for n, entry in enumerate(root[key][key[:-1]]):
            names.append((entry['Type'], n))
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
            maps[entry['Type']] = n
        return maps


base_enums = [
    Enum(
        'GameType',
        [
            ('GAME_NONE', -1),
            ('GAME_SP_NEW', 0),
            ('GAME_SP_SCENARIO', 1),
            ('GAME_SP_LOAD', 2),
            ('GAME_MP_NEW', 3),
            ('GAME_MP_SCENARIO', 4),
            ('GAME_MP_LOAD', 5),
            ('GAME_HOTSEAT_NEW', 6),
            ('GAME_HOTSEAT_SCENARIO', 7),
            ('GAME_HOTSEAT_LOAD', 8),
            ('GAME_PBEM_NEW', 9),
            ('GAME_PBEM_SCENARIO', 10),
            ('GAME_PBEM_LOAD', 11),
            ('GAME_REPLAY', 12),
        ]
    ),
    Enum(
        'GameStateType',
        [
            ('GAMESTATE_ON', 0),
            ('GAMESTATE_OVER', 1),
            ('GAMESTATE_EXTENDED', 2)
        ]
    ),
    Enum(
        'YieldType',
        [
            ('NO_YIELD', -1),
            ('YIELD_FOOD', 0),
            ('YIELD_PRODUCTION', 1),
            ('YIELD_COMMERCE', 2),
        ]
    ),
    Enum(
        'TraitType',
        [
            ('NO_TRAIT', -1),
            ('TRAIT_PHILOSOPHICAL', 0),
            ('TRAIT_AGGRESSIVE', 1),
            ('TRAIT_SPIRITUAL', 2),
            ('TRAIT_EXPANSIVE', 3),
            ('TRAIT_INDUSTRIOUS', 4),
            ('TRAIT_CREATIVE', 5),
            ('TRAIT_FINANCIAL', 6),
            ('TRAIT_ORGANIZED', 7),
            ('TRAIT_CHARISMATIC', 8),
            ('TRAIT_PROTECTIVE', 9),
            ('TRAIT_IMPERIALISTIC', 10),
        ]
    ),
    Enum(
        'TradeableItem',
        [
            ('TRADE_ITEM_NONE', -1),
            ('TRADE_GOLD', 0),
            ('TRADE_GOLD_PER_TURN', 1),
            ('TRADE_MAPS', 2),
            ('TRADE_VASSAL', 3),
            ('TRADE_SURRENDER', 4),
            ('TRADE_OPEN_BORDERS', 5),
            ('TRADE_DEFENSIVE_PACT', 6),
            ('TRADE_PERMANENT_ALLIANCE', 7),
            ('TRADE_PEACE_TREATY', 8),
            ('TRADE_TECHNOLOGIES', 9),
            ('TRADE_RESOURCES', 10),
            ('TRADE_CITIES', 11),
            ('TRADE_PEACE', 12),
            ('TRADE_WAR', 13),
            ('TRADE_EMBARGO', 14),
            ('TRADE_CIVIC', 15),
            ('TRADE_RELIGION', 16),
        ]
    ),
    Enum(
        'ReplayMessageType',
        [
            ('MAJOR_EVENT', 0),
            ('CITY_FOUNDED', 1),
            ('PLOT_OWNER_CHANGE', 2),
        ]
    ),
    Enum(
        'PlotType',
        [
            ('NO_PLOT', -1),
            ('PLOT_PEAK', 0),
            ('PLOT_HILLS', 1),
            ('PLOT_LAND', 2),
            ('PLOT_OCEAN', 3),
        ]
    )
]


building_files = [
    XMLFile(
        name='BuildingType',
        path=BTS_XML / 'Buildings/CIV4BuildingInfos.xml',
        defaults=[('NO_BUILDING', -1)]
    ),
    XMLFile(
        name='BuildingClassType',
        path=BTS_XML / 'Buildings/CIV4BuildingClassInfos.xml',
        defaults=[('NO_BUILDINGCLASS', -1)]
    ),
    XMLFile(
        name='SpecialBuildingType',
        path=BTS_XML / 'Buildings/CIV4SpecialBuildingInfos.xml',
        defaults=[('NO_SPECIALBUILDING', -1)]
    ),
]

civilization_files = [
    XMLFile(
        name='CivilizationType',
        path=BTS_XML / 'Civilizations/CIV4CivilizationInfos.xml',
        defaults=[('NO_CIVILIZATION', -1)]
    ),
    XMLFile(
        name='LeaderHeadType',
        path=BTS_XML / 'Civilizations/CIV4LeaderHeadInfos.xml',
        defaults=[('NO_LEADER', -1)]
    ),
]

event_files = [
    XMLFile(
        name='EventType',
        path=BTS_XML / 'Events/CIV4EventInfos.xml',
        defaults=[('NO_EVENT', -1)]
    ),
    XMLFile(
        name='EventTriggerType',
        path=BTS_XML / 'Events/CIV4EventTriggerInfos.xml',
        defaults=[('NO_EVENTTRIGGER', -1)]
    ),
]

gameinfo_files = [
    XMLFile(
        name='ClimateType',
        path=VANILLA_XML / 'GameInfo/CIV4ClimateInfo.xml',
        defaults=[('NO_CLIMATE', -1)]
    ),
    XMLFile(
        name='CivicType',
        path=BTS_XML / 'GameInfo/CIV4CivicInfos.xml',
        defaults=[('NO_CIVIC', -1)]
    ),
    XMLFile(
        name='CommerceType',
        path=BTS_XML / 'GameInfo/CIV4CommerceInfo.xml',
        defaults=[('NO_COMMERCE', -1)]
    ),
    XMLFile(
        name='CorporationType',
        path=BTS_XML / 'GameInfo/CIV4CorporationInfo.xml',
        defaults=[('NO_CORPORATION', -1)]
    ),
    XMLFile(
        name='CultureLevelType',
        path=VANILLA_XML / 'GameInfo/CIV4CultureLevelInfo.xml',
        defaults=[('NO_CULTURELEVEL', -1)]
    ),
    XMLFile(
        name='DiploCommentType',
        path=BTS_XML / 'GameInfo/CIV4DiplomacyInfos.xml',
        defaults=[('NO_DIPLOCOMMENT', -1)]
    ),
    XMLFile(
        name='EraType',
        path=BTS_XML / 'GameInfo/CIV4EraInfos.xml',
        defaults=[('NO_ERA', -1)]
    ),
    XMLFile(
        name='EspionageMissionType',
        path=BTS_XML / 'GameInfo/CIV4EspionageMissionInfo.xml',
        defaults=[('NO_ESPIONAGEMISSION', -1)]
    ),
    XMLFile(
        name='GameOptionType',
        path=BTS_XML / 'GameInfo/CIV4GameOptionInfos.xml',
        defaults=[('NO_GAMEOPTION', -1)]
    ),
    XMLFile(
        name='GameSpeedType',
        path=BTS_XML / 'GameInfo/CIV4GameSpeedInfo.xml',
        defaults=[('NO_GAMESPEED', -1)]
    ),
    XMLFile(
        name='HandicapType',
        path=BTS_XML / 'GameInfo/CIV4HandicapInfo.xml',
        defaults=[('NO_HANDICAP', -1)]
    ),
    XMLFile(
        name='MultiplayerOptionType',
        path=BTS_XML / 'GameInfo/CIV4MPOptionInfos.xml',
        defaults=[('NO_MPOPTION', -1)]
    ),
    XMLFile(
        name='ProjectType',
        path=BTS_XML / 'GameInfo/CIV4ProjectInfo.xml',
        defaults=[('NO_PROJECT', -1)]
    ),
    XMLFile(
        name='ReligionType',
        path=BTS_XML / 'GameInfo/CIV4ReligionInfo.xml',
        defaults=[('NO_RELIGION', -1)]
    ),
    XMLFile(
        name='SeaLevelType',
        path=VANILLA_XML / 'GameInfo/CIV4SeaLevelInfo.xml',
        defaults=[('NO_SEALEVEL', -1)]
    ),
    XMLFile(
        name='SpecialistType',
        path=BTS_XML / 'GameInfo/CIV4SpecialistInfos.xml',
        defaults=[('NO_SPECIALIST', -1)]
    ),
    XMLFile(
        name='VictoryType',
        path=BTS_XML / 'GameInfo/CIV4VictoryInfo.xml',
        defaults=[('NO_VICTORY', -1)]
    ),
    XMLFile(
        name='VoteType',
        path=BTS_XML / 'GameInfo/CIV4VoteInfo.xml',
        defaults=[('NO_VOTE', -1)]
    ),
    XMLFile(
        name='VoteSourceType',
        path=BTS_XML / 'GameInfo/CIV4VoteSourceInfos.xml',
        defaults=[('NO_VOTESOURCE', -1)]
    ),
    XMLFile(
        name='WorldSizeType',
        path=BTS_XML / 'GameInfo/CIV4WorldInfo.xml',
        defaults=[('NO_WORLDSIZE', -1)]
    ),
]

unit_files = [
    XMLFile(
        name='BuildType',
        path=BTS_XML / 'Units/CIV4BuildInfos.xml',
        defaults=[('NO_BUILD', -1)]
    ),
    XMLFile(
        name='MissionType',
        path=BTS_XML / 'Units/CIV4MissionInfos.xml',
        defaults=[('NO_MISSION', -1)]
    ),
    XMLFile(
        name='PromotionType',
        path=BTS_XML / 'Units/CIV4PromotionInfos.xml',
        defaults=[('NO_PROMOTION', -1)]
    ),
    XMLFile(
        name='SpecialUnitType',
        path=BTS_XML / 'Units/CIV4SpecialUnitInfos.xml',
        defaults=[('NO_SPECIALUNIT', -1)]
    ),
    XMLFile(
        name='UnitType',
        path=BTS_XML / 'Units/CIV4UnitInfos.xml',
        defaults=[('NO_UNIT', -1)]
    ),
    XMLFile(
        name='UnitClassType',
        path=BTS_XML / 'Units/CIV4UnitClassInfos.xml',
        defaults=[('NO_UNITCLASS', -1)]
    ),
]

terrain_files = [
    XMLFile(
        name='BonusType',
        path=VANILLA_XML / 'Terrain/CIV4BonusInfos.xml',
        defaults=[('NO_BONUS', -1)]
    ),
    XMLFile(
        name='FeatureType',
        path=BTS_XML / 'Terrain/CIV4FeatureInfos.xml',
        defaults=[('NO_FEATURE', -1)]
    ),
    XMLFile(
        name='ImprovementType',
        path=BTS_XML / 'Terrain/CIV4ImprovementInfos.xml',
        defaults=[('NO_IMPROVEMENT', -1)]
    ),
    XMLFile(
        name='TerrainType',
        path=BTS_XML / 'Terrain/CIV4TerrainInfos.xml',
        defaults=[('NO_TERRAIN', -1)]
    ),
]


def write_out_enum(e):
    # header = "from enum import Enum\n"
    data = {
        'enum_name': e.__name__,
        'members': [
            {
                'name': m,
                'value': e[m].value
            }
            for m in e.__members__
        ]
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


def write_all_enums():
    all_files = building_files + civilization_files + event_files + gameinfo_files \
        + unit_files + terrain_files
    print('from enum import Enum')
    print()
    for en in base_enums:
        write_out_enum(en)
    for file in all_files:
        e = file.to_enum()
        write_out_enum(e)


if __name__ == '__main__':
    write_all_enums()
