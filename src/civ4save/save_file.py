"""Responsible for parsing a save file into useful data structures."""
from __future__ import annotations

import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from construct import setGlobalPrintPrivateEntries
from lazy_property import LazyProperty

from . import utils
from .objects import GameState, Player, Plot, Settings, get_players
from .vanilla.structure import CivBeyondSwordSave


class NotASaveFile(Exception):
    """Raised when file can't be parsed as a save file."""

    pass


class ParseError(Exception):
    """Raised when unexpected parsing error."""

    pass


def _find_zlib_end(data: bytes, z_start: int) -> int:
    """Used to decompress file.

    Binary search to find byte index where incomplete data stream becomes
    incorrect data stream. I'm not sure if the guess_limit makes sense but
    I do want some check to an infinite loop / hang.

    https://forums.civfanatics.com/threads/need-a-little-help-with-editing-civ4-save-files.452707/
    """
    guess_limit = 50

    low, high = z_start, len(data)
    prev = 0
    guesses = 0
    while True:
        z_end = (low + high) // 2
        if z_end == prev:
            return z_end
        if guesses > guess_limit:
            raise NotASaveFile("Could not find zlib end byte index")
        try:
            zlib.decompress(data[z_start:z_end])
        except Exception as ex:
            prev = z_end
            if "incomplete" in ex.__str__():
                low = z_end + 1
            elif "invalid" in ex.__str__():
                high = z_end - 1
        guesses += 1


def _read_savefile(file: Union[str, Path]) -> bytes:
    """Read and decompress file.

    Find the index in where the zlib magic header is, then find the end
    of the compressed bytes. Then decompress and return the bytes.
    """
    with open(file, "rb") as f:
        data = f.read()

    magic_number = bytes.fromhex("789c")  # default compression
    z_start = data.find(magic_number)
    z_end = _find_zlib_end(data, z_start)
    if z_start < 0 or z_end < 0:
        raise NotASaveFile("This is not a .CivBeyondSwordSave file")

    decomp_obj = zlib.decompressobj()
    uncompressed_data = decomp_obj.decompress(data[z_start:z_end])

    return data[:z_start] + uncompressed_data + data[z_end:]


class SaveFile:
    """Wraps the parsed save file with useful methods."""

    def __init__(
        self,
        file: Union[str, Path],
        debug: bool = False,
    ) -> None:
        """Read and decompress the file, but do not parse anything yet.

        Args:
            file (str | Path): File to be parsed.
            debug (bool): Whether to print detailed debug info. Defaults to False.
        """
        self.file = file
        # Print everything if debug
        setGlobalPrintPrivateEntries(debug)
        self.debug = debug

        self._raw_bytes: bytes
        self._raw: Optional[Any] = None

        self._version: int = 0

    @property
    def raw(self) -> Any:
        """Returns the raw parsed struct."""
        if not self._raw:
            try:
                self._raw_bytes = _read_savefile(self.file)
                self._raw = CivBeyondSwordSave.parse(self._raw_bytes)
            except Exception:
                raise NotASaveFile(f"{self.file}")
        return self._raw

    @property
    def version(self) -> int:
        """Returns the version of the save file, 302 for BTS vanilla."""
        return self.raw.version

    @property
    def current_turn(self) -> int:
        """Returns the current turn."""
        return self.raw.game_turn

    @property
    def map_size(self) -> Tuple[int, int]:
        """Returns map grid size (width x height)."""
        return self.raw.grid_width, self.raw.grid_height

    @LazyProperty
    def settings(self) -> Settings:
        """Returns the game's settings."""
        return Settings.from_struct(self.raw)

    @LazyProperty
    def game_state(self) -> GameState:
        """Return `GameState` object."""
        return GameState.from_struct(self.raw)

    @LazyProperty
    def players(self) -> Dict[int, Player]:
        """Return players Dict."""
        return get_players(self.raw)

    @property
    def plots(self) -> List[Plot]:
        """Return the Plots list."""
        return [Plot.from_struct(p) for p in self.raw.plots]

    def get_plot(self, x: int, y: int) -> Optional[Plot]:
        """Return `Plot` matching the given coordinates (x, y)."""
        plot_index = utils.calc_plot_index(self.map_size[0], x, y)
        try:
            return self.plots[plot_index]
        except IndexError:
            return None

    def get_player(self, player_idx: int) -> Optional[Player]:
        """Return `Player` at the given player idx."""
        # will raise KeyError
        return self.players[player_idx]

    def __str__(self) -> str:
        """Return string representation of the `SaveFile`."""
        v = self.version
        sz = len(self._raw_bytes)
        try:
            n = self.file.name  # type: ignore
            return f"SaveFile(file={n}, version={v}, size={sz})"
        except AttributeError:
            f = self.file
            return f"SaveFile(file={f}, version={v}, size={sz})"
