"""Some potentially interesting stuff with the Leaders."""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import importlib_resources
import xmltodict

from ..enums.vanilla import (
    CivicType,
    ImprovementType,
    LeaderHeadType,
    ReligionType,
    TraitType,
    UnitAIType,
)


@dataclass
class Leader:
    """Object holding Leader attributes."""

    type: LeaderHeadType
    description: str
    favorite_civic: CivicType
    favorite_religion: ReligionType
    traits: Tuple[TraitType, TraitType]
    flavors: Dict[str, int]
    unit_ai_weight_modifiers: Dict[str, int]
    improvement_weight_modifiers: Dict[str, int]
    wonder_construct_rand: int
    base_attitude: int
    base_peace_weight: int
    peace_weight_rand: int
    warmonger_respect: int
    espionage_weight: int
    refuse_to_talk_war_threshold: int
    no_tech_trade_threshold: int
    tech_trade_known_percent: int
    max_gold_trade_percent: int
    max_gold_trade_per_turn_percent: int
    max_war_rand: int
    max_war_nearby_power_ratio: int
    max_war_distant_power_ratio: int
    max_war_min_adjacent_land_percent: int
    limited_war_rand: int
    limited_war_power_ratio: int
    dogpile_war_rand: int
    make_peace_rand: int
    declare_war_trade_rand: int
    demand_rebuked_sneak_prob: int
    demand_rebuked_war_prob: int
    raze_city_prob: int
    build_unit_prob: int
    base_attack_odds_change: int
    attack_odds_change_rand: int
    worse_rank_difference_attitude: int
    better_rank_difference_attitude: int
    close_borders_attitude_change: int
    lost_war_attitude_change: int
    vassal_power_modifier: int
    freedom_appreciation: int

    @classmethod
    def from_dict(cls, d: dict) -> "Leader":
        """Create a new Leader object from a dictionary."""
        d["type"] = LeaderHeadType[d["type"]]
        d["favorite_civic"] = CivicType[d["favorite_civic"]]
        d["favorite_religion"] = ReligionType[d["favorite_religion"]]
        traits = sorted([TraitType[t] for t in d["traits"]], key=lambda x: x.name)
        d["traits"] = traits[0], traits[1]
        return cls(**d)


def leader_attributes() -> List[str]:
    """Returns List of all Leader attributes."""
    return List(Leader.__dict__["__dataclass_fields__"].keys())


