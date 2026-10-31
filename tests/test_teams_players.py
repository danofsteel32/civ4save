"""Handwritten SDK wire layouts, independent of Construct's production builders."""

from io import BytesIO
from pathlib import Path
from struct import pack

import pytest
from construct import ConstructError, StreamError, ValidationError

from civ4save import SaveFile
from civ4save.vanilla.structure import (
    CvCityAI,
    CvDiploParameters,
    CvPlayer,
    CvPlayerAI,
    CvPlotGroup,
    CvPopupInfo,
    CvSelectionGroupAI,
    CvTalkingHeadMessage,
    CvTeam,
    CvTeamAI,
    CvUnitAI,
    EventTriggeredData,
    FVariable,
    IndexedRecord,
    OrderData,
)
from tests.binary_helpers import free_list, ints, narrow, parse_record, wide


def fixed_ints(length, value=0):
    return ints(*([value] * length))


def counted(records):
    return ints(len(records)) + b"".join(records)


def team_bytes(ai=False, projects=True):
    data = ints(0, *range(-12, 12)) + b"\1\0" + ints(3)
    data += b"".join(fixed_ints(n, i) for i, n in enumerate([19] * 6 + [4, 4, 2]))
    data += bytes([0, 1] * 66 + [1]) + bytes([1, 0, 1, 0, 1, 0, 1])
    data += ints(-1, 8)  # route changes
    data += ints(*([2, 0, 1] + [0] * 8 if projects else [0] * 11))
    data += fixed_ints(11, -1)  # project default art types
    if projects:
        data += ints(17, 18, -1)  # counts, not a separate length per project
    data += b"".join(
        fixed_ints(n, i - 3) for i, n in enumerate([11, 89, 125, 159, 92, 92, 9, 7])
    )
    data += b"\1" * 92 + b"\0" * 92
    data += ints(*range(75))
    data += ints(2, 0, 34)  # revealed bonuses
    if ai:
        data += ints(0) + b"".join(fixed_ints(19, i - 1) for i in range(11)) + ints(-1)
    return data


@pytest.mark.parametrize("ai", [False, True])
@pytest.mark.parametrize("projects", [False, True])
def test_team_layout(ai, projects):
    data = team_bytes(ai, projects)
    team = parse_record(CvTeamAI if ai else CvTeam, data)
    assert team.id == 3
    assert team.num_members == -12
    assert team.espionage_points_ever == 11
    assert team.map_centering and not team.capitulated
    assert team.counterespionage_mod_against_team == [5] * 19
    assert team.commerce_flexible_count == [6] * 4
    assert team.extra_moves == [7] * 4
    assert team.force_team_vote_eligibility_count == [8] * 2
    assert team.has_met == [False, True] * 9 + [False]
    assert team.can_launch == [True, False, True, False, True, False, True]
    assert team.route_change == [-1, 8]
    assert team.project_art_types == (
        [[17, 18], [], [-1]] + [[]] * 8 if projects else [[]] * 11
    )
    assert team.project_making == [-3] * 11
    assert team.victory_countdown == [4] * 7
    assert team.has_tech == [True] * 92
    assert team.improvement_yield_change[-1] == [72, 73, 74]
    assert team.revealed_bonuses == ["BONUS_ALUMINUM", "BONUS_MOVIES"]
    if ai:
        assert team.war_plan_state_counter == [-1] * 19
        assert team.war_plan == [9] * 19
        assert team.worst_enemy == -1
        assert team._team_ai_end_index == len(data)


def event_bytes():
    return ints(*range(-1, 12)) + wide("event-é😀") + wide("global")


def plot_group_bytes():
    return ints(0, 8195, 2) + ints(*range(35)) + ints(2, -1, 8, 3, 4)


