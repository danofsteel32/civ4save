from dataclasses import dataclass

from civ4save.enums import vanilla as e


@dataclass(slots=True)
class Plot:
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
    yields: list[int]

    @classmethod
    def from_struct(cls, cv_plot):
        plot_type = e.PlotType[cv_plot.plot_type]
        terrain_type = e.TerrainType[cv_plot.terrain_type]
        feature_type = e.FeatureType[cv_plot.feature_type]
        bonus_type = e.BonusType[cv_plot.bonus_type]
        improvement_type = e.ImprovementType[cv_plot.improvement_type]
        return cls(
            cv_plot.x,
            cv_plot.y,
            cv_plot.ownership_duration,
            cv_plot.improvement_duration,
            cv_plot.starting_plot,
            cv_plot.hills,
            cv_plot.potential_city_work,
            cv_plot.irrigated,
            cv_plot.owner,
            plot_type,
            terrain_type,
            feature_type,
            bonus_type,
            improvement_type,
            cv_plot.yields,
        )
