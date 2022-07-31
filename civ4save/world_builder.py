import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


TEAM = re.compile("Team=*")
LEADER = re.compile("LeaderType=*")
IS_OBSERVER = re.compile("LeaderName=Survivor*")
CIV = re.compile("CivType=*")
STARTING = re.compile("StartingX=*")
BONUS = re.compile("BonusType=*")
FEATURE = re.compile("FeatureType=*")
TERRAIN = re.compile("TerrainType=*")
PLOT_TYPE = re.compile("PlotType=*")


BONUS_ORDER = list(reversed([
    "BONUS_GEMS",
    "BONUS_GOLD",
    "BONUS_SILVER",

    "BONUS_COPPER",
    "BONUS_IRON",
    "BONUS_HORSE",
    "BONUS_IVORY",

    "BONUS_CORN",
    "BONUS_PIG",
    "BONUS_COW",
    "BONUS_WHEAT",
    "BONUS_RICE",
    "BONUS_SHEEP",
    "BONUS_BANANA",
    "BONUS_DEER",

    "BONUS_FISH",
    "BONUS_CLAM",
    "BONUS_CRAB",

    "BONUS_FUR",

    "BONUS_SUGAR",
    "BONUS_SPICES",
    "BONUS_WINE",
    "BONUS_DYE",
    "BONUS_SILK",
    "BONUS_INCENSE",

    "BONUS_STONE",
    "BONUS_MARBLE",

    "BONUS_OIL",
    "BONUS_WHALE",
    "BONUS_COAL",
    "BONUS_ALUMINUM",
    "BONUS_URANIUM",
]))

BONUS_RANKS = {BONUS_ORDER[n]: max(n, 2) for n in range(len(BONUS_ORDER)-1, -1, -1)}


TERRAIN_ORDER = list(reversed([
    "TERRAIN_GRASS",
    "TERRAIN_PLAINS",
    "TERRAIN_COAST",
    "TERRAIN_TUNDRA",
    "TERRAIN_OCEAN",
    "TERRAIN_DESERT",
    "TERRAIN_SNOW",
]))

TERRAIN_RANKS = {TERRAIN_ORDER[n]: n for n in range(len(TERRAIN_ORDER)-1, -1, -1)}

FEATURE_ORDER = list(reversed([
    "FEATURE_FLOOD_PLAINS",
    "FEATURE_OASIS",
    "FEATURE_FOREST",
    "FEATURE_ICE",
    "FEATURE_JUNGLE",
]))

FEATURE_RANKS = {FEATURE_ORDER[n]: n for n in range(len(FEATURE_ORDER)-1, -1, -1)}

PLOT_TYPES = {
    "0": 0,  # peak
    "3": 1,  # ocean
    "1": 2,  # hills
    "2": 3,  # land
}


# S6_saves = (f for f in Path("tests/S6_Saves").iterdir() if "WBSave" in f.name)
# for f in S6_saves:
#     break


@dataclass
class Player:
    team: int
    leader: str
    civ: str
    start_x: int
    start_y: int


def process_player_block(player_block):
    for line in player_block:
        if IS_OBSERVER.match(line):
            return None
        if TEAM.match(line):
            team = int(line.split("=")[1])
        elif LEADER.match(line):
            leader = line.split("=")[1]
        elif CIV.match(line):
            civ = line.split("=")[1]
        elif STARTING.match(line):
            plots = line.split(", ")
            start_x = int(plots[0].split("=")[1])
            start_y = int(plots[1].split("=")[1])
    try:
        return Player(team, leader, civ, start_x, start_y)
    except UnboundLocalError:
        return None


@dataclass
class Plot:
    x: int
    y: int
    type: str
    terrain: str
    bonus: Optional[str]
    feature: Optional[str]


def process_plot_block(plot_block):
    coords = plot_block[0].split(",")
    x = int(coords[0].split("=")[1])
    y = int(coords[1].split("=")[1])
    bonus, feature = None, None
    for line in plot_block[1:]:
        if TERRAIN.match(line):
            terrain = line.split("=")[1]
        elif BONUS.match(line):
            bonus = line.split("=")[1]
        elif FEATURE.match(line):
            feature = line.split("=")[1].rstrip(", FeatureVariety")
        elif PLOT_TYPE.match(line):
            type = line.split("=")[1]
    return Plot(x, y, type, terrain, bonus, feature)


def player_plot_radius(player, plots, radius: int = 2):
    min_x, max_x = player.start_x - radius, player.start_x + radius
    min_y, max_y = player.start_y - radius, player.start_y + radius

    plot_radius = []
    for plot in plots:
        if plot.x < min_x or plot.x > max_x:
            continue
        elif plot.y < min_y or plot.y > max_y:
            continue
        plot_radius.append(plot)
    return plot_radius


def plot_value(plot):
    value = 0
    value += TERRAIN_RANKS[plot.terrain]
    value += PLOT_TYPES[plot.type]
    if plot.bonus:
        value += BONUS_RANKS[plot.bonus]
    if plot.feature:
        value += FEATURE_RANKS[plot.feature]
    return value


with open("tests/S6_Saves/survivor6-4.CivBeyondSwordWBSave", "r") as f:
    lines = [line.strip() for line in f.readlines()]

players = []
plots = []
for idx, line in enumerate(lines):

    if line == "BeginPlayer":
        player_block = []
        for player_line in lines[idx+1:]:
            if player_line != "EndPlayer":
                player_block.append(player_line)
            else:
                break
        player = process_player_block(player_block)
        if player:
            players.append(player)

    elif line == "BeginPlot":
        plot_block = []
        for plot_line in lines[idx+1:]:
            if plot_line != "EndPlot":
                plot_block.append(plot_line)
            else:
                break
        plots.append(process_plot_block(plot_block))


for player in players:
    plot_radius = player_plot_radius(player, plots, 2)
    radius_value = sum(plot_value(p) for p in plot_radius)
    print(player, radius_value)


"""
{winner} {first_dead}
"""