def city_bytes():
    data = ints(0, *range(87)) + bytes([1, 0, 1, 0, 1, 0, 1, 0, 1])
    data += ints(2, -1, 2, 0)
    data += b"".join(
        fixed_ints(n, i) for i, n in enumerate([3] * 9 + [4] * 8 + [4] * 2 + [19] * 2)
    )
    data += b"\0" * (19 * 4)
    data += wide("city-é😀") + narrow("script-é")
    for i, n in enumerate(
        [35] * 4
        + [11]
        + [159] * 4
        + [123] * 4
        + [14] * 4
        + [25]
        + [7] * 2
        + [10, 54, 159, 159]
    ):
        data += fixed_ints(n, i)
    data += b"\1" * 21 + b"\0" * 7 + b"\1" * 7
    data += ints(*([-1, -1] * 8))
    # OrderData occupies 16 bytes; the last three are padding, not fields.
    data += ints(1, 0, 7, -1) + b"\1\xaa\xbb\xcc"
    data += ints(4) + b"\1" + ints(1, 2, 3) + b"\1\0\1"
    data += ints(4, 5, 6) + b"\0\1\0" + ints(7, 8, 9, 10) + b"\1\0\1\0"
    data += ints(1, 0)  # event
    data += ints(1, 2, 0, -3) + ints(1, 3, 1, -4)  # yield/commerce changes
    data += ints(1, 4, -5) + ints(1, 5, -6)  # happy/health changes
    # CvCityAI trailer
    data += ints(0, 1, 2) + b"\1\0" + ints(-1, -1)
    data += ints(3, 4, 5, 6, 7, 8, 9) + b"\1"
    data += fixed_ints(21, 10) + fixed_ints(21, -1) + b"\1\0\1\0\1\0"
    data += ints(11, 12, 13, 14, 15) + fixed_ints(19, 16) + ints(17, 18, 19, 20)
    return data


def unit_bytes(flag=2):
    data = ints(flag, *range(19))
    if flag < 2:
        data += ints(-99)  # removed combat damage
    data += ints(*range(19, 57)) + b"\1\0\1\0\1\0"
    if flag > 0:
        data += b"\1"  # added air combat flag
    data += ints(2, -1, 0, -1, -1, -1, 2, 8193)
    data += ints(-1, 1, 2, 3) + wide("unit-é😀") + narrow("unit script")
    data += b"\1\0" * 27
    for i, n in enumerate([9, 6, 9, 9, 6, 6, 10]):
        data += fixed_ints(n, i - 1)
    return data + ints(0, 42, 0, -1)  # CvUnitAI


def selection_group_bytes():
    data = ints(0, 8193, 4) + b"\1" + ints(2, 0, -1)
    data += ints(1, 2, 8194)  # units, IDInfo
    data += ints(1, 0, 1, -1, 3, 4)  # MissionData, 20 raw bytes
    data += ints(0, 12, 13) + b"\1" + ints(-1, 2, 8194)
    return data + b"\0" + ints(-1, -1)


def message_bytes():
    return (
        wide("message-é😀")
        + narrow("sound")
        + narrow("icon")
        + ints(5, 6, 7, 8)
        + b"\1\0"
        + ints(9, 10, -1, -1)
        + b"\1"
    )


def popup_bytes():
    return (
        ints(1, 2, 3, 4)
        + b"\1\0"
        + ints(5)
        + wide("popup-é😀")
        + narrow("focus")
        + narrow("clicked")
        + narrow("module")
        + ints(1)
        + wide("button")
        + narrow("art")
    )


def diplo_bytes():
    data = ints(0, 1, -1)
    data += ints(1, 7, 50) + b"\1\0\xab\xcd" + ints(0)  # offers
    data += b"\1\0" + ints(-1) + b"\1\0\1" + wide("chat-é😀")
    return (
        data
        + ints(3, 5)
        + pack("<q", -42)
        + ints(9)
        + narrow("argument")
        + ints(10)
        + wide("wide😀")
    )


@pytest.mark.parametrize("flag", [0, 1, 2])
def test_unit_version_flags(flag):
    unit = parse_record(CvUnitAI, unit_bytes(flag))
    assert unit.id == 0 and unit.group_id == 1
    assert unit.combat_damage == (-99 if flag < 2 else None)
    assert unit.fortify_turns == 19 and unit.immobile_timer == 56
    assert unit.air_combat == (True if flag > 0 else None)
    assert unit.owner == 2 and unit.transport_unit_id == 8193
    assert unit.name == "unit-é😀"
    assert unit.has_promotion == [True, False] * 27
    assert unit.extra_unit_combat_modifier == [5] * 10
    assert unit.birthmark == 42 and unit.automated_abort_turn == -1


def test_city_and_queues():
    city = parse_record(CvCityAI, city_bytes())
    assert city.id == 0 and city.espionage_defense_modifier == 86
    assert city.name == "city-é😀" and city.script_data == "script-é"
    assert city.num_free_building == [23] * 159
    assert city.working_plot == [True] * 21
    assert city.trade_cities[7].i_id == -1
    assert city.order_queue[0].data2 == -1 and city.order_queue[0].save
    assert city.population_rank == 4 and city.population_rank_valid
    assert city.commerce_rank == [7, 8, 9, 10]
    assert city.events_occurred == ["EVENT_FOREST_FIRE_1"]
    assert city.building_yield_change[0].change == -3
    assert city.building_health_change[0].change == -6
    assert city.route_to_city_id == -1
    assert city.workers_have == 20
    assert OrderData.sizeof() == 16


