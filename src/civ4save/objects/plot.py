"""Used in `SaveFile.plots`."""
from __future__ import annotations

from typing import Any, List

import attrs

from civ4save.vanilla import enums as e


@attrs.define(slots=True)
class Plot:
    """Represents a plot."""

    x: int
    y: int
    ownership_duration: int
    improvement_duration: int
    starting_plot: bool
    hills: bool
    can_be_worked: bool
    irrigated: bool
    owner: int
    plot_type: e.PlotType
    terrain_type: e.TerrainType
    feature_type: e.FeatureType
    bonus_type: e.BonusType
    improvement_type: e.ImprovementType
    yields: List[int]

    @classmethod
    def from_struct(cls, data: Any) -> Plot:
        """Return `Plot` from parsed struct."""
        plot_type = e.PlotType[data.plot_type]
        terrain_type = e.TerrainType[data.terrain_type]
        feature_type = e.FeatureType[data.feature_type]
        bonus_type = e.BonusType[data.bonus_type]
        improvement_type = e.ImprovementType[data.improvement_type]
        return cls(
            data.x,
            data.y,
            data.ownership_duration,
            data.improvement_duration,
            data.starting_plot,
            data.hills,
            data.potential_city_work,
            data.irrigated,
            data.owner,
            plot_type,
            terrain_type,
            feature_type,
            bonus_type,
            improvement_type,
            data.yields,
        )
