"""Current player state must not depend on replay text or city names."""

from collections import Counter
from pathlib import Path
from types import SimpleNamespace as Record

import attrs
import pytest

from civ4save import SaveFile
from civ4save.objects import (
    City,
    Civics,
    OrderType,
    Player,
    ProductionOrder,
    Unit,
    get_players,
)
from civ4save.vanilla import enums as e


def city_record(**changes):
    values = {
        "id": 8195,
        "owner": 1,
        "name": "München",
        "x": 3,
        "y": 4,
        "game_turn_founded": 12,
        "game_turn_acquired": 30,
        "population": 7,
        "num_real_building": [1, 0, 1],
        "num_free_building": [0, 1, 1],
        "has_religion": [False, True],
        "has_corporation": [True, False],
        "order_queue": [],
        "commerce_rate": [1250, 2375, 680, 199],
        "base_yield_rate": [10, 7, 15],
        "unit_production": [13, 29],
        "building_production": [31, 47],
        "project_production": [53, 71],
    }
    values.update(changes)
    return Record(**values)


def unit_record(**changes):
    values = {
        "id": 16387,
        "owner": 1,
        "unit_type": 0,
        "x": 3,
        "y": 4,
        "name": "",
        "game_turn_created": 15,
        "group_id": 8198,
        "experience": 11,
        "level": 4,
        "damage": 25,
        "has_promotion": [True, False, True],
    }
    values.update(changes)
    return Record(**values)


def player_record(**changes):
    values = {
        "id": 1,
        "cities": [city_record(), city_record(id=8196, x=5, y=6)],
        "units": [unit_record()],
        "last_state_religion": 1,
        "state_religion_count": 1,
        "civics": [
            "CIVIC_REPRESENTATION",
            "CIVIC_BUREAUCRACY",
            "CIVIC_SLAVERY",
            "CIVIC_FREE_MARKET",
            "CIVIC_FREE_RELIGION",
        ],
        "alive": True,
        "ever_alive": True,
        "total_population": 14,
        "total_land": 85,
        "gold": 123,
        "gold_per_turn": -7,
        "golden_age_turns": 3,
        "anarchy_turns": 2,
        "capital_city_id": 8195,
        "current_era": 2,
        "research_queue": ["TECH_MYSTICISM", "TECH_MEDITATION"],
    }
    values.update(changes)
    return Record(**values)


def root_record(**changes):
    values = {
        # Unused first slot makes confusing record IDs and filtered positions fail.
        "player_records": [Record(id=0), player_record()],
        "leader_names": ["", "Player"],
        "civ_descriptions": ["", "Germany"],
        "civ_short_descriptions": ["", "Germany"],
        "civ_adjectives": ["", "German"],
        "teams": [0, 3],
        "handicaps": ["HANDICAP_NOBLE"] * 2,
        "leaders": ["NO_LEADER", "LEADER_BISMARCK"],
        "civs": ["NO_CIVILIZATION", "CIVILIZATION_GERMANY"],
        "ai_player_score": [0, 100],
        "ai_player_rank": [1, 0],
        "plots": [Record(owner=1), Record(owner=1), Record(owner=-1)],
        "replay_messages": [],
        "deals": [],
        "game_options": [False] * 24,
    }
    values.update(changes)
    return Record(**values)


def test_city_and_unit_conversion():
    city = City.from_struct(city_record())
    assert (city.idx, city.owner, city.name, city.x, city.y) == (
        8195,
        1,
        "München",
        3,
        4,
    )
    assert (city.population, city.turn_founded, city.turn_acquired) == (7, 12, 30)
    assert city.buildings == [e.BuildingType(i) for i in range(3)]
    assert city.religions == [e.ReligionType(1)]
    assert city.corporations == [e.CorporationType(0)]
    assert city.wonders == []
    assert City("Old constructor", 1, 2, 3, ["Stonehenge"]).wonders == ["Stonehenge"]

    unit = Unit.from_struct(unit_record())
    assert (unit.idx, unit.owner, unit.unit_type) == (16387, 1, e.UnitType(0))
    assert (unit.x, unit.y, unit.name, unit.turn_created) == (3, 4, "", 15)
    assert (unit.group_id, unit.experience, unit.level, unit.damage) == (
        8198,
        11,
        4,
        25,
    )
    assert unit.promotions == [e.PromotionType(0), e.PromotionType(2)]


