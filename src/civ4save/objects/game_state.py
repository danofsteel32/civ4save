"""The object returned by the `--spoilers` option."""
from __future__ import annotations

from typing import Any, List

import attrs

from civ4save.vanilla import enums as e


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
    def from_struct(cls, data: Any) -> GameState:
        """Create GameState from the parsed struct."""
        best_land_unit = e.UnitType[data.best_land_unit]
        victory = e.VictoryType[data.victory]
        state = e.GameStateType[data.game_state]
        scores = [s for s in data.ai_player_score if s > 0]

        return cls(
            data.total_cities,
            data.total_population,
            data.nukes_exploded,
            data.circumnavigated,
            data.nukes_valid,
            best_land_unit,
            data.winner,
            victory,
            state,
            scores,
            data.cities_destroyed,
            data.great_people_born,
            data.land_plots,
            data.owned_plots,
        )
