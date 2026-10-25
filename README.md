# Civ4Save

Civ4Save is a Python library and command line tool for reading vanilla
Civilization IV: Beyond the Sword `.CivBeyondSwordSave` files.

- Inspect game settings, players, cities, civics, and trades.
- Read game state and map plots, including ownership and improvements.
- Export save data as JSON for scripts and other tools.
- Look up civilizations and leaders, and rank leaders by attribute.
- Find game files and convert Civ IV XML into Python enums or translated text maps.

## Install

Requires Python 3.9 or newer.

[uv](https://github.com/dguenms/beyond-the-sword-sdk.git) **(recommended)**

```bash
uv tool install civ4save
civ4save --help
```

If the command is not found, run `uv tool update-shell` and restart your terminal.

To use Civ4Save as a library in an existing uv project, run:

```bash
uv add civ4save
```

**pip**

```bash
pip install civ4save
```

This installs both the command line tool and the Python library.

## Usage

### Quick start

Read the settings from a save, list its players, or export its data:

```bash
civ4save parse "Rome.CivBeyondSwordSave"
civ4save parse --list-players "Rome.CivBeyondSwordSave"
civ4save parse --player 0 "Rome.CivBeyondSwordSave"
civ4save parse --json "Rome.CivBeyondSwordSave" > settings.json
```

Pass a single save file to `parse`. Add `--spoilers` to include game state and
map data that may reveal information unavailable to the human player.

### Command line tool

```
$ civ4save --help

Usage: civ4save [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  civs       Show details for a Civ or list all Civs.
  gamefiles  Find and print relevant game files paths.
  leaders    Show Leader or list Leaders optionally sorted by attribute.
  parse      Parse a .CivBeyondSwordSave file.
  xml        Generate python code or JSON from the XML files.
```

```
$ civ4save parse --help

Usage: civ4save parse [OPTIONS] FILE

  Parse a .CivBeyondSwordSave file.

  FILE is a .CivBeyondSwordSave file.

Options:
  --settings        Basic settings only. Nothing that would be unknown to the
                    human player
  --spoilers        Extra info that could give an advantage to human player
  --player INTEGER  Only show data for a specific player idx. Defaults to the
                    human player
  --list-players    List all player (idx, name, leader, civ) in the game
  --json            Format output as JSON. Default is text
  --help            Show this message and exit.
```

Use `--json` to write a single JSON document to stdout, for example:

```bash
civ4save parse --json Rome.CivBeyondSwordSave > settings.json
civ4save parse --json --player 0 Rome.CivBeyondSwordSave > player.json
civ4save parse --json --spoilers Rome.CivBeyondSwordSave > map.json
```

By default the document contains a `settings` object. `--player INDEX` selects
a `player` object, and `--list-players` selects a `players` object keyed by player
index (JSON object keys are strings). If both are supplied, `--player` takes
precedence. `--spoilers` adds `state` and `plots` alongside the selected section.
Enum values use their names, such as `GAMESPEED_NORMAL`; nested cities, civics,
and trades are objects and arrays. JSON output contains no text header or
terminal formatting, so it can be redirected or piped to other tools.

![Settings](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-settings.png)

<details>
<summary>More output examples</summary>

![Spoilers](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-spoilers.png)

![Player](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-player_1.png)

![Player Cont.](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-player_2.png)

</details>

`gamefiles` command works on both Linux and Windows.

```
$ civ4save gamefiles

Game Folder
-----------
/home/dan/.local/share/Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword

Saves Folder
------------
/home/dan/.local/share/Steam/steamapps/compatdata/8800/pfx/drive_c/users/steamuser/My Documents/My Games/Beyond the Sword/Saves/single

XML Folder
----------
/home/dan/.local/share/Steam/steamapps/common/Sid Meier's Civilization IV Beyond the Sword/Beyond the Sword/Assets/XML
```

The `xml` command can transform the XML files into other datatypes.
It **does not make any changes to your XML files**, just reads them.

```
$ civ4save xml --help

Usage: civ4save xml [OPTIONS]

  Generate python code or JSON from the XML files.

Options:
  --enums                         Transform XML files into Python Enums.
  --text-map                      Create JSON mapping TEXT_KEY to LANG. Default is English.
  --lang [English|French|German|Italian|Spanish]
                                  Language to map TEXT_KEY's to
  --help                          Show this message and exit.
```

`--enums` could be useful for developers/modders, I used it to make this project.
It locates the XML files (Vanilla, Warlords, BTS), reads each file, and transforms
each into a python enum. BTS takes precendence over Warlords and Warlords over Vanilla
if 2 XML files have the same name.
The enums are written to stdout. Ex. `civ4save xml --enums > enums.py` to save them to a file.

`--text-map` creates a simple JSON object mapping each `TEXT_KEY*` human presentable text
in the given `--lang`. I use this in the `contrib` package to make some of the Civ and Leader
attributes more readable.


### As a library

```python
from civ4save import SaveFile

save = SaveFile("Rome.CivBeyondSwordSave")
save.raw  # Parsed Construct container for access to low-level fields
save.settings  # civ4save.objects.Settings
save.players  # dict[int, civ4save.objects.Player]
save.teams  # dict[int, civ4save.objects.Team]
save.game_state  # civ4save.objects.GameState
save.get_player(0)  # Returns civ4save.objects.Player
save.get_plot(x=20, y=20)  # Returns civ4save.objects.Plot
for plot in save.plots:
    print(plot.owner, plot.improvement_type)

player = save.get_player(0)
team = save.teams[player.team]
print(team.population, team.land)
print([tech.name for tech in team.techs])
for other_team_id, relation in team.relations.items():
    if relation.at_war:
        print("At war with team", other_team_id)

print(player.gold, player.population, player.alive)
for city in player.cities:
    print(city.idx, city.name, city.population, city.buildings)
    print(city.gold_per_turn, city.science_per_turn, city.culture_per_turn)
    print("Base hammers:", city.base_production_per_turn)
    if city.current_production is not None:
        order = city.current_production
        print(order.item.name, order.invested_production)
for unit in player.units:
    print(unit.idx, unit.unit_type.name, unit.x, unit.y, unit.promotions)
```

`save.teams` includes every team slot, including inactive and barbarian teams;
`team.alive_count` gives the number of living members. Technologies are lists of
`TechType` enums in enum order. `team.research_progress` and `team.projects` map
`TechType` and `ProjectType` enums to research progress and completed project
counts, including zero values. `team.no_trade_techs` lists technologies marked
as unavailable for trading. Relations include every team ID, including self;
their war weariness and espionage points belong to the source team and need
not match the other team's values. Team models expose current serialized state,
which may include information unavailable to the human player.

Players now use serialized state for cities, units, civics and religion rather
than reconstructing them from replay messages. `player.owned_plots` counts
current map ownership (including water); `player.land` is the serialized land
total. `player.gold_per_turn` is net diplomatic payments, not total net income.
`player.research_queue` preserves queue order. `player.religion` is the active
state religion, or `NO_RELIGION` when state religion is disabled; the previous
choice remains available as `player.last_state_religion`.

`save.players` retains configured civilizations, including eliminated players,
and omits unused `NO_CIVILIZATION` slots. Use `player.alive` to filter living
players. City and unit IDs are local to their owners: use `(owner, idx)` as a
reference. `player.capital_city` resolves the saved capital ID to a current city,
or returns `None`. `player.capital_city_id` preserves the saved value, which may
be `-1` or a stale ID for an eliminated player. City names and ownership come
directly from the save, so renamed cities and duplicate names are supported.
`city.buildings` lists present building types, including free and obsolete
buildings.

`city.production_queue` contains typed `ProductionOrder` objects in queue order;
`city.current_production` returns the first, or `None` for an empty queue. Each
order has an `OrderType`, an `item` (`UnitType`, `BuildingType`, `ProjectType`,
or `ProcessType`), a `repeat` flag, and `invested_production`. Investment is
stored per item type, so duplicate queued items share the same saved progress.
Processes such as Wealth have `invested_production=None`; unit orders also
include a `unit_ai` role. `OrderType` and `ProductionOrder` are exported from
`civ4save.objects`.

City `gold_per_turn`, `science_per_turn`, `culture_per_turn`, and
`espionage_per_turn` are saved commerce output rates converted from hundredths
to floats (for example, `1250` becomes `12.5`). Gold output does not subtract
city expenses. With No Espionage enabled, espionage output is added to culture
and `espionage_per_turn` is zero. These rates already include saved commerce
modifiers; culture per turn is distinct from accumulated culture.

`base_production_per_turn` is base hammer yield before modifiers. It excludes
overflow, chops and food converted during worker/settler production. Exact
hammers applied to an order and turns remaining are not calculated: those
also need item-specific rules from the game's XML. No installed game is needed
for the exposed rates and queue. Player JSON includes the queue and output
fields; the current order is its first queue entry.

The existing `player.great_people`, `player.projects`, and `city.wonders` string
lists remain English replay-derived history and may be incomplete. Use
`team.projects` for current project counts and `city.buildings` for current
buildings. `Unit.name` is the saved custom name and may be empty; `unit.damage`
is hit points lost. Existing imports from `civ4save.objects.player`, including
`City`, continue to work; `City`, `Civics`, and `Unit` are also exported from
`civ4save.objects`. New fields are included in the CLI's player JSON output.

`SaveFile` accepts a file path as a string or `pathlib.Path`. Pass `debug=True`
to include hidden fields when displaying parsed Construct data.

The save is decompressed and parsed on the first access to data, such as
`save.settings` or `save.raw`, and the parsed container is cached. Some arrays
are evaluated lazily. The settings, players, teams, and game-state wrappers are
cached; each access to `save.plots` creates a new list of `Plot` wrappers. Store
that list if you need to reuse it.

## Development and contributing

Clone the repository, then run these commands from its root:

```bash
uv sync --locked
uv run --locked pre-commit install
uv run civ4save --help
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
```

The hooks run Ruff's safe fixes, Ruff formatting, and mypy before each commit.
If they edit files, review and stage the changes before committing again. Run
all hooks manually with `uv run --locked pre-commit run --all-files`.

For a focused test or to select a Python version:

```bash
uv run pytest tests/test_savefile.py -k bismark
uv run --python 3.9 pytest
uv run --python 3.15 pytest
```


See [AGENTS.md](AGENTS.md) for repository development guidance and
[BINARY_FORMAT.md](BINARY_FORMAT.md) for parser coverage and binary-format notes.


## Acknowledgements
Thanks to [this repo](https://github.com/dguenms/beyond-the-sword-sdk) for hosting the Civ4 BTS source. Wouldn't have been possible to make this without it.
