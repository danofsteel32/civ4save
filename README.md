# Beyond the Sword Save File Reader

Uncompresses and decodes the data in a `.CivBeyondSwordSave` file.
check out this [example](example.json) to see what data you can get.

So far I've only tested with the vanilla version of the Civ4 BTS and the slightly tweaked XML files Sullla uses in the [AI survivor series](https://sullla.com/Civ4/civ4survivor6-14.html).
Mods like BAT/BUG/BULL change the structure of the save file and do not work.
I'd like to support them but I need specific details on what changes the mods are making to the binary save format.

Thanks to [this repo](https://github.com/dguenms/beyond-the-sword-sdk) for hosting
the Civ4 BTS source. Wouldn't have been possible to make this without it.


### Usage

#### Install

* Requires >= python3.10
* If someone opens an issue requesting 3.6-3.9 I'll get to it

`python -m pip install civ4save`

#### Command line Tool
Output is JSON.

`python -m civ4save <options> <save_file>`

```
usage: civ4save [-h] [--max-players MAX_PLAYERS]
    [--with-plots | --just-settings | --just-players | --player PLAYER | --list-players]
    file

Extract data from .CivBeyondSwordSave file

positional arguments:
  file                  Target save file

options:
  -h, --help            show this help message and exit
  --max-players MAX_PLAYERS
                        Needed if you have changed your MAX_PLAYERS value in CvDefines.h
  --with-plots          Attempt to parse the plot data. WARNING: still buggy!
  --just-settings       Only return the games settings. No game state or player data
  --just-players        Only return the player data
  --player PLAYER       Only return the player data for a specific player idx
  --list-players        List all player idx, name, leader, civ in the game
  --ai-survivor         Use XML settings from AI Survivor series
  --debug               Print debug info
```

#### As a Libray

```python
from civ4save import save_file
from civ4save.structure import get_format

save_bytes = save_file.read('path/to/save')

# get_format takes 3 optional arguments
# ai_survivor: bool  -- use the tweaked XML files as seen in ai survivor
# with_plots: bool  -- try expiremental plot parsing
# debug: bool  -- calls Construct.Probe() to print debug info
fmt = get_format()
# default max_players=19, you'll know if you changed this
data = fmt.parse(save_bytes, max_players=19)

# do whatever you want to with the data, see organize.py for ideas
```

#### Developement / Contributing
* [poetry](https://python-poetry.org/docs/)
* run tests with `poetry run pytest -rP tests/`
* If you open an issue please attach the save file you had the issue with


### How it Works
Games are saved in a binary format that kind of looks like a sandwich

`| uncompressed data | zlib compressed data | uncompressed checksum |`

with most of the data in the compressed middle part. See `save_file.py` to understand
how the file is uncompressed.

The [construct](https://github.com/construct/construct) library makes it easy to declaratively
define the binary format in `structure.py` and this gives us parsing/writing for free.

From there the functions in `organize.py` sort and cleanup the parsed data.

The enums defined in `cv_enums.py` are automatically generated from the game
XML files using `xml_to_enum.py`. To run this yourself you'll need to install the optional
`jinja2` and `xmltodict` dependencies:

`poetry install -E xml`

Right now the paths to the XML files in `xml_to_enum.py` are hardcoded so you'll have to edit
them to match your system.


#### Write Order
The game calls it's `::write` functions in this order:

1. CvInitCore
2. CvGame
3. CvMap
4. CvPlot (incomplete/buggy)
4. CvTeam (not implemented)
5. CvPlayer (not implemented)

But there's issues consistently parsing `CvPlot` so only up to CvMap is parsed by default.
I haven't drilled down the exact cause but it seems to have something to do with the size of the save file.
Files under 136K (largest test save I have that works) parse fine but anything larger only makes it through ~30-80% of the plots before hitting a string of `0xff` bytes followed by data I can't make any sense of.

`poetry run python -m civ4save.plots_bug.py` will demonstrate the bug and prints out debug info.
