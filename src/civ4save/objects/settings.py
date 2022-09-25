from dataclasses import dataclass

from civ4save.enums import vanilla as e


@dataclass(slots=True)
class Settings:
    """
    Class representing the game's settings (sp only)
    """

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
    game_options: dict[str, bool]
    """Each GameOption and whether it's enabled"""
    max_turns: int
    advanced_start_points: int
    victories: dict[str, bool]
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
    def from_struct(cls, cv_init, cv_game, cv_map):
        game_type = e.GameType[cv_init.game_type]
        game_speed = e.GameSpeedType[cv_init.game_speed]
        world_size = e.WorldType[cv_init.world_size]
        climate = e.ClimateType[cv_init.climate]
        sea_level = e.SeaLevelType[cv_init.sea_level]
        start_era = e.EraType[cv_init.start_era]

        handicap = e.HandicapType[cv_game.handicap]
        culture_victory_level = e.CultureLevelType[cv_game.culture_victory_level]

        game_options = {
            e.GameOptionType(n).name: v for n, v in enumerate(cv_init.game_options)
        }

        advanced_start_points = 0
        if game_options["GAMEOPTION_ADVANCED_START"]:
            advanced_start_points = cv_init.advanced_start_points

        victories = {e.VictoryType(n).name: v for n, v in enumerate(cv_init.victories)}

        num_civs = len([c for c in cv_init.civs[:-1] if c != "NO_CIVILIZATION"])

        return cls(
            game_type=game_type,
            game_name=cv_init.game_name,
            map_script=cv_init.map_script_name,
            world_size=world_size,
            climate=climate,
            sea_level=sea_level,
            start_era=start_era,
            game_speed=game_speed,
            game_options=game_options,
            max_turns=cv_init.max_turns,
            advanced_start_points=advanced_start_points,
            victories=victories,
            num_civs=num_civs,
            start_turn=cv_game.start_turn,
            start_year=cv_game.start_year,
            handicap=handicap,
            map_random_seed=cv_game.map_random_seed,
            soren_random_seed=cv_game.soren_random_seed,
            culture_victory_cities=cv_game.num_culture_victory_cities,
            culture_victory_level=culture_victory_level,
            grid_width=cv_map.grid_width,
            grid_height=cv_map.grid_height,
            wrap_x=cv_map.wrap_x,
            wrap_y=cv_map.wrap_y,
        )