def test_other_owned_records():
    group = parse_record(CvPlotGroup, plot_group_bytes())
    assert group.id == 8195 and group.plots[0].x == -1
    event = parse_record(EventTriggeredData, event_bytes())
    assert event.id == -1 and event.building == 11 and event.text == "event-é😀"
    selection = parse_record(CvSelectionGroupAI, selection_group_bytes())
    assert selection.units[0].i_id == 8194
    assert selection.mission_queue[0].data2 == -1
    assert selection.mission_ai_x == 12 and selection.mission_ai_y == 13
    message = parse_record(CvTalkingHeadMessage, message_bytes())
    assert message.description == "message-é😀" and message.shown
    assert message.from_player == -1
    popup = parse_record(CvPopupInfo, popup_bytes())
    assert popup.text == "popup-é😀" and popup.python_buttons[0].art == "art"
    diplo = parse_record(CvDiploParameters, diplo_bytes())
    assert diplo.our_offer[0].extra_data == 50 and not diplo.their_offer
    assert diplo.diplo_comment_args[0].value == pack("<q", -42)
    assert diplo.diplo_comment_args[1].value == "argument"
    assert diplo.diplo_comment_args[2].value == "wide😀"


def player_bytes(flag=1, populated=False, ai=False):
    data = ints(flag, *range(92)) + b"\1\0\1\0\1\0\1\0\1"
    data += ints(2, 0, 0, -1, -1)
    data += b"".join(
        fixed_ints(n, i) for i, n in enumerate([3] * 5 + [4] * 8 + [19, 19])
    )
    data += b"\1" * 31 + b"\0" * 22 + narrow("player-é😀")
    for i, n in enumerate(
        [35, 35, 25, 159, 159, 159, 6, 89, 89, 125, 125, 2, 4, 5, 5, 7, 7, 3, 14]
    ):
        data += fixed_ints(n, i - 1)
    data += b"\1" * 92 + b"\0\1"  # researching tech, loyal member
    data += ints(0, 5, 10, 15, 20)
    data += ints(*range(42)) + ints(*range(75))
    data += ints(2, -1, 8193) + ints(1, 0)  # group cycle, research queue
    data += ints(1) + wide("future city-é😀")
    for record in [
        plot_group_bytes(),
        city_bytes(),
        unit_bytes(),
        selection_group_bytes(),
        event_bytes(),
    ]:
        data += free_list([record] if populated else [])
    for record in [message_bytes(), popup_bytes(), diplo_bytes()]:
        data += counted([record] if populated else [])
    for i in range(7):
        data += ints(2, -1, i, 10, i + 100)  # seven history maps
    for record in [
        ints(0) + event_bytes(),
        ints(1) + event_bytes(),
        ints(0, 1),
        ints(2, 3),
        ints(7, -1),
        ints(8, -2),
    ]:
        data += counted([record] if populated else [])
    if flag > 0:
        data += ints(2, 0, 196)
    else:
        data += b"\1" + b"\0" * 175  # original 176 event trigger bools
    data += ints(-3, 17)
    if ai:
        data += ints(0, *range(10)) + ints(*range(11)) + ints(-1, -2, -3)
        for i, n in enumerate([41, 41] + [19] * 8):
            data += fixed_ints(n, i)
        data += b"\1" * 19 + fixed_ints(19 * 14, -1) + fixed_ints(19 * 33, 2)
        data += b"\1" + ints(18, 2, -1, 99)
        data += (
            fixed_ints(35, 20)
            + fixed_ints(89, 21)
            + fixed_ints(10, 22)
            + fixed_ints(19, 23)
        )
    return data