def test_city_production_queue_and_fractional_rates():
    raw = city_record(
        order_queue=[
            Record(order_type=0, data1=1, data2=2, save=True),
            Record(order_type=1, data1=1, data2=-99, save=False),
            Record(order_type=2, data1=1, data2=-99, save=False),
            Record(order_type=3, data1=0, data2=-99, save=False),
            Record(order_type=0, data1=1, data2=-1, save=False),
        ]
    )
    city = City.from_struct(raw)
    assert city.production_queue == [
        ProductionOrder(
            OrderType.ORDER_TRAIN, e.UnitType(1), True, 29, e.UnitAIType(2)
        ),
        ProductionOrder(OrderType.ORDER_CONSTRUCT, e.BuildingType(1), False, 47),
        ProductionOrder(OrderType.ORDER_CREATE, e.ProjectType(1), False, 71),
        ProductionOrder(
            OrderType.ORDER_MAINTAIN, e.ProcessType.PROCESS_WEALTH, False, None
        ),
        ProductionOrder(
            OrderType.ORDER_TRAIN, e.UnitType(1), False, 29, e.UnitAIType.NO_UNIT_A_I
        ),
    ]
    assert city.current_production is city.production_queue[0]
    assert [type(order.item) for order in city.production_queue] == [
        e.UnitType,
        e.BuildingType,
        e.ProjectType,
        e.ProcessType,
        e.UnitType,
    ]
    assert city.base_production_per_turn == 7
    assert city.gold_per_turn == 12.5
    assert city.science_per_turn == 23.75
    assert city.culture_per_turn == 6.8
    assert city.espionage_per_turn == 1.99
    # The model must not mutate raw arrays or retain a live view of queue records.
    raw.order_queue[0].data1 = 0
    raw.unit_production[1] = 999
    assert city.current_production.item == e.UnitType(1)
    assert city.current_production.invested_production == 29


def test_empty_city_queue_and_zero_output():
    city = City.from_struct(city_record(commerce_rate=[0] * 4, base_yield_rate=[0] * 3))
    assert city.current_production is None
    assert city.production_queue == []
    assert city.base_production_per_turn == 0
    assert city.gold_per_turn == city.science_per_turn == 0
    assert city.culture_per_turn == city.espionage_per_turn == 0


@pytest.mark.parametrize("enabled", [False, True])
def test_no_espionage_converts_output_to_culture(enabled):
    raw = root_record()
    raw.game_options[e.GameOptionType.GAMEOPTION_NO_ESPIONAGE] = enabled
    city = get_players(raw)[1].cities[0]
    assert city.gold_per_turn == 12.5
    assert city.science_per_turn == 23.75
    assert city.culture_per_turn == (8.79 if enabled else 6.8)
    assert city.espionage_per_turn == (0 if enabled else 1.99)
    assert raw.player_records[1].cities[0].commerce_rate == [1250, 2375, 680, 199]


@pytest.mark.parametrize(
    "order_type,item_id",
    [(-1, 0), (4, 0), (0, -1), (1, -1), (2, -1), (3, -1), (0, 99999)],
)
def test_invalid_production_order_rejected(order_type, item_id):
    raw = city_record(
        order_queue=[
            Record(
                order_type=order_type,
                data1=item_id,
                data2=-1,
                save=False,
            )
        ]
    )
    with pytest.raises(ValueError):
        City.from_struct(raw)


@pytest.mark.parametrize("religion_count", [0, 1, 2])
def test_player_current_state(religion_count):
    raw = root_record()
    raw.player_records[1].state_religion_count = religion_count
    players = get_players(raw)
    assert set(players) == {1}
    player = players[1]
    assert (player.idx, player.team, player.name, player.score, player.rank) == (
        1,
        3,
        "Player",
        100,
        0,
    )
    assert player.leader == e.LeaderHeadType.LEADER_BISMARCK
    assert player.civ == e.CivilizationType.CIVILIZATION_GERMANY
    assert player.handicap == e.HandicapType.HANDICAP_NOBLE
    assert player.alive and player.ever_alive
    assert (player.population, player.land, player.owned_plots) == (14, 85, 2)
    assert (player.gold, player.gold_per_turn) == (123, -7)
    assert (player.golden_age_turns, player.anarchy_turns) == (3, 2)
    assert player.capital_city_id == 8195
    assert player.capital_city is player.cities[0]
    assert player.current_era == e.EraType(2)
    assert player.last_state_religion == e.ReligionType(1)
    assert player.religion == (
        e.ReligionType(1) if religion_count else e.ReligionType.NO_RELIGION
    )
    assert player.civics == Civics(
        e.CivicType.CIVIC_REPRESENTATION,
        e.CivicType.CIVIC_BUREAUCRACY,
        e.CivicType.CIVIC_SLAVERY,
        e.CivicType.CIVIC_FREE_MARKET,
        e.CivicType.CIVIC_FREE_RELIGION,
    )
    assert player.research_queue == [
        e.TechType.TECH_MYSTICISM,
        e.TechType.TECH_MEDITATION,
    ]
    assert [city.idx for city in player.cities] == [8195, 8196]
    assert player.cities[0].name == player.cities[1].name
    assert len(player.units) == 1
    raw.player_records[1].research_queue.clear()
    raw.player_records[1].units[0].has_promotion[0] = False
    assert len(player.research_queue) == 2
    assert player.units[0].promotions[0] == e.PromotionType(0)


