"""Classes and functions for dealing with players."""

from __future__ import annotations

from collections import Counter
from typing import Any

import attrs

from civ4save.vanilla import enums as e

from .production import ProductionOrder
from .unit import Unit


@attrs.define(slots=True)
class City:
    """Current city state, identified by (owner, idx).

    Wonders retains replay-derived completion names; buildings is the current
    serialized inventory, including free buildings and obsolete buildings.
    """

    name: str
    x: int
    y: int
    turn_founded: int
    wonders: list[str] = attrs.field(factory=list)
    idx: int = -1
    owner: int = -1
    population: int = 0
    turn_acquired: int = -1
    buildings: list[e.BuildingType] = attrs.field(factory=list)
    religions: list[e.ReligionType] = attrs.field(factory=list)
    corporations: list[e.CorporationType] = attrs.field(factory=list)
    production_queue: list[ProductionOrder] = attrs.field(factory=list)
    base_production_per_turn: int = 0
    gold_per_turn: float = 0.0
    science_per_turn: float = 0.0
    culture_per_turn: float = 0.0
    espionage_per_turn: float = 0.0

    @property
    def current_production(self) -> ProductionOrder | None:
        """Return the first queued order, or None for an empty queue."""
        return self.production_queue[0] if self.production_queue else None

    @classmethod
    def from_struct(cls, data: Any, *, no_espionage: bool = False) -> City:
        """Create a city from a parsed CvCity or CvCityAI record.

        Commerce rates are saved in hundredths. With No Espionage, the SDK
        adds espionage to culture instead. Base production excludes modifiers,
        overflow, chops and food converted while producing workers/settlers.
        Gold is city output before subtracting expenses, not net income.
        """
        gold, science, culture, espionage = data.commerce_rate
        if no_espionage:
            culture += espionage
            espionage = 0
        return cls(
            name=data.name,
            x=data.x,
            y=data.y,
            turn_founded=data.game_turn_founded,
            idx=data.id,
            owner=data.owner,
            population=data.population,
            turn_acquired=data.game_turn_acquired,
            buildings=[
                e.BuildingType(i)
                for i, count in enumerate(data.num_real_building)
                if count + data.num_free_building[i] > 0
            ],
            religions=[
                e.ReligionType(i)
                for i, present in enumerate(data.has_religion)
                if present
            ],
            corporations=[
                e.CorporationType(i)
                for i, present in enumerate(data.has_corporation)
                if present
            ],
            production_queue=[
                ProductionOrder.from_struct(order, data) for order in data.order_queue
            ],
            base_production_per_turn=data.base_yield_rate[e.YieldType.YIELD_PRODUCTION],
            gold_per_turn=gold / 100,
            science_per_turn=science / 100,
            culture_per_turn=culture / 100,
            espionage_per_turn=espionage / 100,
        )


@attrs.define(slots=True)
class Civics:
    """Maps to a players Civics. Initialized with default Civics."""

    government: e.CivicType = e.CivicType.CIVIC_DESPOTISM
    legal: e.CivicType = e.CivicType.CIVIC_BARBARISM
    labor: e.CivicType = e.CivicType.CIVIC_TRIBALISM
    economy: e.CivicType = e.CivicType.CIVIC_DECENTRALIZATION
    religion: e.CivicType = e.CivicType.CIVIC_PAGANISM

    @classmethod
    def from_struct(cls, data: Any) -> Civics:
        """Read the five vanilla civic options in their serialized order."""
        return cls(*(e.CivicType[str(civic)] for civic in data))


@attrs.define(slots=True)
class Trade:
    """Can be an item like TRADE_OPEN_BORDERS or Bonus like BONUS_COW."""

    item: e.TradeableItem | e.BonusType
    amount: int


@attrs.define(slots=True)
class TradeDeal:
    """Represent a trade deal between players."""

    first_player: int
    second_player: int
    initial_turn: int
    first_trades: list[Trade]
    second_trades: list[Trade]


