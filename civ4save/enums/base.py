""" enums/base.py
These are defined in the source instead of being constructed at runtime
from the XML files.
"""
from enum import Enum


class GameType(Enum):
    GAME_NONE = -1
    GAME_SP_NEW = 0
    GAME_SP_SCENARIO = 1
    GAME_SP_LOAD = 2
    GAME_MP_NEW = 3
    GAME_MP_SCENARIO = 4
    GAME_MP_LOAD = 5
    GAME_HOTSEAT_NEW = 6
    GAME_HOTSEAT_SCENARIO = 7
    GAME_HOTSEAT_LOAD = 8
    GAME_PBEM_NEW = 9
    GAME_PBEM_SCENARIO = 10
    GAME_PBEM_LOAD = 11
    GAME_REPLAY = 12


class GameStateType(Enum):
    GAMESTATE_ON = 0
    GAMESTATE_OVER = 1
    GAMESTATE_EXTENDED = 2


class YieldType(Enum):
    NO_YIELD = -1
    YIELD_FOOD = 0
    YIELD_PRODUCTION = 1
    YIELD_COMMERCE = 2


class TraitType(Enum):
    NO_TRAIT = -1
    TRAIT_PHILOSOPHICAL = 0
    TRAIT_AGGRESSIVE = 1
    TRAIT_SPIRITUAL = 2
    TRAIT_EXPANSIVE = 3
    TRAIT_INDUSTRIOUS = 4
    TRAIT_CREATIVE = 5
    TRAIT_FINANCIAL = 6
    TRAIT_ORGANIZED = 7
    TRAIT_CHARISMATIC = 8
    TRAIT_PROTECTIVE = 9
    TRAIT_IMPERIALISTIC = 10


class TradeableItem(Enum):
    TRADE_ITEM_NONE = -1
    TRADE_GOLD = 0
    TRADE_GOLD_PER_TURN = 1
    TRADE_MAPS = 2
    TRADE_VASSAL = 3
    TRADE_SURRENDER = 4
    TRADE_OPEN_BORDERS = 5
    TRADE_DEFENSIVE_PACT = 6
    TRADE_PERMANENT_ALLIANCE = 7
    TRADE_PEACE_TREATY = 8
    TRADE_TECHNOLOGIES = 9
    TRADE_RESOURCES = 10
    TRADE_CITIES = 11
    TRADE_PEACE = 12
    TRADE_WAR = 13
    TRADE_EMBARGO = 14
    TRADE_CIVIC = 15
    TRADE_RELIGION = 16


class ReplayMessageType(Enum):
    MAJOR_EVENT = 0
    CITY_FOUNDED = 1
    PLOT_OWNER_CHANGE = 2


class PlotType(Enum):
    NO_PLOT = -1
    PLOT_PEAK = 0
    PLOT_HILLS = 1
    PLOT_LAND = 2
    PLOT_OCEAN = 3


BASE_ENUMS = [
    GameType,
    GameStateType,
    YieldType,
    TraitType,
    TradeableItem,
    ReplayMessageType,
    PlotType,
]
