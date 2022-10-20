"""The object returned by the `--spoilers` option."""
from typing import List

import attrs

from civ4save.enums import vanilla as e


@attrs.define(slots=True)
class GameState:
    """Supposed to represent state a human player shouldn't necessarily know."""
    total_cities: int
    total_population: int
    nukes_exploded: int
    circumnavigated: bool
    nukes_buildable: bool
    best_land_unit: e.UnitType
    winner: int
    victory: e.VictoryType
    state: e.GameStateType
    scores: List[int]
    # holy cities, corp headquarters
    cities_destroyed: List[str]
    great_people_born: List[str]
    # CvMap
    land_plots: int
    owned_plots: int

    @classmethod
    def from_struct(cls, cv_game, cv_map):
        """Create GameState from the cv_game and cv_map parsed structs."""
        best_land_unit = e.UnitType[cv_game.best_land_unit]
        victory = e.VictoryType[cv_game.victory]
        state = e.GameStateType[cv_game.game_state]
        scores = [s for s in cv_game.ai_player_score if s > 0]
        great_people_born = [gp.name for gp in cv_game.great_people_born]

        return cls(
            cv_game.total_cities,
            cv_game.total_population,
            cv_game.nukes_exploded,
            cv_game.circumnavigated,
            cv_game.nukes_valid,
            best_land_unit,
            cv_game.winner,
            victory,
            state,
            scores,
            cv_game.cities_destroyed,
            great_people_born,
            cv_map.land_plots,
            cv_map.owned_plots
        )