@pytest.mark.parametrize("flag", [0, 1])
@pytest.mark.parametrize("populated", [False, True])
@pytest.mark.parametrize("ai", [False, True])
def test_player_layout(flag, populated, ai):
    data = player_bytes(flag, populated, ai)
    player = parse_record(CvPlayerAI if ai else CvPlayer, data)
    assert player.id == 2 and player.combat_experience == 91
    assert player.alive and not player.ever_alive
    assert player.gold == 5 and player.capital_city_id == 82
    assert player.sea_plot_yield == [0] * 3
    assert player.espionage_spending_weight_against_team == [14] * 19
    assert player.feat_accomplished == [True] * 31
    assert player.script_data == "player-é😀"
    assert player.specialist_valid_count == [17] * 14
    assert player.civics == [
        "CIVIC_DESPOTISM",
        "CIVIC_BARBARISM",
        "CIVIC_TRIBALISM",
        "CIVIC_DECENTRALIZATION",
        "CIVIC_PAGANISM",
    ]
    assert player.specialist_extra_yield[-1] == [39, 40, 41]
    assert player.improvement_yield_change[-1] == [72, 73, 74]
    assert player.group_cycle == [-1, 8193]
    assert player.research_queue == ["TECH_MYSTICISM"]
    assert player.city_names == ["future city-é😀"]
    assert len(player.cities) == len(player.units) == int(populated)
    if populated:
        assert player.cities[0].name == "city-é😀"
        assert player.units[0].name == "unit-é😀"
        assert player.events_triggered[0].text == "event-é😀"
        assert player.events_occurred[0].data.global_text == "global"
        assert player.event_countdown[0].event == "EVENT_FOREST_FIRE_2"
        assert player.unit_extra_costs[0].cost == -2
        assert player.diplomacy[0].chat_text == "chat-é😀"
    assert [(entry.turn, entry.value) for entry in player.espionage_history] == [
        (-1, 6),
        (10, 106),
    ]
    if flag:
        assert player.triggers_fired == [
            "EVENTTRIGGER_FOREST_FIRE",
            "EVENTTRIGGER_IMPEACHMENT",
        ]
    else:
        assert player.triggers_fired == [True] + [False] * 175
    assert player.pop_rush_hurry_count == -3 and player.inflation_modifier == 17
    if ai:
        assert player.peace_weight == 0 and player.average_commerce_exchange == [
            7,
            8,
            9,
            10,
        ]
        assert player.contact_timer[-1] == [-1] * 14
        assert player.memory_count[-1] == [2] * 33
        assert player.ai_city_sites == [-1, 99]
        assert player.close_borders_attitude_cache == [23] * 19
        assert player._player_ai_end_index == len(data)


@pytest.mark.parametrize(
    "schema,data",
    [
        (CvTeamAI, team_bytes(True)),
        (CvPlayerAI, player_bytes(populated=True, ai=True)),
        (CvCityAI, city_bytes()),
        (CvUnitAI, unit_bytes()),
        (CvSelectionGroupAI, selection_group_bytes()),
        (CvPopupInfo, popup_bytes()),
        (CvDiploParameters, diplo_bytes()),
        (EventTriggeredData, event_bytes()),
    ],
)
def test_truncated_records_fail(schema, data):
    with pytest.raises(StreamError):
        schema.parse(data[:-1])


def test_negative_counts_and_unknown_variable_type_fail():
    # Project counts drive unprefixed art arrays; never accept negative counts.
    data = bytearray(team_bytes())
    project_count_offset = (
        4 + 24 * 4 + 2 + 4 + (19 * 6 + 4 + 4 + 2) * 4 + 19 * 7 + 7 + 2 * 4
    )
    data[project_count_offset : project_count_offset + 4] = ints(-1)
    with pytest.raises(ValidationError, match="project_count"):
        CvTeam.parse(data)
    with pytest.raises(ValidationError, match="revealed_bonuses"):
        CvTeam.parse(team_bytes()[:-12] + ints(-1))
    with pytest.raises(ValidationError, match="python_buttons"):
        CvPopupInfo.parse(
            popup_bytes()[: -(4 + len(wide("button")) + len(narrow("art")))] + ints(-1)
        )
    with pytest.raises(ValidationError):
        FVariable.parse(ints(11))
    with pytest.raises(ValidationError, match="triggers_fired"):
        CvPlayer.parse(player_bytes()[:-20] + ints(-1))


@pytest.mark.parametrize("variable_type", range(9))
def test_diplomacy_numeric_union_retains_all_eight_bytes(variable_type):
    raw = bytes.fromhex("ffffffffaabbccdd")
    argument = parse_record(FVariable, ints(variable_type) + raw)
    assert argument.type == variable_type
    assert argument.value == raw


