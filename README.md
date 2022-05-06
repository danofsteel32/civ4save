# Beyond the Sword Save File Reader

Uncompresses and decodes the data in a `.CivBeyondSwordSave` file.
check out this [example](example.json) to see what data you can get.

I've only tested with the vanilla version of the Civ4 BTS. Mods like BAT/BUG/BULL
that only change the interface should work but I need some example saves to test with.
If your mod changes the saved game format the parser will not work but if's there's
enough demand to support a particular mod I'll make an effort to support it.

Thanks to [this repo](https://github.com/dguenms/beyond-the-sword-sdk) for hosting
the Civ4 BTS source. Wouldn't have been possible to make this without it.


### Usage

##### Developement Install
Use this if you want to work on the code.

1. clone the repo
2. `poetry install`

##### Lib/Cli Install

`python -m pip install civ4save`

##### Command line Tool
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
```

##### As a Libray

```python
from civ4save import save_file
from civ4save.structure import SaveFormat

save_bytes = save_file.read('path/to/save')

# default max_players=19, you'll know if you changed this
data = SaveFormat.parse(save_bytes, max_players)

# do whatever you want to with the data, see organize.py for ideas
```

### How it Works
Games are saved in a binary format that kind of looks like a sandwich

`| uncompressed data | zlib compressed data | uncompressed checksum |`

with most of the data in the compressed middle part. See `save_file.py` to understand
how the file is uncompressed.

Then using the [construct](https://github.com/construct/construct) library the binary format
is declaratively defined in `structure.py`.

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
I haven't drilled down the exact cause but it seems to have something to do with the size
of the save file. Files under 136K (largest test save I have that works) parse fine but
anything larger only makes it through ~30-80% of plots before failing.
