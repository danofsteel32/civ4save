"""Independently packed settings/game sections and their composition."""

from struct import pack

import pytest
from construct import ConstructError, StreamError, ValidationError

from civ4save.vanilla import enums as e
from civ4save.vanilla import structure as s
from tests.binary_helpers import free_list, ints, map_bytes, narrow, parse_record, wide
from tests.test_teams_players import player_bytes, team_bytes


def init_core_bytes():
    data = ints(1, 0) + b"".join(map(wide, ["Game 😀", "secret", "admin", "Map.py"]))
    data += b"\x01" + ints(2, 1, 1, 0, 2, 0, 0)
    data += ints(2, 1, -1, 7, 7) + bytes([1, 0, 1, 0, 1, 0, 1])
    data += bytes([1, 0] * 12) + bytes([0, 1, 0, 1, 0]) + b"\x01"
    data += ints(86, 500, 3, 100, 0, 10)
    for field in ["leader", "description", "short", "adjective", "password"]:
        data += b"".join(wide(f"{field}-{i}é") for i in range(19))
    data += b"".join(narrow(f"player-{i}@example.test") for i in range(19))
    data += b"".join(narrow(f"smtp-{i}.example.test") for i in range(19))
    data += bytes([1, 0] * 9 + [1])
    data += b"".join(wide(f"flag-{i}") for i in range(19))
    data += ints(*([0] * 19)) * 2  # civs, leaders
    data += ints(*range(19))  # teams
    data += ints(*([0] * 19)) * 5  # handicap, color, art style, status, claim
    data += bytes([1] * 19) + bytes([0] * 19)
    return data


def game_bytes():
    data = ints(1, *range(1, 23)) + bytes([1, 0, 1, 0, 1])
    data += ints(4, -1, -1, -1, -1, 0) + narrow("script-é")
    for row in range(6):
        data += ints(*range(row * 100, row * 100 + 19))
    # XML table sizes for vanilla BTS, in CvGame::write order.
    for row, count in enumerate([123, 89, 125, 11, 25, 22, 7, 7, 2, 2, 2]):
        data += ints(*range(row * 1000, row * 1000 + count))
    data += bytes([1, 0, 1]) + bytes([0, 1, 0, 1]) + bytes([1, 0, 1, 0, 1, 0, 1])
    data += ints(*([-1, -1] * 7))
    data += b"".join(ints(i, 8192 + i) for i in range(7))
    data += ints(2) + wide("Destroyed 😀") + wide("") + ints(1) + wide("Artist-é")
    data += free_list([]) * 3
    data += pack("<2I", 0xFFFFFFFF, 0x80000000)
    data += ints(1, 86, 0, -1, -1, 0) + wide("Replay 😀") + ints(2)
    data += ints(2)  # sessions
    data += ints(1, 2, 3, -1, 4, 5)  # one extra yield
    data += ints(1, 2, 3, -8)  # one extra cost, a scalar
    data += ints(1, 1, 2)  # one vote source/religion pair
    data += ints(2, 0, 1)  # two inactive event triggers
    data += ints(1, 0, *([-1] * 158))  # shrine count and 159 building IDs
    data += ints(2, *([-1] * 158))  # 159 religion IDs, not building IDs
    data += ints(3, 5)
    return data


def test_header_wire_layout():
    raw = parse_record(s.SaveHeader, ints(302, *range(8), 1499))
    assert raw.version == 302
    assert raw._save_bits == list(range(8))
    assert raw._bytes_to_zlib_magic_number == 1499
    assert (raw._header_start_index, raw._header_end_index) == (0, 40)
    framing = parse_record(s.CompressedSectionHeader, ints(0, 65536))
    assert framing._compression_flag == 0
    assert framing._first_chunk_size == 65536