def test_indexed_failure_has_start_offset():
    stream = BytesIO(b"prefix" + team_bytes(True)[:-1])
    stream.seek(6)
    with pytest.raises(ConstructError, match="team 3 at byte 6"):
        IndexedRecord(CvTeamAI, "team").parse_stream(stream, _index=3)


@pytest.mark.parametrize(
    "filename,teams_end,players_end,cities,units",
    [
        ("bismark-emperor-turn86.CivBeyondSwordSave", 1402436, 2212221, 36, 147),
        ("churchill-random-roll.CivBeyondSwordSave", 967032, 1307798, 7, 52),
        ("mehmed-epic.CivBeyondSwordSave", 2462024, 5014887, 96, 731),
        ("Gandhi-culture-win-t331.CivBeyondSwordSave", 1447586, 3059850, 47, 471),
    ],
)
def test_complete_teams_and_players(filename, teams_end, players_end, cities, units):
    save = SaveFile(Path(__file__).parent / "saves" / filename)
    raw = save.raw
    assert [team.id for team in raw.team_records] == list(range(19))
    assert [player.id for player in raw.player_records] == list(range(19))
    assert raw.team_records[0]._team_start_index == raw._map_end_index
    assert raw._teams_end_index == teams_end
    assert raw.player_records[0]._player_start_index == teams_end
    assert raw._players_end_index == players_end
    statistics_ends = {
        "bismark-emperor-turn86.CivBeyondSwordSave": 2231592,
        "churchill-random-roll.CivBeyondSwordSave": 1325018,
        "mehmed-epic.CivBeyondSwordSave": 5036409,
        "Gandhi-culture-win-t331.CivBeyondSwordSave": 3072768,
    }
    statistics = raw.statistics
    assert statistics._statistics_start_index == players_end
    assert statistics._statistics_end_index == statistics_ends[filename]
    assert [p.id for p in statistics.players] == [
        i for i, p in enumerate(raw.player_records) if p.ever_alive
    ]
    assert statistics.players[-1].id == 18  # barbarian statistics are serialized too
    assert all(
        p._player_record_end_index - p._player_record_start_index == 2151
        for p in statistics.players
    )
    assert raw.footer._footer_start_index == statistics._statistics_end_index
    assert raw.footer.python_data == b"S''\np0\n."
    assert [(s.x, s.y, s.caption) for s in raw.footer.signs] == (
        [(56, 23, "X"), (59, 22, "X"), (59, 11, "X")]
        if filename == "bismark-emperor-turn86.CivBeyondSwordSave"
        else []
    )
    assert len(raw.footer.checksum) == 32
    assert raw.footer._footer_end_index == raw._save_end_index == len(save._raw_bytes)
    expected_player_zero = {
        "bismark-emperor-turn86.CivBeyondSwordSave": (23, 4, 1, 6, 0),
        "churchill-random-roll.CivBeyondSwordSave": (1, 1, 0, 1, 0),
        "mehmed-epic.CivBeyondSwordSave": (126, 93, 29, 10, 1),
        "Gandhi-culture-win-t331.CivBeyondSwordSave": (91, 5, 2, 6, 1),
    }
    player_statistics = statistics.players[0]
    assert (
        sum(player_statistics.units_built),
        sum(player_statistics.units_killed),
        sum(player_statistics.units_lost),
        player_statistics.cities_built,
        player_statistics.golden_ages,
    ) == expected_player_zero[filename]
    assert sum(len(player.cities) for player in raw.player_records) == cities
    assert sum(len(player.units) for player in raw.player_records) == units
    # Existing settings mapping and higher-level Player API must survive.
    assert save.get_player(0).team == raw.teams[0] == 0
    for current, following in zip(raw.team_records, raw.team_records[1:]):
        assert current._team_ai_end_index == following._team_start_index
    for current, following in zip(raw.player_records, raw.player_records[1:]):
        assert current._player_ai_end_index == following._player_start_index
    for player in raw.player_records:
        team = raw.team_records[raw.teams[player.id]]
        assert len(player.cities) <= team.num_cities
        assert player.total_population == sum(city.population for city in player.cities)
        for city in player.cities:
            plot = raw.plots[city.y * raw.grid_width + city.x]
            assert city.owner == player.id == plot.plot_city_owner
            assert city.id == plot.plot_city_id
        assert all(unit.owner == player.id for unit in player.units)
        unit_ids = {unit.id for unit in player.units}
        assert all(
            info.i_id in unit_ids
            for group in player.selection_groups
            for info in group.units
        )
