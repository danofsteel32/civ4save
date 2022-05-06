"""
organize.py

A rough
"""
from dataclasses import dataclass, field, asdict
import re

from . import cv_enums as cv


# TODO: Add NO_PLAYER to players dict {-1: {idx: -1, name: NO_PLAYER}}


@dataclass
class City:
    name: str
    x: int
    y: int
    turn_founded: int
    wonders: list[str] = field(default_factory=list)


@dataclass
class Civics:
    government: cv.CivicType = cv.CivicType.CIVIC_DESPOTISM
    legal: cv.CivicType = cv.CivicType.CIVIC_BARBARISM
    labor: cv.CivicType = cv.CivicType.CIVIC_TRIBALISM
    economy: cv.CivicType = cv.CivicType.CIVIC_DECENTRALIZATION
    religion: cv.CivicType = cv.CivicType.CIVIC_PAGANISM


@dataclass
class Trade:
    item: str
    amount: int


@dataclass
class TradeDeal:
    first_player: int
    second_player: int
    initial_turn: int
    first_trades: list[Trade]
    second_trades: list[Trade]


@dataclass
class Player:
    idx: int
    name: str
    desc: str
    short_desc: str
    adjective: str
    team: int
    handicap: cv.HandicapType
    leader: cv.LeaderHeadType
    civ: cv.CivilizationType
    score: int
    owned_plots: int = 0
    great_people: list[str] = field(default_factory=list)
    cities: list[City] = field(default_factory=list)
    religion: cv.ReligionType = cv.ReligionType.NO_RELIGION
    civics: Civics = field(default_factory=Civics)
    trades: list[TradeDeal] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)

    def adopt_civic(self, new_civic: cv.CivicType):
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

    def pop_city(self, city_name: str):
        for n, city in enumerate(self.cities):
            if city.name == city_name:
                return self.cities.pop(n)
        raise ValueError(f'player {self.idx} has no city named {city_name}')

    def city_from_xy(self, x: int, y: int):
        for city in self.cities:
            if (city.x, city.y) == (x, y):
                return city
        raise ValueError(f'player {self.idx} has no city @ ({x}, {y})')


@dataclass
class GameSettings:
    name: str
    type: str
    speed: str
    map_script: str
    world_size: cv.WorldSizeType
    climate: cv.ClimateType
    sea_level: cv.SeaLevelType
    start_turn: int
    start_year: int
    start_era: str
    options: list
    mp_options: list
    map_random_seed: int
    soren_random_seed: int
    grid_width: int
    grid_height: int
    wrap_x: bool
    wrap_y: bool
    land_plots: int
    culture_victory_level: str
    culture_victory_cities: int
    victories_enabled: list


@dataclass
class GameState:
    state: cv.GameStateType
    turn: int
    victory: cv.VictoryType
    winner: int
    owned_plots: int
    circumnavigated: bool
    nukes_buildable: bool
    total_cities: int
    total_population: int
    # total created not total currently existing
    total_units: list
    total_buildings: list


@dataclass
class Plot:
    x: int
    y: int
    starting_plot: bool
    irrigated: bool
    yields: list[int]
    owner_idx: int
    plot_type: cv.PlotType
    terrain_type: cv.TerrainType
    feature_type: cv.FeatureType
    bonus_type: cv.BonusType
    improvement_type: cv.ImprovementType


def init_plots(data) -> list[Plot]:
    plots = []
    for p in data['plots']:
        plots.append(
            Plot(
                p.x,
                p.y,
                p.starting_plot,
                p.irrigated,
                p.yields,
                p.owner,
                p.plot_type,
                p.terrain_type,
                p.feature_type,
                p.bonus_type,
                p.improvement_type
            )
        )
    return plots


