"""Some potentially interesting stuff with the Civs."""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import importlib_resources
import xmltodict

from ..enums.vanilla import (
    BuildingType,
    CivilizationType,
    LeaderHeadType,
    TechType,
    UnitType,
)


@dataclass
class Civ:
    """Object holding Civ attributes."""
    type: CivilizationType
    description: str
    short_description: str
    cities: List[str]
    unique_building: BuildingType
    unique_unit: UnitType
    starting_techs: Tuple[TechType, TechType]
    leaders: List[LeaderHeadType]

    @classmethod
    def from_dict(cls, d: dict) -> "Civ":
        """Create a new Civ object from a dictionary."""
        techs = [TechType[t] for t in d["starting_techs"]]
        starting_techs = techs[0], techs[1]
        return cls(
            type=CivilizationType[d["type"]],
            description=d["description"],
            short_description=d["short_description"],
            cities=d["cities"],
            unique_building=BuildingType[d["unique_building"]],
            unique_unit=UnitType[d["unique_unit"]],
            starting_techs=starting_techs,
            leaders=[LeaderHeadType[ld] for ld in d["leaders"]]
        )


@lru_cache(1)
def _get_civs_from_xml_files(xml_file: str | Path) -> Dict[str, Civ]:
    """Create a mapping of short_description -> Civ.

    Ex. "Mali": Civ(CivilizationType.CIVILIZATION_MALI, ...)
    """
    civs = {}

    text_map_json = (
        importlib_resources.files("civ4save.contrib.data")
        .joinpath("text_map.json")
        .read_text()
    )
    text_map = json.loads(text_map_json)

    with open(xml_file, "r") as f:
        data = xmltodict.parse(f.read())

    civ_infos = data["Civ4CivilizationInfos"]["CivilizationInfos"]["CivilizationInfo"]
    for civ_info in civ_infos:
        type = CivilizationType[civ_info["Type"]]
        description = text_map.get(civ_info["Description"], civ_info["Type"])
        short_description = text_map.get(civ_info["ShortDescription"], "")
        # TODO actually look up the TXT_KEY
        cities = [text_map.get(c, c) for c in civ_info["Cities"]["City"]]
        try:
            unique_building = BuildingType[
                civ_info["Buildings"]["Building"]["BuildingType"]
            ]
            unique_unit = UnitType[civ_info["Units"]["Unit"]["UnitType"]]
        except TypeError:  # MINOR and BARBARIAN civs
            break
        techs = [TechType[t["TechType"]] for t in civ_info["FreeTechs"]["FreeTech"]]
        starting_techs = techs[0], techs[1]
        try:
            # Multiple Leaders
            leaders = [
                LeaderHeadType[ld["LeaderName"]] for ld in civ_info["Leaders"]["Leader"]
            ]
        except TypeError:
            # Single Leader
            leaders = [LeaderHeadType[civ_info["Leaders"]["Leader"]["LeaderName"]]]
        civ = Civ(
            type,
            description,
            short_description,
            cities,
            unique_building,
            unique_unit,
            starting_techs,
            leaders,
        )
        civs[short_description] = civ
    return civs


@lru_cache(1)
def _get_civ_map() -> dict:
    """Load from json file in contrib/data."""
    civs_json = (
        importlib_resources.files("civ4save.contrib.data")
        .joinpath("civs.json")
        .read_text()
    )
    civs = json.loads(civs_json)
    return civs


def get_civs() -> Dict[str, Civ]:
    """Get all Civs."""
    civs = _get_civ_map()
    return {c: Civ.from_dict(civs[c]) for c in civs}


def get_civ(name: str) -> Optional[Civ]:
    """Get a single Civ by name."""
    civs = _get_civ_map()
    civ_dict = civs.get(name, None)
    if civ_dict:
        return Civ.from_dict(civ_dict)
    return None


if __name__ == "__main__":
    # from ..utils import CustomJsonEncoder
    # CIV_INFOS = Path("xml") / "CIV4CivilizationInfos.xml"
    # civs = _get_civs_from_xml_files(CIV_INFOS)
    # print(json.dumps(civs, cls=CustomJsonEncoder, indent=4))
    print(get_civ("Germany"))