@lru_cache(1)
def _get_leaders_from_xml_file(xml_file: str | Path) -> Dict[str, Leader]:
    leaders = {}

    text_map_json = (
        importlib_resources.files("civ4save.contrib.data")
        .joinpath("text_map.json")
        .read_text()
    )
    text_map = json.loads(text_map_json)

    with open(xml_file, "r") as f:
        data = xmltodict.parse(f.read())

    leader_infos = data["Civ4LeaderHeadInfos"]["LeaderHeadInfos"]["LeaderHeadInfo"]
    for leader_info in leader_infos:
        type = LeaderHeadType[leader_info["Type"]]
        if type == LeaderHeadType.LEADER_BARBARIAN:
            continue
        description = text_map.get(
            leader_info["Description"], leader_info["Description"]
        )

        try:
            favorite_civic = CivicType[leader_info["FavoriteCivic"]]
        except KeyError:
            favorite_civic = CivicType.NO_CIVIC
        try:
            favorite_religion = ReligionType[leader_info["FavoriteReligion"]]
        except KeyError:
            favorite_religion = ReligionType.NO_RELIGION

        trait_types = sorted(
            [TraitType[t["TraitType"]] for t in leader_info["Traits"]["Trait"]],
            key=lambda x: x.name,
        )
        traits = trait_types[0], trait_types[1]
        try:
            flavors = {
                f["FlavorType"]: int(f["iFlavor"])
                for f in leader_info["Flavors"]["Flavor"]
            }
        except TypeError:
            flavors = {}

        try:
            u_mods = leader_info["UnitAIWeightModifiers"]["UnitAIWeightModifier"]
            u_type = UnitAIType[u_mods["UnitAIType"]]
            u_weight = int(u_mods["iWeightModifier"])
            unit_ai_weight_modifiers = {u_type.name: u_weight}
        except TypeError:
            unit_ai_weight_modifiers = {}

        try:
            i_mods = leader_info["ImprovementWeightModifiers"][
                "ImprovementWeightModifier"
            ]
            i_type = ImprovementType[i_mods["ImprovementType"]]
            i_weight = int(i_mods["iWeightModifier"])
            improvement_weight_modifiers = {i_type.name: i_weight}
        except TypeError:
            improvement_weight_modifiers = {}

        wonder_construct_rand = int(leader_info["iWonderConstructRand"])
        base_attitude = int(leader_info["iBaseAttitude"])
        base_peace_weight = int(leader_info["iBasePeaceWeight"])
        peace_weight_rand = int(leader_info["iPeaceWeightRand"])
        warmonger_respect = int(leader_info["iWarmongerRespect"])
        espionage_weight = int(leader_info["iEspionageWeight"])
        refuse_to_talk_war_threshold = int(leader_info["iRefuseToTalkWarThreshold"])
        no_tech_trade_threshold = int(leader_info["iNoTechTradeThreshold"])
        tech_trade_known_percent = int(leader_info["iTechTradeKnownPercent"])
        max_gold_trade_percent = int(leader_info["iMaxGoldTradePercent"])
        max_gold_trade_per_turn_percent = int(
            leader_info["iMaxGoldPerTurnTradePercent"]
        )
        max_war_rand = int(leader_info["iMaxWarRand"])
        max_war_nearby_power_ratio = int(leader_info["iMaxWarNearbyPowerRatio"])
        max_war_distant_power_ratio = int(leader_info["iMaxWarDistantPowerRatio"])
        max_war_min_adjacent_land_percent = int(
            leader_info["iMaxWarMinAdjacentLandPercent"]
        )
        limited_war_rand = int(leader_info["iLimitedWarRand"])
        limited_war_power_ratio = int(leader_info["iLimitedWarPowerRatio"])
        dogpile_war_rand = int(leader_info["iDogpileWarRand"])
        make_peace_rand = int(leader_info["iMakePeaceRand"])
        declare_war_trade_rand = int(leader_info["iDeclareWarTradeRand"])
        demand_rebuked_sneak_prob = int(leader_info["iDemandRebukedSneakProb"])
        demand_rebuked_war_prob = int(leader_info["iDemandRebukedWarProb"])
        raze_city_prob = int(leader_info["iRazeCityProb"])
        build_unit_prob = int(leader_info["iBuildUnitProb"])
        base_attack_odds_change = int(leader_info["iBaseAttackOddsChange"])
        attack_odds_change_rand = int(leader_info["iAttackOddsChangeRand"])
        worse_rank_difference_attitude = int(
            leader_info["iWorseRankDifferenceAttitudeChange"]
        )
        better_rank_difference_attitude = int(
            leader_info["iBetterRankDifferenceAttitudeChange"]
        )
        close_borders_attitude_change = int(leader_info["iCloseBordersAttitudeChange"])
        lost_war_attitude_change = int(leader_info["iLostWarAttitudeChange"])
        vassal_power_modifier = int(leader_info["iVassalPowerModifier"])
        freedom_appreciation = int(leader_info["iFreedomAppreciation"])

        leader = Leader(
            type=type,
            description=description,
            favorite_civic=favorite_civic,
            favorite_religion=favorite_religion,
            traits=traits,
            flavors=flavors,
            unit_ai_weight_modifiers=unit_ai_weight_modifiers,
            improvement_weight_modifiers=improvement_weight_modifiers,
            wonder_construct_rand=wonder_construct_rand,
            base_attitude=base_attitude,
            base_peace_weight=base_peace_weight,
            peace_weight_rand=peace_weight_rand,
            warmonger_respect=warmonger_respect,
            espionage_weight=espionage_weight,
            refuse_to_talk_war_threshold=refuse_to_talk_war_threshold,
            no_tech_trade_threshold=no_tech_trade_threshold,
            tech_trade_known_percent=tech_trade_known_percent,
            max_gold_trade_percent=max_gold_trade_percent,
            max_gold_trade_per_turn_percent=max_gold_trade_per_turn_percent,
            max_war_rand=max_war_rand,
            max_war_nearby_power_ratio=max_war_nearby_power_ratio,
            max_war_distant_power_ratio=max_war_distant_power_ratio,
            max_war_min_adjacent_land_percent=max_war_min_adjacent_land_percent,
            limited_war_rand=limited_war_rand,
            limited_war_power_ratio=limited_war_power_ratio,
            dogpile_war_rand=dogpile_war_rand,
            make_peace_rand=make_peace_rand,
            declare_war_trade_rand=declare_war_trade_rand,
            demand_rebuked_sneak_prob=demand_rebuked_sneak_prob,
            demand_rebuked_war_prob=demand_rebuked_war_prob,
            raze_city_prob=raze_city_prob,
            build_unit_prob=build_unit_prob,
            base_attack_odds_change=base_attack_odds_change,
            attack_odds_change_rand=attack_odds_change_rand,
            worse_rank_difference_attitude=worse_rank_difference_attitude,
            better_rank_difference_attitude=better_rank_difference_attitude,
            close_borders_attitude_change=close_borders_attitude_change,
            lost_war_attitude_change=lost_war_attitude_change,
            vassal_power_modifier=vassal_power_modifier,
            freedom_appreciation=freedom_appreciation,
        )
        leaders[description] = leader
    return leaders