@attrs.define(slots=True)
class Player:
    """Current player state with replay-derived great-person/project history.

    Gold per turn is net diplomatic payments, not total treasury income.
    """

    idx: int
    name: str
    desc: str
    short_desc: str
    adjective: str
    team: int
    handicap: e.HandicapType
    leader: e.LeaderHeadType
    civ: e.CivilizationType
    score: int
    rank: int
    owned_plots: int = 0
    great_people: list[str] = attrs.field(factory=list)
    cities: list[City] = attrs.field(factory=list)
    religion: e.ReligionType = e.ReligionType.NO_RELIGION
    civics: Civics = attrs.field(factory=Civics)
    trades: list[TradeDeal] = attrs.field(factory=list)
    projects: list[str] = attrs.field(factory=list)
    alive: bool = False
    ever_alive: bool = False
    population: int = 0
    land: int = 0
    gold: int = 0
    gold_per_turn: int = 0
    golden_age_turns: int = 0
    anarchy_turns: int = 0
    capital_city_id: int = -1
    current_era: e.EraType = e.EraType.NO_ERA
    last_state_religion: e.ReligionType = e.ReligionType.NO_RELIGION
    research_queue: list[e.TechType] = attrs.field(factory=list)
    units: list[Unit] = attrs.field(factory=list)

    @classmethod
    def from_struct(cls, data: Any, settings: Any) -> Player:
        """Combine a CvPlayer record with identity/score fields from the root."""
        idx = data.id
        return cls(
            idx=idx,
            name=settings.leader_names[idx],
            desc=settings.civ_descriptions[idx],
            short_desc=settings.civ_short_descriptions[idx],
            adjective=settings.civ_adjectives[idx],
            team=settings.teams[idx],
            handicap=e.HandicapType[str(settings.handicaps[idx])],
            leader=e.LeaderHeadType[str(settings.leaders[idx])],
            civ=e.CivilizationType[str(settings.civs[idx])],
            score=settings.ai_player_score[idx],
            rank=settings.ai_player_rank[idx],
            cities=[
                City.from_struct(
                    city,
                    no_espionage=settings.game_options[
                        e.GameOptionType.GAMEOPTION_NO_ESPIONAGE
                    ],
                )
                for city in data.cities
            ],
            religion=(
                e.ReligionType(data.last_state_religion)
                if data.state_religion_count > 0
                else e.ReligionType.NO_RELIGION
            ),
            civics=Civics.from_struct(data.civics),
            alive=data.alive,
            ever_alive=data.ever_alive,
            population=data.total_population,
            land=data.total_land,
            gold=data.gold,
            gold_per_turn=data.gold_per_turn,
            golden_age_turns=data.golden_age_turns,
            anarchy_turns=data.anarchy_turns,
            capital_city_id=data.capital_city_id,
            current_era=e.EraType(data.current_era),
            last_state_religion=e.ReligionType(data.last_state_religion),
            research_queue=[e.TechType[str(tech)] for tech in data.research_queue],
            units=[Unit.from_struct(unit) for unit in data.units],
        )

    def adopt_civic(self, new_civic: e.CivicType) -> None:
        """Correctly set the new civic."""
        v = new_civic.value
        if v < 5:
            self.civics.government = new_civic
        elif v >= 5 and v < 10:
            self.civics.legal = new_civic
        elif v >= 10 and v < 15:
            self.civics.labor = new_civic
        elif v >= 15 and v < 20:
            self.civics.economy = new_civic
        elif v >= 20:
            self.civics.religion = new_civic

    @property
    def capital_city(self) -> City | None:
        """Resolve the saved capital ID, returning None for absent/stale IDs.

        Eliminated players can retain an ID for a city they no longer own.
        """
        return next(
            (city for city in self.cities if city.idx == self.capital_city_id), None
        )

    def pop_city(self, city_name: str) -> City:
        """Remove `City` with `city_name` from cities List and return it."""
        for n, city in enumerate(self.cities):
            if city.name == city_name:
                return self.cities.pop(n)
        raise ValueError(f"player {self.idx} has no city named {city_name}")

    def city_from_xy(self, x: int, y: int) -> City:
        """Return city from cities List at given coordinates (x,y)."""
        for city in self.cities:
            if (city.x, city.y) == (x, y):
                return city
        raise ValueError(f"player {self.idx} has no city @ ({x}, {y})")


PlayerDict = dict[int, Player]


def _set_player_trade_deals(deals: list, players: PlayerDict) -> PlayerDict:
    for deal in deals:
        trade_deal = TradeDeal(
            deal["first_player"],
            deal["second_player"],
            deal["initial_game_turn"],
            deal["first_trades"],
            deal["second_trades"],
        )
        players[deal["first_player"]].trades.append(trade_deal)
    return players


def _set_player_history(replay_messages: list, players: PlayerDict) -> None:
    """Retain legacy English replay histories without reconstructing current state.

    City completions are associated by coordinates and lifetime, never by name.
    These strings are historical hints, not an authoritative building inventory.
    """
    cities = {
        (city.x, city.y): city for player in players.values() for city in player.cities
    }
    for msg in replay_messages:
        if msg.type != "MAJOR_EVENT" or msg.player not in players:
            continue
        player = players[msg.player]
        if " completes " in msg.text:
            name = msg.text.split(" completes ", 1)[1]
            if (msg.plot_x, msg.plot_y) == (-1, -1):
                player.projects.append(name)
            else:
                city = cities.get((msg.plot_x, msg.plot_y))
                if city is not None and msg.turn >= city.turn_founded:
                    city.wonders.append(name)
        elif " has been born" in msg.text:
            player.great_people.append(msg.text.split(" has been born", 1)[0])


def get_players(data: Any) -> PlayerDict:
    """Return configured civilizations, including eliminated players.

    Identity and scores come from the root, current state from CvPlayer/CvCity/
    CvUnit, and owned plot counts from CvPlot. Unused NO_CIVILIZATION slots are
    omitted, preserving the existing player membership policy.
    """
    players = {
        record.id: Player.from_struct(record, data)
        for record in data.player_records
        if data.civs[record.id] != "NO_CIVILIZATION"
    }
    owned_plots = Counter(plot.owner for plot in data.plots if plot.owner >= 0)
    for idx, player in players.items():
        player.owned_plots = owned_plots[idx]
    _set_player_history(data.replay_messages, players)
    return _set_player_trade_deals(data.deals, players)