def test_replay_text_cannot_override_current_state():
    raw = root_record()
    expected = get_players(raw)
    raw.replay_messages = [
        Record(type=kind, player=player, text=text, plot_x=3, plot_y=4, turn=20)
        for kind, player, text in [
            ("CITY_FOUNDED", 1, "München is founded"),
            ("CITY_FOUNDED", 1, "München is founded"),
            ("MAJOR_EVENT", 1, "Unknown was captured"),
            ("MAJOR_EVENT", 1, "Unknown is razed"),
            ("MAJOR_EVENT", 1, "Unknown revolts and joins the Missing Empire!"),
            ("MAJOR_EVENT", 1, "adopts unknown civic"),
            ("MAJOR_EVENT", 1, "converts to unknown religion"),
            ("MAJOR_EVENT", 1, "Eine Stadt wurde gegründet"),
            ("MAJOR_EVENT", 99, "Unknown completes Stonehenge"),
            ("PLOT_OWNER_CHANGE", -1, ""),
        ]
    ]
    assert get_players(raw) == expected


def test_replay_history_survives_capture_but_not_city_replacement():
    raw = root_record()
    raw.civs[0] = "CIVILIZATION_ENGLAND"
    raw.leaders[0] = "LEADER_CHURCHILL"
    raw.player_records[0] = player_record(
        id=0, alive=False, cities=[], units=[], total_population=0
    )
    raw.replay_messages = [
        Record(
            type="MAJOR_EVENT", player=owner, text=text, plot_x=x, plot_y=y, turn=turn
        )
        for owner, text, x, y, turn in [
            (0, "Old city completes Old wonder", 3, 4, 5),
            (0, "Old name completes Stonehenge", 3, 4, 20),
            (1, "Player completes Apollo Program", -1, -1, 40),
            (1, "Artist has been born in a city", -1, -1, 41),
        ]
    ]
    player = get_players(raw)[1]
    assert player.cities[0].wonders == ["Stonehenge"]
    assert player.projects == ["Apollo Program"]
    assert player.great_people == ["Artist"]


@pytest.mark.parametrize("capital_id", [-1, 65543])
def test_eliminated_player_has_empty_current_holdings(capital_id):
    raw = root_record(
        player_records=[
            Record(id=0),
            player_record(
                alive=False,
                cities=[],
                units=[],
                capital_city_id=capital_id,
                total_population=0,
                total_land=0,
                research_queue=[],
            ),
        ],
        plots=[],
    )
    player = get_players(raw)[1]
    assert not player.alive and player.ever_alive
    assert player.cities == player.units == player.research_queue == []
    assert player.capital_city_id == capital_id
    assert player.capital_city is None
    assert player.owned_plots == player.population == player.land == 0


def test_cities_do_not_imply_a_capital():
    # Barbarian players can own cities without having a capital.
    raw = root_record()
    raw.player_records[1].capital_city_id = -1
    player = get_players(raw)[1]
    assert player.cities
    assert player.capital_city is None


@pytest.mark.parametrize(
    "filename",
    [
        "bismark-emperor-turn86.CivBeyondSwordSave",
        "churchill-random-roll.CivBeyondSwordSave",
        "mehmed-epic.CivBeyondSwordSave",
        "Gandhi-culture-win-t331.CivBeyondSwordSave",
    ],
)
def test_players_reconcile_with_serialized_holdings(filename):
    save = SaveFile(Path(__file__).parent / "saves" / filename)
    players = save.players
    assert save.players is players
    owned = Counter(plot.owner for plot in save.raw.plots)
    assert (
        sum(len(player.cities) for player in players.values()) == save.raw.total_cities
    )
    for idx, player in players.items():
        assert isinstance(player, Player)
        record = save.raw.player_records[idx]
        assert player.population == record.total_population
        assert sum(city.population for city in player.cities) == player.population
        assert player.owned_plots == owned[idx]
        assert player.gold == record.gold
        assert player.alive == record.alive
        assert {(city.owner, city.idx) for city in player.cities} == {
            (idx, city.id) for city in record.cities
        }
        assert {(unit.owner, unit.idx) for unit in player.units} == {
            (idx, unit.id) for unit in record.units
        }
        for city, city_raw in zip(player.cities, record.cities):
            assert len(city.production_queue) == len(city_raw.order_queue)
            assert city.base_production_per_turn == city_raw.base_yield_rate[1]
            assert city.gold_per_turn == city_raw.commerce_rate[0] / 100
            assert city.science_per_turn == city_raw.commerce_rate[1] / 100
            no_espionage = save.raw.game_options[
                e.GameOptionType.GAMEOPTION_NO_ESPIONAGE
            ]
            assert (
                city.culture_per_turn
                == (
                    city_raw.commerce_rate[2]
                    + (city_raw.commerce_rate[3] if no_espionage else 0)
                )
                / 100
            )
            for order, order_raw in zip(city.production_queue, city_raw.order_queue):
                assert order.item.value == order_raw.data1
                assert order.order_type.value == order_raw.order_type
                assert order.repeat == order_raw.save
        assert player.team in save.teams
        assert player.capital_city_id == record.capital_city_id
        if player.alive and player.capital_city_id != -1:
            assert player.capital_city is not None
            assert player.capital_city.owner == idx
        else:
            assert player.capital_city is None
        assert list(attrs.asdict(player.civics).values()) == [
            e.CivicType[str(civic)] for civic in record.civics
        ]