@lru_cache(1)
def _get_leader_map():
    """Load from json file in contrib/data."""
    leaders_json = (
        importlib_resources.files("civ4save.contrib.data")
        .joinpath("leaders.json")
        .read_text()
    )
    leaders = json.loads(leaders_json)
    return leaders


def rank_leaders(attribute: str, reverse: bool = False) -> List[Tuple]:
    """Returns a sorted List of Tuples (description, attribute) by attribute value.

    Accepts attributes in CamelCase or snake_case.
    """
    leader_map = _get_leader_map()
    leaders = [Leader.from_dict(leader_map[ld]) for ld in leader_map]

    # convert Camel -> snake
    attribute = "".join(
        ["_" + c.lower() if c.isupper() else c for c in attribute]
    ).lstrip("_")

    ranked: List[Leader] = []
    if attribute == "traits":
        ranked = sorted(leaders, key=lambda x: x.traits[0].name)

    while not ranked:
        try:
            ranked = sorted(
                leaders, key=lambda x: getattr(x, attribute), reverse=reverse
            )
        except TypeError:
            try:
                # Enum
                ranked = sorted(
                    leaders, key=lambda x: getattr(x, attribute).name, reverse=reverse
                )
            except AttributeError:
                # Dict
                ranked = sorted(leaders, key=lambda x: x.description)

    return [(ld.description, getattr(ld, attribute)) for ld in ranked]


def get_leader(name: str) -> Optional[Leader]:
    """Returns Leader where name == Leader.description or None."""
    leaders = _get_leader_map()
    l_dict = leaders.get(name, None)
    if l_dict:
        return Leader.from_dict(l_dict)
    return None


def get_leaders() -> Dict[str, Leader]:
    """Returns a dict of leader descriptions mapped to the Leader object."""
    leaders = _get_leader_map()
    return {ld: Leader.from_dict(leaders[ld]) for ld in leaders}


if __name__ == "__main__":
    # from ..utils import CustomJsonEncoder
    # LEADER_INFOS = Path("xml") / "CIV4LeaderHeadInfos.xml"
    # leaders = _get_leaders_from_xml_file(LEADER_INFOS)
    # print(json.dumps(leaders, cls=CustomJsonEncoder, indent=4))
    print(leader_attributes())
