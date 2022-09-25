import re
from dataclasses import dataclass, field

from civ4save.enums import vanilla as e


@dataclass(slots=True)
class City:
    name: str
    x: int
    y: int
    turn_founded: int
    wonders: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Civics:
    government: e.CivicType = e.CivicType.CIVIC_DESPOTISM
    legal: e.CivicType = e.CivicType.CIVIC_BARBARISM
    labor: e.CivicType = e.CivicType.CIVIC_TRIBALISM
    economy: e.CivicType = e.CivicType.CIVIC_DECENTRALIZATION
    religion: e.CivicType = e.CivicType.CIVIC_PAGANISM


@dataclass(slots=True)
class Trade:
    item: e.TradeableItem | e.BonusType
    amount: int


@dataclass(slots=True)
class TradeDeal:
    first_player: int
    second_player: int
    initial_turn: int
    first_trades: list[Trade]
    second_trades: list[Trade]


@dataclass(slots=True)
class Player:
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
    great_people: list[str] = field(default_factory=list)
    cities: list[City] = field(default_factory=list)
    religion: e.ReligionType = e.ReligionType.NO_RELIGION
    civics: Civics = field(default_factory=Civics)
    trades: list[TradeDeal] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)

    def adopt_civic(self, new_civic: e.CivicType):
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
        raise ValueError(f"player {self.idx} has no city named {city_name}")

    def city_from_xy(self, x: int, y: int):
        for city in self.cities:
            if (city.x, city.y) == (x, y):
                return city
        raise ValueError(f"player {self.idx} has no city @ ({x}, {y})")


def _match_empire_to_player(empire: str, players: dict[int, Player]) -> int:
    """Indian matches IND"""
    all_civs = [(en.name, en.value) for en in e.CivilizationType if en.value > -1]
    empire = empire.upper()[:3]
    for civ, n in all_civs:
        stemmed = civ.split("CIVILIZATION_")[1][:3]
        if stemmed == empire:
            match = e.CivilizationType(n)
            break
    else:
        match = None
    for idx in players:
        if players[idx].civ == match:
            return idx
    else:
        raise ValueError("Could match empire to player")


def _init_players(cv_init, cv_game) -> dict[int, Player]:
    players = {}
    for p_idx in range(len(cv_init.civs)):
        civ = cv_init.civs[p_idx]
        if civ == "NO_CIVILIZATION":
            continue
        player = Player(
            p_idx,
            name=cv_init.leader_names[p_idx].name,
            desc=cv_init.civ_descriptions[p_idx].description,
            short_desc=cv_init.civ_short_descriptions[p_idx].short_description,
            adjective=cv_init.civ_adjectives[p_idx].adjective,
            team=cv_init.teams[p_idx],
            handicap=e.HandicapType[str(cv_init.handicaps[p_idx])],
            leader=e.LeaderHeadType[str(cv_init.leaders[p_idx])],
            civ=e.CivilizationType[str(civ)],
            score=cv_game.ai_player_score[p_idx],
            rank=cv_game.ai_player_rank[p_idx],
        )
        players[p_idx] = player
    return players


def _set_player_trade_deals(deals, players) -> dict[int, Player]:

    def process_trades(trades) -> list[Trade]:
        player_trades = []
        for trade in trades:
            item = e.TradeableItem[trade.item]
            amount = 1
            if trade.item in {"TRADE_GOLD", "TRADE_GOLD_PER_TURN"}:
                amount = trade.extra_data
            elif trade.item == "TRADE_RESOURCES":
                item = e.BonusType(trade.extra_data)  # type: ignore
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


def _set_player_data(replay_messages, players):
    """
    Read the replay messages and assign ownership of plots, cities, wonders
    as well as player religion and civics
    """

    # local vars for tracking who currently owns cities and plots
    cities: dict[str, int] = {}
    plots: dict[str, int] = {}

    def text_to_enum_name(text: str):
        rm_leading = re.sub(".*color=[0-9]+,[0-9]+,[0-9]+,[0-9]+>", "", text)
        rm_trailing = rm_leading.replace("</color>!", "")
        return rm_trailing.replace(" ", "_").upper()

    for msg in replay_messages:
        p_idx = msg.player

        if msg.type == "CITY_FOUNDED":
            city_name = msg.text.split(" is founded")[0]
            city = City(city_name, msg.plot_x, msg.plot_y, msg.turn)
            players[p_idx].cities.append(city)
            cities[city_name] = p_idx

        elif msg.type == "MAJOR_EVENT":
            if "captured" in msg.text:
                city_and_owner = msg.text.split(" was captured")[0]
                city_name = city_and_owner.split("(")[0].strip()
                prev_owner = cities[city_name]
                city = players[prev_owner].pop_city(city_name)
                players[p_idx].cities.append(city)
                cities[city_name] = p_idx
            elif "razed" in msg.text:
                city_name = msg.text.split(" is razed")[0]
                prev_owner = cities[city_name]
                players[prev_owner].pop_city(city_name)
                del cities[city_name]
            elif "completes" in msg.text:
                wonder = msg.text.split(" completes ")[-1]
                if (msg.plot_x, msg.plot_y) == (-1, -1):  # global wonder (ie apollo)
                    players[p_idx].projects.append(wonder)
                    continue
                city = players[p_idx].city_from_xy(msg.plot_x, msg.plot_y)
                city.wonders.append(wonder)
            elif "born" in msg.text:
                gp = msg.text.split(" has been born")[0]
                players[p_idx].great_people.append(gp)
            elif "converts" in msg.text:
                relig_text = text_to_enum_name(msg.text)
                religion = e.ReligionType[f"RELIGION_{relig_text}"]
                players[p_idx].religion = religion
            elif "adopts" in msg.text:
                civic_text = text_to_enum_name(msg.text)
                civic = e.CivicType[f"CIVIC_{civic_text}"]
                players[p_idx].adopt_civic(civic)

            elif "revolts" in msg.text:
                city_name = msg.text.split(" revolts")[0]
                prev_owner = cities[city_name]
                city = players[prev_owner].pop_city(city_name)
                empire = msg.text.split("joins the ")[1].replace(" Empire!", "")
                p_idx = _match_empire_to_player(empire, players)
                players[p_idx].cities.append(city)
            else:
                # print(msg.player, msg.text)
                pass

        elif msg.type == "PLOT_OWNER_CHANGE":
            plot_key = f"{msg.plot_x}-{msg.plot_y}"
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


def _fix_potential_duplicate_cities(players):
    """If capital founded but then map regenerated on turn 0 | 1 there will be
    duplicate capital founding messages for the human player."""
    for p_idx in players:
        cities = players[p_idx].cities

        new_start_idx = 0
        names = set()
        for n, city in enumerate(cities):
            if city.name in names:
                new_start_idx = n
            else:
                names.add(city.name)
        players[p_idx].cities = cities[new_start_idx:]
    return players


def get_players(cv_init, cv_game) -> dict[int, Player]:
    players = _init_players(cv_init, cv_game)
    players = _set_player_data(cv_game.replay_messages, players)
    players = _set_player_trade_deals(cv_game.deals, players)
    players = _fix_potential_duplicate_cities(players)
    return players
