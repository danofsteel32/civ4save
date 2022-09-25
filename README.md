# Civ4Save 

Parse the data in a `.CivBeyondSwordSave` file.

So far I've only tested with the vanilla version of the Civ4 BTS and the slightly tweaked XML files
Sullla uses in the [AI survivor series](https://sullla.com/Civ4/civ4survivor6-14.html).

Mods like BAT/BUG/BULL change the structure of the save file and currently cannot be parsed.
I'd like to support them but I need specific details on what changes the mods are making to the binary save format.

Thanks to [this repo](https://github.com/dguenms/beyond-the-sword-sdk) for hosting the Civ4 BTS source.
Wouldn't have been possible to make this without it.

### TODO
- Caching of parsed saves (Pickle?, JSON?)
- Textual cli for browsing saves in a directory
    - partial parsing for speeed
- `xml_files.py` needs tests
- `src/civ4save/objects/*` all need tests
- use `pdoc` to autogenerate docs
- `contrib` module/subpackage for interesting scripts (ex. comparing starting locations in ai survivor)
- diffing tools to tell what changed between 2 saves/autosaves
- Click mutually exclusive groups


### Usage

#### Install

* Requires >= python3.10 (only bc type hints)
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
/home/dan/.local/share/Steam/steamapps/compatdata/8800/pfx/drive_c/users/steamuser/My 
Documents/My Games/Beyond the Sword/Saves/single
```

`make-enums` command is useful for developers/modders.
It locates the XML files (vanilla, warlords, bts), reads each file, and transforms it into a python enum.
The enums are written to stdout. Ex. `civ4save make-enums > enums.py`
It **does not make any changes to your files**.


#### As a Libray

```python

from civ4save Context, SaveFile

# Create a Context
# Context takes 3 kwargs:
#   max_players: int (You'll know if you changed it from 19)
#   max_teams: int (defaults to same as max_players)
#   ai_survivor: bool (default False)
context = Context(max_players=19)

# SaveFile takes 3 kwargs:
#   file: str | Path
#   context: Context
#   debug: bool (default False)
# calling parse() will take a few seconds the first time
save = SaveFile('Rome.CivBeyondSwordSave', context).parse()
print(save.settings)
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

If you want to see the binary types they are defined in `src/civ4save/structs.py`


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
