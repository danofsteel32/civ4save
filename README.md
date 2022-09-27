# Civ4Save 

Parse the data in a `.CivBeyondSwordSave` file.

So far I've only tested with the vanilla version of the Civ4 BTS and the slightly tweaked XML files
Sullla uses in the [AI survivor series](https://sullla.com/Civ4/civ4survivor6-14.html).
A tweaked DLL to support a higher `MAX_PLAYERS` will work you just need to pass the `max_players` value to the parser.

Mods like BAT/BUG/BULL change the structure of the save file and currently cannot be parsed.
I'd like to support them but I need specific details on what changes the mods are making to the binary save format.

Thanks to [this repo](https://github.com/dguenms/beyond-the-sword-sdk) for hosting the Civ4 BTS source.
Wouldn't have been possible to make this without it.


### Usage

#### Install

* Requires >= python3.10
* If someone opens an issue requesting 3.6-3.9 I'll get to it

`python -m pip install civ4save`

#### Command line Tool

```
$ civ4save --help

Usage: civ4save [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  gamefiles   Find and print relevant game files paths
  make-enums  Convert XML files to Enums (does not modify your files).
  parse       Parses a .CivBeyondSwordSave file
```

```
$ civ4save parse --help

Usage: civ4save parse [OPTIONS] FILE

  Parses a .CivBeyondSwordSave file

  FILE is a save file or directory of save files

Options:
  --max-players INTEGER  Needed if you have changed your MAX_PLAYERS value in
                         CvDefines.h
  --settings             Basic info and settings only. Nothing that would be
                         unknown to the human player
  --spoilers             Extra info that could give an advantage to human
                         player.
  --player INTEGER       Only show data for a specific player idx. Defaults to
                         the human player
  --list-players         List all player (idx, name, leader, civ, etc.) in the game
  --ai-survivor          Use XML settings from AI Survivor series
  --debug                Print detailed debugging info
  --json                 Format output as JSON
  --help                 Show this message and exit.
```

![Settings](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-settings.png)

![Spoilers](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-spoilers.png)

![Player](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-player_1.png)

![Player Cont.](https://github.com/danofsteel32/civ4save/blob/main/screenshots/civ4save-player_2.png)

`gamefiles` command works on both Linux (flatpak Steam install too) and Windows.

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

`make-enums` command could be useful for developers/modders, I needed it to make this library possible.
It locates the XML files (Vanilla, Warlords, BTS), reads each file, and transforms it into a python enum.
BTS takes precendence over Warlords and Vanilla if 2 XML files have the same name.
The enums are written to stdout. Ex. `civ4save make-enums > enums.py`
It **does not make any changes to your files**.


#### As a Libray

```python

from civ4save import SaveFile

# SaveFile takes 3 args:
#   file: str | Path (required)
#   context: Context | None (default None)
#   debug: bool (default False)
save = SaveFile('Rome.CivBeyondSwordSave')
save.settings  # civ4save.objects.Settings
save.players  # dict[int, civ4save.objects.Player]
save.game_state  # civ4save.objects.GameState
save.get_player(0)  # Returns civ4save.objects.Player
# The plots take a few seconds to parse as there are thousands of them so they
# only get parsed when accessed. Afterwards they are cached so access is fast again
save.get_plot(x=20, y=20)  # Returns civ4save.objects.Plot
for plot in save.plots:
    print(plot.owner, plot.improvement_type)

# Optionally create a Context to change a few values the parser uses
# Context takes 3 kwargs:
#   max_players: int (default is 19, defines length of many arrays in the savefile)
#   max_teams: int (defaults to same as max_players)
#   ai_survivor: bool (default False, changes the size of the BuildingType arrays)
context = Context(max_players=50)
save = SaveFile('Rome.CivBeyondSwordSave', context)
```


### Development / Contributing

`python -m pip install ".[dev]"` to install in editable mode along with all dev deps.

`python -m pytest tests/` to run the tests.

Or you can use the `./run.sh` script if you're on Linux.

```
./run.sh install dev
./run.sh tests
./run.sh c4 --help
./run.sh clean
./run.sh build
```

### How it Works
Games are saved in a what's basically a memory dump that kind of looks like a sandwich.

`| uncompressed data | zlib compressed data | uncompressed data + checksum |`

The `SaveFile` class handles all of the decompression stuff as well as the parsing using the
[construct](https://github.com/construct/construct) library.

If you want to see the actual binary structure of the save file see `src/civ4save/structs.py`.


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
a large save file and you'll get detailed debugging output. When `debug=False` the parser parses as many
plots as it can and doesn't raise any exceptions.


### TODO
- Caching of parsed saves (Pickle?, JSON?)
- Build more useful objects from some of the XML files (Leaders, Civs)
- [Textual](https://github.com/Textualize/textual) UI for browsing saves in a directory
- `xml_files.py` needs tests
- `src/civ4save/objects/*` all need tests
- use `pdoc` to autogenerate docs (and better docstrings)
- `contrib` subpackage for interesting scripts (ex. comparing starting locations in ai survivor)
- diffing tools to tell what changed between 2 saves/autosaves
- Click mutually exclusive group plugin for more robust cli arg handling
- `cli.py` fix all those if statements
