"""Independent wire-layout checks for CvArea and its streamable free list."""

from io import BytesIO
from struct import pack

import pytest
from construct import StreamError, ValidationError

from civ4save.vanilla import enums as e
from civ4save.vanilla.structure import CvArea, CvAreaList


def ints(values):
    return pack(f"<{len(values)}i", *values)


def area_bytes(area_id=8192, water=False):
    # CvArea::write: uint flag, eight signed ints, bool; vanilla has 19 players
    # and teams, 3 yields, 41 unit AI types, 35 bonuses and 25 improvements.
    parts = [pack("<I8i?", 0, area_id, 50, 20, 10, 9, 8, 7, 6, water)]
    parts.extend(ints(list(range(row * 100, row * 100 + 19))) for row in range(13))
    parts.append(ints([-1] * 19))  # NO_AREAAI
    parts.append(ints([-1, -1] * 19))  # IDInfo: owner and city ID
    parts.append(ints(list(range(19 * 3))))
    parts.append(ints(list(range(19 * 41))))
    parts.append(ints(list(range(-19 * 41, 0))))
    parts.append(ints(list(range(35))))
    parts.append(ints(list(range(25))))
    return b"".join(parts)


def area_list_bytes(records, slots=4):
    # Holes in slots 0 and 2; active records need not have contiguous IDs.
    return (
        ints([slots, 3, 0, 2, 16384])
        + ints([2, -1, -1, -1][:slots])
        + ints([len(records)])
        + b"".join(records)
    )


def test_area_wire_layout():
    data = area_bytes(water=True)
    stream = BytesIO(data + b"next section")
    area = CvArea.parse_stream(stream)

    assert stream.read() == b"next section"
    assert area._area_start_index == 0
    assert area._area_end_index == len(data)
    assert area._area_flag == 0
    assert area.area_id == 8192
    assert [
        area.num_tiles,
        area.num_owned_tiles,
        area.num_river_edges,
        area.num_units,
        area.num_cities,
        area.total_population,
        area.num_starting_plots,
    ] == [50, 20, 10, 9, 8, 7, 6]
    assert area.water is True
    for row, field in enumerate(
        [
            "units_per_player",
            "animals_per_player",
            "cities_per_player",
            "pop_per_player",
            "building_good_health_per_player",
            "building_bad_health_per_player",
            "building_happiness_per_player",
            "free_specialist_per_player",
            "power",
            "best_found_value",
            "num_revealed_tiles",
            "clean_power_count",
            "border_obstacle_count",
        ]
    ):
        assert area[field] == list(range(row * 100, row * 100 + 19))
    assert area.area_ai_type == ["NO_AREAAI"] * 19
    assert [(city.owner, city.i_id) for city in area.target_cities] == [(-1, -1)] * 19
    assert area.yield_rate_modifiers == [
        list(range(player * 3, (player + 1) * 3)) for player in range(19)
    ]
    assert area.num_train_ai_units == [
        list(range(player * 41, (player + 1) * 41)) for player in range(19)
    ]
    assert area.num_ai_units == [
        list(range(-19 * 41 + player * 41, -19 * 41 + (player + 1) * 41))
        for player in range(19)
    ]
    assert area.num_bonuses == {e.BonusType(i): i for i in range(35)}
    assert area.num_improvements == {e.ImprovementType(i): i for i in range(25)}


def test_area_list_reads_active_records_and_preserves_next_section():
    records = [area_bytes(8193), area_bytes(8195, water=True)]
    data = area_list_bytes(records)
    stream = BytesIO(data + b"next section")
    parsed = CvAreaList.parse_stream(stream)

    assert parsed.sz_areas == 2
    assert parsed._areas_num_slots == 4
    assert parsed._areas_next_free_index_array == [2, -1, -1, -1]
    assert [area.area_id for area in parsed.areas] == [8193, 8195]
    assert [area.water for area in parsed.areas] == [False, True]
    assert parsed.areas[0]._area_end_index == parsed.areas[1]._area_start_index
    assert parsed._areas_end_index == len(data)
    assert stream.read() == b"next section"


@pytest.mark.parametrize("slots", [0, 4])
def test_empty_area_list(slots):
    parsed = CvAreaList.parse(area_list_bytes([], slots=slots))
    assert parsed.sz_areas == 0
    assert parsed.areas == []


@pytest.mark.parametrize("slots", [-1, 8193])
def test_invalid_slot_count(slots):
    with pytest.raises(ValidationError, match="areas slots"):
        CvAreaList.parse(ints([slots]))


@pytest.mark.parametrize("count", [-1, 5])
def test_invalid_active_count(count):
    header = area_list_bytes([])[:-4] + ints([count])
    with pytest.raises(ValidationError, match="sz_areas"):
        CvAreaList.parse(header)


@pytest.mark.parametrize("missing", [1, 100, 7953])
def test_truncated_area_list_fails(missing):
    data = area_list_bytes([area_bytes(8193), area_bytes(8195)])
    with pytest.raises(StreamError, match="areas"):
        CvAreaList.parse(data[:-missing])
