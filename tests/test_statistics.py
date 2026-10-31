"""Statistics bytes follow CvStatistics.cpp, not the production builders."""

from types import SimpleNamespace

import pytest
from construct import Computed, ConstructError, Struct

from civ4save.vanilla.structure import (
    CvGameRecord,
    CvPlayerRecord,
    CvStatistics,
    EngineSigns,
    MapSign,
    SaveFooter,
)
from tests.binary_helpers import ints, narrow, parse_record, wide


def statistics_player_bytes(player_id):
    return (
        ints(0, player_id, 123, -1, 4)
        + ints(*range(123))
        + ints(*range(-123, 0))
        + ints(*range(200, 323))
        + ints(*range(159))
        + b"\1\0\1\0\0\1\0"
        + ints(12, 3, 2)
    )


def footer_bytes(python_data=b"S''\np0\n.", engine_data=b"\0" * 32):
    return (
        ints(len(python_data))
        + python_data
        + engine_data
        + b"\0"
        + narrow("0123456789abcdef" * 2)
    )


def test_game_statistics_layout():
    raw = parse_record(CvGameRecord, ints(0, -1) + narrow("Map-é😀"))
    assert raw.era == -1
    assert raw.map_name == "Map-é😀"


def test_player_statistics_layout():
    data = statistics_player_bytes(18)
    assert len(data) == 2151
    raw = parse_record(CvPlayerRecord, data)
    assert (raw.id, raw.time_played, raw.victory, raw.leader) == (18, 123, -1, 4)
    assert raw.units_built == list(range(123))
    assert raw.units_killed == list(range(-123, 0))
    assert raw.units_lost == list(range(200, 323))
    assert raw.buildings_built == list(range(159))
    assert raw.religions_founded == [True, False, True, False, False, True, False]
    assert (raw.cities_built, raw.cities_razed, raw.golden_ages) == (12, 3, 2)
    assert raw._player_record_end_index == len(data)


def statistics_schema(ever_alive):
    return Struct(
        "player_records"
        / Computed(
            [
                SimpleNamespace(ever_alive=i in ever_alive, alive=False)
                for i in range(19)
            ]
        ),
        "statistics" / CvStatistics,
    )


@pytest.mark.parametrize("player_ids", [[], [2, 18], list(range(19))])
def test_statistics_ever_alive_slots(player_ids):
    # Includes dead players and the barbarian slot, skips never-alive slots.
    data = ints(0, -1) + narrow("")
    data += b"".join(statistics_player_bytes(i) for i in player_ids)
    raw = parse_record(statistics_schema(player_ids), data).statistics
    assert [p.id for p in raw.players] == player_ids
    assert raw._statistics_start_index == 0
    assert raw._statistics_end_index == len(data)


def test_statistics_wrong_player_id():
    data = ints(0, -1) + narrow("") + statistics_player_bytes(0)
    with pytest.raises(ConstructError):
        statistics_schema([18]).parse(data)


@pytest.mark.parametrize("cut", [0, 1, 8, 20, 100, 2140, 2150])
def test_truncated_statistics_player(cut):
    with pytest.raises(ConstructError):
        CvPlayerRecord.parse(statistics_player_bytes(0)[:cut])


def test_invalid_statistics_map_name_length():
    with pytest.raises(ConstructError):
        CvGameRecord.parse(ints(0, -1, -1))


@pytest.mark.parametrize(
    "python_data,engine_data",
    [(b"", ints(0, 0)), (b"\x80\xff\0python", ints(0, 0) + b"\xff\0engine\x80")],
)
def test_footer_keeps_binary_payloads_without_unpickling(python_data, engine_data):
    # Deliberately not a pickle or UTF-8 string: data stays uninterpreted bytes.
    data = footer_bytes(python_data, engine_data)
    raw = SaveFooter.parse(data)
    assert raw.python_data == python_data
    assert raw.engine_data == engine_data
    assert raw.signs == []
    assert raw.checksum_byte == 0
    assert raw.checksum == "0123456789abcdef" * 2
    assert raw._footer_end_index == len(data)


@pytest.mark.parametrize("cut", [0, 3, 8, 12, 36, 37, 48, 80])
def test_truncated_footer(cut):
    with pytest.raises(ConstructError):
        SaveFooter.parse(footer_bytes()[:cut])


@pytest.mark.parametrize(
    "data",
    [
        ints(-1),
        ints(1000) + b"short",
        footer_bytes()[:-36] + ints(31) + b"a" * 32,
        footer_bytes()[:-32] + b"z" * 32,
        footer_bytes() + b"unexpected trailing bytes",
    ],
)
def test_malformed_footer(data):
    with pytest.raises(ConstructError):
        SaveFooter.parse(data)


def test_map_sign_layout():
    data = ints(-1, 56, 23, 18) + wide("City-é😀")
    sign = parse_record(MapSign, data)
    assert (sign.x, sign.y, sign.caption) == (56, 23, "City-é😀")
    assert sign._unknown_before_coordinates == ints(-1)
    assert sign._unknown_after_coordinates == ints(18)


def test_footer_signs_preserve_remaining_engine_data():
    signs = ints(7, 2) + ints(0, 56, 23, 0) + wide("X")
    signs += ints(0, 59, 11, 0) + wide("")
    engine_data = signs + b"\xffunidentified geometry\0"
    raw = SaveFooter.parse(footer_bytes(engine_data=engine_data))
    assert [(s.x, s.y, s.caption) for s in raw.signs] == [(56, 23, "X"), (59, 11, "")]
    assert raw.engine_data == engine_data
    assert parse_record(EngineSigns, signs).signs == raw.signs


@pytest.mark.parametrize(
    "engine_data",
    [
        b"",
        ints(0),
        ints(0, -1),
        ints(0, 1),
        ints(0, 1, 0, 56, 23, 0, -1),
        ints(0, 1, 0, 56, 23, 0, 1),
        ints(0, 1, 0, 56, 23, 0, 2) + b"X\0",
    ],
)
def test_invalid_signs_do_not_read_checksum_bytes(engine_data):
    with pytest.raises(ConstructError):
        SaveFooter.parse(footer_bytes(engine_data=engine_data))
