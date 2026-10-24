# Civ4Save 

Parse the data in a `.CivBeyondSwordSave` file.

Currenly only vanilla BTS saves are supported (No mods). Once the remaining parsing bugs are ironed out I
will work to support the most popular mods (BAT, BUG).

Thanks to [this repo](https://github.com/dguenms/beyond-the-sword-sdk) for hosting the Civ4 BTS source.
Wouldn't have been possible to make this without it.


### Usage

#### Install

* Requires Python >=3.9. CI checks Python 3.9 and 3.15.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then install
the command line tool with `uv tool install civ4save`. To use the library in a
uv project, run `uv add civ4save` instead.

#### Command line Tool

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

  FILE is a save file or directory of save files

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

![Settings](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-settings.png)

![Spoilers](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-spoilers.png)

![Player](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-player_1.png)

![Player Cont.](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-player_2.png)

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
it into a python enum. BTS takes precendence over Warlords and Warlords over Vanilla
if 2 XML files have the same name.
The enums are written to stdout. Ex. `civ4save xml --enums > enums.py` to save them to a file.

`--text-map` creates a simple JSON object mapping each `TEXT_KEY*` human presentable text
in the given `--lang`. I use this in the `contrib` package to make some of the Civ and Leader
attributes more readable.


#### As a Libray

```python

from civ4save import SaveFile

# SaveFile takes 2 args:
#   file: str | Path (required)
#   debug: bool (default False, prints hidden fields)

save = SaveFile('Rome.CivBeyondSwordSave')
save.raw  # raw construct.Struct, use to create your own wrapper objects
save.settings  # civ4save.objects.Settings
save.players  # dict[int, civ4save.objects.Player]
save.game_state  # civ4save.objects.GameState
save.get_player(0)  # Returns civ4save.objects.Player
# The plots take a few seconds to parse as there are thousands of them so they
# only get parsed when accessed. Afterwards they are cached so access is fast again
save.get_plot(x=20, y=20)  # Returns civ4save.objects.Plot
for plot in save.plots:
    print(plot.owner, plot.improvement_type)
```


### Development / Contributing

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone the
repository, and run these commands from its root:

```bash
uv sync --locked
uv run --locked civ4save --help
uv run --locked pytest
uv run --locked ruff check src tests
uv run --locked mypy src
```

`uv sync` installs the project in editable mode and includes the development
dependency group. `uv run` uses the project's `.venv`; activation is unnecessary.
`--locked` checks that `pyproject.toml` and the checked-in `uv.lock` agree without
updating the lockfile.

Ruff uses its [current default rule set](https://docs.astral.sh/ruff/default-rules/)
with a Python 3.9 target. No `lint.select` override is needed; dependency upgrades
can expand the defaults, so review new findings when updating Ruff.

For a focused test or to select a Python version:

```bash
uv run --locked pytest tests/test_savefile.py -k bismark
uv run --locked --python 3.9 pytest
uv run --locked --python 3.15 pytest
```

uv can download a requested interpreter if it is missing. Selecting a different
Python version recreates `.venv` for that version. CI uses separate jobs for
Python 3.9 and 3.15, covering the minimum and newest targeted versions. The
project retains compatibility with 3.9 and 3.10,
although [upstream Python support](https://devguide.python.org/versions/) now
covers 3.11 through 3.15. Use an upstream-supported version for development.

The maintenance branch has known failures: `parse --json` is unimplemented,
the large Gandhi and Mehmed saves fail exact plot parsing, and Ruff's expanded
defaults expose existing lint findings, mostly unused `noqa` comments and older
typing syntax. XML CLI tests also require a local Civ IV installation and fail
when its XML files cannot be found.
CI runs the full suite
and reports these failures; it does not suppress them. See
[PLOT_PARSING_NOTES.md](PLOT_PARSING_NOTES.md) for parser diagnostics.

To refresh dependencies, then review and validate the resulting lockfile:

```bash
uv lock --upgrade
uv sync --locked
```

Commit `pyproject.toml` and `uv.lock` together when changing dependency
requirements. The lockfile selects compatible dependency versions for each
Python version, including older releases where necessary for Python 3.9.

Build the source distribution and wheel with:

```bash
uv build
```

For a release, synchronize the version in `pyproject.toml`,
`src/civ4save/__init__.py`, and `tests/test_civ4save.py`, run the checks above,
and build into an empty `dist/` directory. After reviewing the artifacts, upload
those specific files with `uv publish dist/<filename>.tar.gz dist/<filename>.whl`
using your PyPI credentials. Publishing is a separate, explicit step.

### How it Works
Games are saved in a what's basically a memory dump that kind of looks like a sandwich.

`| uncompressed data | zlib compressed data | uncompressed data + checksum |`

The `SaveFile` class handles all of the decompression stuff as well as the parsing using the
[construct](https://github.com/construct/construct) library.

If you want to see the actual binary structure of the save file see `src/civ4save/vanilla/structure.py`.


### Write Order
The game calls its `::write` functions in this order when saving:

1. CvInitCore (done)
2. CvGame (done)
3. CvMap (done)
4. CvPlot (buggy/inconsistent)
5. CvArea (under construction)
6. CvTeam (not implemented)
7. CvPlayer (not implemented)


### Plots Bug
For some unknown reason save files larger than 136KB (largest I have that doesn't encounter the bug)
parsing fails about half through the plots array. pass `debug=True` to `SaveFile` to see details when parsing
a large save file and you'll get detailed debugging output.


### TODO
- Click mutually exclusive group plugin for more robust cli arg handling
- Better docs
- `SaveFile` needs a logger
- `src/civ4save/objects/*` all need tests
- `xml_files.py` needs tests
- Caching of parsed saves (probably using [dataclasses_json](https://pypi.org/project/dataclasses-json/))
- [Textual](https://github.com/Textualize/textual) UI for browsing saves in a directory
    - maybe a `send to trash` button to make it easy to clean out unwanted saves
- Diffing tools to tell what changed between 2 saves/autosaves
