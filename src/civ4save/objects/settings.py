"""The object returned by the `--settings` option."""
from __future__ import annotations

from typing import Any, Dict

import attrs

from civ4save.vanilla import enums as e


@attrs.define(slots=True)
class Settings:
    """Class representing the game's settings (sp only)."""

    # CvInitCore
    game_type: e.GameType
    game_name: str
    map_script: str
    """Name of the map script"""
    world_size: e.WorldType
    climate: e.ClimateType
    sea_level: e.SeaLevelType
    start_era: e.EraType
    game_speed: e.GameSpeedType
    game_options: Dict[str, bool]
    """Each GameOption and whether it's enabled"""
    max_turns: int
    advanced_start_points: int
    victories: Dict[str, bool]
    """Each VictoryType and whether it's enabled"""
    num_civs: int
    """Number of civs (not counting barbs)"""

    # CvGame
    start_turn: int
    start_year: int
    handicap: e.HandicapType
    map_random_seed: int
    soren_random_seed: int
    culture_victory_cities: int
    culture_victory_level: e.CultureLevelType

    # CvMap
    grid_width: int
    grid_height: int
    wrap_x: bool
    wrap_y: bool

    @classmethod
    def from_struct(cls, data: Any) -> Settings:
        """Return `Settings` from the parsed struct."""
        game_type = e.GameType[data.game_type]
        game_speed = e.GameSpeedType[data.game_speed]
        world_size = e.WorldType[data.world_size]
        climate = e.ClimateType[data.climate]
        sea_level = e.SeaLevelType[data.sea_level]
        start_era = e.EraType[data.start_era]

        handicap = e.HandicapType[data.handicap]
        culture_victory_level = e.CultureLevelType[data.culture_victory_level]

        game_options = {
            e.GameOptionType(n).name: v for n, v in enumerate(data.game_options)
        }

        advanced_start_points = 0
        if game_options["GAMEOPTION_ADVANCED_START"]:
            advanced_start_points = data.advanced_start_points

        victories = {e.VictoryType(n).name: v for n, v in enumerate(data.victories)}

        num_civs = len([c for c in data.civs[:-1] if c != "NO_CIVILIZATION"])

        return cls(
            game_type=game_type,
            game_name=data.game_name,
            map_script=data.map_script_name,
            world_size=world_size,
            climate=climate,
            sea_level=sea_level,
            start_era=start_era,
            game_speed=game_speed,
            game_options=game_options,
            max_turns=data.max_turns,
            advanced_start_points=advanced_start_points,
            victories=victories,
            num_civs=num_civs,
            start_turn=data.start_turn,
            start_year=data.start_year,
            handicap=handicap,
            map_random_seed=data.map_random_seed,
            soren_random_seed=data.soren_random_seed,
            culture_victory_cities=data.num_culture_victory_cities,
            culture_victory_level=culture_victory_level,
            grid_width=data.grid_width,
            grid_height=data.grid_height,
            wrap_x=data.wrap_x,
            wrap_y=data.wrap_y,
        )