def test_init_core_player_strings_and_settings():
    data = init_core_bytes()
    raw = parse_record(s.CvInitCore, data)
    assert (raw.game_type, raw.game_name) == ("GAME_SP_NEW", "Game 😀")
    assert (raw.game_password, raw.admin_password, raw.map_script_name) == (
        "secret",
        "admin",
        "Map.py",
    )
    assert raw.wb_map_no_players is True
    assert [
        raw.world_size,
        raw.climate,
        raw.sea_level,
        raw.start_era,
        raw.game_speed,
        raw.turn_timer,
        raw.calendar,
    ] == [
        "WORLDSIZE_SMALL",
        "CLIMATE_TROPICAL",
        "SEALEVEL_MEDIUM",
        "ERA_ANCIENT",
        "GAMESPEED_NORMAL",
        "TURNTIMER_STATIC",
        "CALENDAR_DEFAULT",
    ]
    assert raw.custom_map_options == [-1, 7]
    assert raw.num_hidden_custom_map_options == 1
    assert list(raw.victories.values()) == [True, False, True, False, True, False, True]
    assert list(raw.game_options.values()) == [True, False] * 12
    assert list(raw.mp_game_options.values()) == [False, True, False, True, False]
    assert raw.stat_reporting is True
    assert [
        raw.game_turn,
        raw.max_turns,
        raw.pitboss_turn_time,
        raw.target_score,
        raw.max_city_eliminations,
        raw.advanced_start_points,
    ] == [86, 500, 3, 100, 0, 10]
    for field, label in [
        ("leader_names", "leader"),
        ("civ_descriptions", "description"),
        ("civ_short_descriptions", "short"),
        ("civ_adjectives", "adjective"),
        ("civ_passwords", "password"),
    ]:
        assert raw[field] == [f"{label}-{i}é" for i in range(19)]
    assert raw.emails == [f"player-{i}@example.test" for i in range(19)]
    assert raw.smtp_hosts == [f"smtp-{i}.example.test" for i in range(19)]
    assert raw.white_flags == [True, False] * 9 + [True]
    assert raw.flag_decals == [f"flag-{i}" for i in range(19)]
    assert raw.civs == [e.CivilizationType(0).name] * 19
    assert raw.leaders == [e.LeaderHeadType(0).name] * 19
    assert raw.teams == list(range(19))
    assert raw.handicaps == [e.HandicapType(0).name] * 19
    assert raw.colors == [e.PlayerColorType(0).name] * 19
    assert raw.art_style == [e.UnitArtStyleType(0).name] * 19
    assert raw.slot_statuses == raw.slot_claims == [0] * 19
    assert raw.playable_civs == [True] * 19
    assert raw.minor_nation_civs == [False] * 19
    assert (raw._init_core_start_index, raw._init_core_end_index) == (0, len(data))


def test_game_scalars_arrays_and_nested_records():
    data = game_bytes()
    raw = parse_record(s.CvGame, data)
    for value, field in enumerate(
        [
            "elapsed_game_turns",
            "start_turn",
            "start_year",
            "estimated_end_turn",
            "turn_slice",
            "cutoff_slice",
            "num_game_turn_active",
            "total_cities",
            "total_population",
            "trade_routes",
            "free_trade_count",
            "no_nukes_count",
            "nukes_exploded",
            "max_population",
            "max_land",
            "max_tech",
            "max_wonders",
            "init_population",
            "init_land",
            "init_tech",
            "init_wonders",
            "ai_autoplay",
        ],
        start=1,
    ):
        assert raw[field] == value
    assert [
        raw.score_dirty,
        raw.circumnavigated,
        raw.final_initialized,
        raw.hot_pbem_between_turns,
        raw.nukes_valid,
    ] == [True, False, True, False, True]
    assert raw.handicap == e.HandicapType(4).name
    assert (
        raw.pause_player,
        raw.best_land_unit,
        raw.winner,
        raw.victory,
        raw.game_state,
    ) == (
        -1,
        "NO_UNIT",
        -1,
        "NO_VICTORY",
        "GAMESTATE_ON",
    )
    assert raw.script_data.string == "script-é"
    for row, field in enumerate(
        [
            "ai_rank_player",
            "ai_player_rank",
            "ai_player_score",
            "ai_rank_team",
            "ai_team_rank",
            "ai_team_score",
        ]
    ):
        assert raw[field] == list(range(row * 100, row * 100 + 19))
    for row, (field, enum, count) in enumerate(
        [
            ("unit_created_counts", e.UnitType, 123),
            ("unit_class_created_counts", e.UnitClassType, 89),
            ("building_class_created_counts", e.BuildingClassType, 125),
            ("project_created_counts", e.ProjectType, 11),
            ("force_civic_counts", e.CivicType, 25),
            ("vote_outcomes", e.VoteType, 22),
            ("religion_game_turn_founded", e.ReligionType, 7),
            ("corporation_game_turn_founded", e.CorporationType, 7),
            ("secretary_general_timer", e.VoteSourceType, 2),
            ("vote_timer", e.VoteSourceType, 2),
            ("diplo_vote", e.VoteSourceType, 2),
        ]
    ):
        assert raw[field] == {enum(i): row * 1000 + i for i in range(count)}
    assert raw.special_unit_valid == [True, False, True]
    assert raw.special_building_valid == [False, True, False, True]
    assert list(raw.religion_slot_taken.values()) == [
        True,
        False,
        True,
        False,
        True,
        False,
        True,
    ]
    assert [(city.owner, city.i_id) for city in raw.holy_cities] == [(-1, -1)] * 7
    assert [(city.owner, city.i_id) for city in raw.corporation_headquarters] == [
        (i, 8192 + i) for i in range(7)
    ]
    assert raw.cities_destroyed == ["Destroyed 😀", ""]
    assert raw.great_people_born == ["Artist-é"]
    assert raw.deals == raw.vote_selections == raw.votes_triggered == []
    assert (raw.map_random_seed, raw.soren_random_seed) == (0xFFFFFFFF, 0x80000000)
    assert raw.replay_messages[0].text == "Replay 😀"
    assert raw.num_sessions == 2
    assert raw.plot_extra_yields[0].extra_yields == [-1, 4, 5]
    assert raw.plot_extra_costs[0].extra_costs == -8
    assert raw.vote_source_religions[0].religion == e.ReligionType(2).name
    assert raw.inactive_triggers == [e.EventTriggerType(i).name for i in range(2)]
    assert raw.shrine_building_count == 1
    assert raw.shrine_buildings == [e.BuildingType(0).name] + ["NO_BUILDING"] * 158
    assert raw.shrine_religion == [e.ReligionType(2).name] + ["NO_RELIGION"] * 158
    assert (raw.num_culture_victory_cities, raw.culture_victory_level) == (
        3,
        e.CultureLevelType(5).name,
    )
    assert (raw._game_start_index, raw._game_end_index) == (0, len(data))


