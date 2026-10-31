"""CvPlot's fixed fields, optional arrays, and exact map plot counts."""

import pytest
from construct import ConstructError, StreamError, ValidationError

from civ4save.vanilla import enums as e
from civ4save.vanilla.structure import CvMap, CvPlot
from tests.binary_helpers import ints, map_bytes, parse_record, plot_bytes


@pytest.mark.parametrize("populated", [False, True])
def test_plot_wire_layout(populated):
    data = plot_bytes(3, 4, populated)
    plot = parse_record(CvPlot, data)
    assert (plot.x, plot.y, plot.area_id) == (3, 4, 8192)
    assert [
        plot.feature_variety,
        plot.ownership_duration,
        plot.improvement_duration,
        plot.upgrade_progress,
        plot.force_unowned_timer,
        plot.city_radius_count,
        plot.river_id,
        plot.min_original_start_distance,
        plot.recon_count,
        plot.river_crossing_count,
    ] == [1, 2, 3, 4, 5, 6, -1, 7, 8, 9]
    assert [
        plot.starting_plot,
        plot.hills,
        plot.north_of_river,
        plot.west_of_river,
        plot.irrigated,
        plot.potential_city_work,
    ] == [True, False, True, False, True, False]
    assert plot.owner == -1
    assert plot.plot_type == "PLOT_LAND"
    assert plot.terrain_type == "TERRAIN_GRASS"
    assert plot.feature_type == "NO_FEATURE"
    assert plot.bonus_type == "NO_BONUS"
    assert plot.improvement_type == "NO_IMPROVEMENT"
    assert (plot.route_type, plot.river_north_south, plot.river_east_west) == (
        -1,
        -1,
        -1,
    )
    assert [
        plot.plot_city_owner,
        plot.plot_city_id,
        plot.working_city_owner,
        plot.working_city_id,
        plot.working_city_override_owner,
        plot.working_city_override_id,
    ] == [-1] * 6
    assert plot.yields == [2, 1, 0]
    for field in [
        "culture",
        "found_value",
        "player_city_radius",
        "plot_group",
        "visibility",
        "stolen_visibility",
        "blockaded",
        "revealed_owner",
        "revealed_improvement_type",
        "revealed_route_type",
    ]:
        assert plot[field].arr == ([-1, 12] if populated else [])
    for field in ["river_crossings", "revealed"]:
        assert plot[field].arr == ([True, False] if populated else [])
    assert plot.plot_script_data == ("plot-é" if populated else "")
    assert plot.build_progress.arr == ([-1, 300] if populated else [])
    if populated:
        assert [row.arr for row in plot.culture_range_cities] == [[-1, 7], []]
        assert [row.arr for row in plot.invisible_visibles] == [[], [-1, 500]]
        assert [(unit.owner, unit.i_id) for unit in plot.units] == [
            (0, 8193),
            (1, 8195),
        ]
    else:
        assert plot.culture_range_cities is None
        assert plot.invisible_visibles is None
        assert plot.units == []
    assert plot._plot_start_index == 0
    assert plot._plot_end_index == plot.plot_sizeof == len(data)


@pytest.mark.parametrize("populated", [False, True])
def test_truncated_plot_fails(populated):
    with pytest.raises(StreamError):
        CvPlot.parse(plot_bytes(populated=populated)[:-1])


@pytest.mark.parametrize("outer_count", [b"\xff", b"\x14"])
@pytest.mark.parametrize(
    "trailing,label", [(6, "culture range cities"), (5, "invisible visibility")]
)
def test_invalid_plot_row_counts(outer_count, trailing, label):
    prefix = plot_bytes()[:-trailing]
    with pytest.raises(ValidationError, match=label):
        CvPlot.parse(prefix + outer_count)


@pytest.mark.parametrize("trailing,field", [(6, "_sz_crc"), (5, "_sz_iv")])
def test_negative_inner_row_count(trailing, field):
    with pytest.raises(ValidationError, match=field):
        CvPlot.parse(plot_bytes()[:-trailing] + b"\x01" + ints(-1))


def test_map_reads_exact_plot_count():
    plots = [plot_bytes(0, 0), plot_bytes(1, 0, populated=True)]
    data = map_bytes(plots)
    raw = parse_record(CvMap, data)
    assert (raw.grid_width, raw.grid_height) == (2, 1)
    assert [(plot.x, plot.y) for plot in raw.plots] == [(0, 0), (1, 0)]
    assert raw.plots[0]._plot_end_index == raw.plots[1]._plot_start_index
    assert raw.sz_areas == 0
    assert raw.areas == []
    assert raw.wrap_x is True and raw.wrap_y is False
    assert (
        raw.land_plots,
        raw.owned_plots,
        raw.top_latitude,
        raw.bottom_latitude,
        raw.next_river_id,
    ) == (2, 1, 90, -90, 7)
    assert raw.bonus_counts == {e.BonusType(i): i for i in range(35)}
    assert raw.bonus_counts_on_land == {e.BonusType(i): 100 + i for i in range(35)}
    assert raw._map_end_index == raw._areas_end_index == len(data)


def test_truncated_map_identifies_plot_and_offset():
    data = map_bytes([plot_bytes()])[:-24]  # remove the area header too
    with pytest.raises(ConstructError, match=r"plot \(1, 0\) at byte \d+"):
        CvMap.parse(data)


@pytest.mark.parametrize("width,height", [(-1, 1), (1, -1)])
def test_invalid_map_dimensions(width, height):
    with pytest.raises(ValidationError, match="grid_"):
        CvMap.parse(map_bytes([], width=width, height=height))


def test_empty_map_reads_no_plots():
    raw = parse_record(CvMap, map_bytes([], width=0, height=0))
    assert raw.plots == []