def init_game_state(data) -> GameState:

    total_units = []
    for n, count in enumerate(data.unit_created_counts):
        unit = cv.UnitType(n)
        if count > 0:
            total_units.append((unit, count))

    total_buildings = []
    for n, count in enumerate(data.building_class_created_counts):
        building = cv.BuildingClassType(n)
        if count > 0:
            total_buildings.append((building, count))

    game_state = GameState(
        state=data.game_state,
        turn=data.game_turn,
        victory=data.victory,
        winner=data.winner,
        owned_plots=data.owned_plots,
        circumnavigated=data.circumnavigated,
        nukes_buildable=data.nukes_valid,
        total_cities=data.total_cities,
        total_population=data.total_population,
        total_units=total_units,
        total_buildings=total_buildings,
    )
    return game_state


def init_game_settings(data) -> GameSettings:
    options = []
    for n, opt in enumerate(data.game_options):
        option = cv.GameOptionType(n)
        options.append((option, opt))

    mp_options = []
    for n, mp_opt in enumerate(data.mp_game_options):
        mp_option = cv.MultiplayerOptionType(n)
        mp_options.append((mp_option, mp_opt))

    victories_enabled = []
    for n, v in enumerate(data.victories):
        if v:
            victory = cv.VictoryType(n)
            victories_enabled.append(victory)

    settings = GameSettings(
        name=data.game_name,
        type=data.game_type,
        speed=data.game_speed,
        map_script=data.map_script_name,
        world_size=data.world_size,
        climate=data.climate,
        sea_level=data.sea_level,
        start_turn=data.start_turn,
        start_year=data.start_year,
        start_era=data.start_era,
        options=options,
        mp_options=mp_options,
        map_random_seed=data.map_random_seed,
        soren_random_seed=data.soren_random_seed,
        grid_width=data.grid_width,
        grid_height=data.grid_height,
        wrap_x=data.wrap_x,
        wrap_y=data.wrap_y,
        land_plots=data.land_plots,
        culture_victory_level=data.culture_victory_level,
        culture_victory_cities=data.num_culture_victory_cities,
        victories_enabled=victories_enabled,
    )
    return settings


def set_player_trade_deals(deals, players) -> dict[int, Player]:

    def process_trades(trades) -> list[Trade]:
        player_trades = []
        for trade in trades:
            item = trade.item
            amount = 1
            if trade.item in {'TRADE_GOLD', 'TRADE_GOLD_PER_TURN'}:
                amount = trade.extra_data
            elif trade.item == 'TRADE_RESOURCES':
                item = cv.BonusType(trade.extra_data)
            player_trades.append(Trade(item, amount))
        return player_trades

    for deal in deals:
        trade_deal = TradeDeal(
            deal.first_player,
            deal.second_player,
            deal.initial_game_turn,
            process_trades(deal.first_trades),
            process_trades(deal.second_trades),
        )
        players[deal.first_player].trades.append(trade_deal)
    return players


def init_players(data, max_players: int) -> dict[int, Player]:
    players = {}
    for p_idx in range(max_players):
        civ = data.civs[p_idx]
        if civ == 'NO_CIVILIZATION':
            continue
        player = Player(
            p_idx,
            name=data.leader_names[p_idx].name,
            desc=data.civ_descriptions[p_idx].description,
            short_desc=data.civ_short_descriptions[p_idx].short_description,
            adjective=data.civ_adjectives[p_idx].adjective,
            team=data.teams[p_idx],
            handicap=cv.HandicapType[str(data.handicaps[p_idx])],
            leader=cv.LeaderHeadType[str(data.leaders[p_idx])],
            civ=cv.CivilizationType[str(data.civs[p_idx])],
            score=data.ai_player_score[p_idx],
        )
        players[p_idx] = player
    return players