def test_sections_compose_into_flat_raw_fields():
    header = ints(302, *range(8), 1499)
    settings = init_core_bytes()
    framing = ints(0, 65536)
    game = game_bytes() + ints(0, 17)  # CvGameAI flag and pad follow CvGame.
    map_data = map_bytes([], width=0, height=0)
    teams = team_bytes(ai=True) * 19
    players = player_bytes(ai=True) * 19
    raw = parse_record(
        s.CivBeyondSwordSave,
        header + settings + framing + game + map_data + teams + players,
    )
    assert raw.version == 302
    assert raw.game_name == "Game 😀"
    assert raw.civ_passwords[0] == "password-0é"
    assert raw.plot_extra_costs[0].extra_costs == -8
    assert (raw._game_ai_flag, raw._game_ai_pad) == (0, 17)
    assert raw.grid_width == raw.grid_height == 0
    assert raw._header_end_index == raw._init_core_start_index
    assert raw._init_core_end_index == raw._compressed_section_start_index
    assert raw._compressed_section_end_index == raw._game_start_index
    assert raw._game_end_index + 8 == raw._game_ai_end_index == raw._map_start_index
    assert raw._map_end_index == len(header + settings + framing + game + map_data)
    assert raw.teams == list(range(19))  # settings assignments stay intact
    assert len(raw.team_records) == len(raw.player_records) == 19
    assert raw._teams_end_index == raw._map_end_index + len(teams)
    assert raw._players_end_index == raw._teams_end_index + len(players)
    prefix = header + settings + framing + game + map_data
    with pytest.raises(ConstructError, match="team 18 at byte"):
        s.CivBeyondSwordSave.parse(prefix + teams[:-1])
    with pytest.raises(ConstructError, match="player 18 at byte"):
        s.CivBeyondSwordSave.parse(prefix + teams + players[:-1])


@pytest.mark.parametrize(
    "schema,data",
    [
        (s.SaveHeader, ints(302, *range(8), 1499)),
        (s.CompressedSectionHeader, ints(0, 65536)),
        (s.CvInitCore, init_core_bytes()),
        (s.CvGame, game_bytes()),
    ],
)
def test_truncated_sections(schema, data):
    with pytest.raises(StreamError):
        schema.parse(data[:-1])


def test_negative_custom_map_option_count():
    data = ints(1, 0) + wide("") * 4 + b"\0" + ints(*([0] * 7)) + ints(-1)
    with pytest.raises(ValidationError, match="num_custom_map_options"):
        s.CvInitCore.parse(data)
