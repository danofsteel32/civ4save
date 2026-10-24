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
save.game_state  # civ4save.objects.GameState
save.get_player(0)  # Returns civ4save.objects.Player
save.get_plot(x=20, y=20)  # Returns civ4save.objects.Plot
for plot in save.plots:
    print(plot.owner, plot.improvement_type)
```

`SaveFile` accepts a file path as a string or `pathlib.Path`. Pass `debug=True`
to include hidden fields when displaying parsed Construct data.

The save is decompressed and parsed on the first access to data, such as
`save.settings` or `save.raw`, and the parsed container is cached. Some arrays
are evaluated lazily. The settings, players, and game-state wrappers are cached;
each access to `save.plots` creates a new list of `Plot` wrappers. Store that
list if you need to reuse it.

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