def set_player_data(replay_messages, players):
    """
    Read the replay messages and assign ownership of plots, cities, wonders
    as well as player religion and civics
    """

    # local vars for tracking who currently owns cities and plots
    cities: dict[str, int] = {}
    plots: dict[str, int] = {}

    def text_to_enum_name(text: str):
        rm_leading = re.sub('.*color=[0-9]+,[0-9]+,[0-9]+,[0-9]+>', '', text)
        rm_trailing = rm_leading.replace('</color>!', '')
        return rm_trailing.replace(' ', '_').upper()

    for msg in replay_messages:
        p_idx = msg.player

        if msg.type == 'CITY_FOUNDED':
            city_name = msg.text.split(' is founded')[0]
            city = City(city_name, msg.plot_x, msg.plot_y, msg.turn)
            players[p_idx].cities.append(city)
            cities[city_name] = p_idx

        elif msg.type == 'MAJOR_EVENT':
            if 'captured' in msg.text:
                city_and_owner = msg.text.split(' was captured')[0]
                city_name = city_and_owner.split('(')[0].strip()
                prev_owner = cities[city_name]
                city = players[prev_owner].pop_city(city_name)
                players[p_idx].cities.append(city)
                cities[city_name] = p_idx
            elif 'razed' in msg.text:
                city_name = msg.text.split(' is razed')[0]
                prev_owner = cities[city_name]
                players[prev_owner].pop_city(city_name)
                del cities[city_name]
            elif 'completes' in msg.text:
                wonder = msg.text.split(' completes ')[-1]
                if (msg.plot_x, msg.plot_y) == (-1, -1):  # global wonder (ie apollo)
                    players[p_idx].projects.append(wonder)
                    continue
                city = players[p_idx].city_from_xy(msg.plot_x, msg.plot_y)
                city.wonders.append(wonder)
            elif 'born' in msg.text:
                gp = msg.text.split(' has been born')[0]
                players[p_idx].great_people.append(gp)
            elif 'converts' in msg.text:
                relig_text = text_to_enum_name(msg.text)
                religion = cv.ReligionType[f'RELIGION_{relig_text}']
                players[p_idx].religion = religion
            elif 'adopts' in msg.text:
                civic_text = text_to_enum_name(msg.text)
                civic = cv.CivicType[f'CIVIC_{civic_text}']
                players[p_idx].adopt_civic(civic)
            else:
                # potentially handle war decs and peace signings
                # print(msg.player, msg.text)
                pass

        elif msg.type == 'PLOT_OWNER_CHANGE':
            plot_key = f'{msg.plot_x}-{msg.plot_y}'
            try:
                prev_owner = plots[plot_key]
            except KeyError:
                # First assignment
                plots[plot_key] = p_idx
                players[p_idx].owned_plots += 1
                continue
            # re-assignment
            if p_idx > -1:
                players[p_idx].owned_plots += 1
                if prev_owner > -1:
                    players[prev_owner].owned_plots -= 1
            # owner lost plot but no new owner
            elif p_idx == -1:
                players[prev_owner].owned_plots -= 1
            plots[plot_key] = p_idx

    return players


def default(data, max_players) -> dict:
    settings = init_game_settings(data)
    game_state = init_game_state(data)
    players = init_players(data, max_players)
    players = set_player_data(data.replay_messages, players)
    players = set_player_trade_deals(data.deals, players)
    return dict(settings=settings, game_state=game_state, players=players)


def just_settings(data) -> dict:
    return asdict(init_game_settings(data))


def just_players(data, max_players) -> dict:
    players = init_players(data, max_players)
    players = set_player_data(data.replay_messages, players)
    players = set_player_trade_deals(data.deals, players)
    return players


def player_list(data, max_players) -> list[dict]:
    # idx, name, leader, civ
    players = init_players(data, max_players)
    return [
        {
            'idx': players[p].idx,
            'name': players[p].name,
            'civ': players[p].civ,
            'leader': players[p].leader
        }
        for p in players
    ]


def player(data, max_players, player_idx: int) -> dict:
    players = init_players(data, max_players)
    return asdict(players[player_idx])


def with_plots(data, max_players) -> dict:
    out = default(data, max_players)
    plots = init_plots(data)
    out['plots'] = plots
    return out
