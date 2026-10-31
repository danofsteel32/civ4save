"""Responsible for parsing a save file into useful data structures."""

from __future__ import annotations

import zlib
from pathlib import Path
from typing import Any

from construct import setGlobalPrintPrivateEntries
from lazy_property import LazyProperty

from . import utils
from .objects import GameState, Player, Plot, Settings, Team, get_players
from .vanilla.structure import CivBeyondSwordSave


class NotASaveFile(Exception):
    """Raised when file can't be parsed as a save file."""


class ParseError(Exception):
    """Raised when unexpected parsing error."""


def _read_savefile(file: str | Path) -> bytes:
    """Return decompressed save bytes, preserving the header and trailer."""
    return _decompress_savefile(file)[0]


def _decompress_savefile(file: str | Path) -> tuple[bytes, int]:
    """Decompress the length-prefixed zlib chunks in a BTS save.

    Each chunk has a little-endian uint32 byte length; a zero length ends the
    compressed section. All chunks belong to one zlib stream. BTS flushes this
    stream without an end marker, so zlib EOF is not the section boundary.
    Return the combined bytes and the trailer's offset in those bytes.
    """
    with open(file, "rb") as f:
        data = f.read()

    z_start = data.find(bytes.fromhex("789c"))  # default compression
    if z_start < 4:
        raise NotASaveFile("This is not a .CivBeyondSwordSave file")

    offset = z_start - 4
    decomp_obj = zlib.decompressobj()
    uncompressed = []
    while True:
        if offset + 4 > len(data):
            raise NotASaveFile(f"Missing compressed chunk length at byte {offset}")
        size = int.from_bytes(data[offset : offset + 4], "little")
        offset += 4
        if size == 0:
            break
        end = offset + size
        if end > len(data):
            raise NotASaveFile(f"Truncated compressed chunk at byte {offset}")
        try:
            uncompressed.append(decomp_obj.decompress(data[offset:end]))
        except zlib.error as exc:
            raise NotASaveFile(f"Invalid compressed chunk at byte {offset}") from exc
        offset = end

    # The schema includes the first chunk length in its uncompressed header.
    payload = data[:z_start] + b"".join(uncompressed)
    return payload + data[offset:], len(payload)


class SaveFile:
    """Wraps the parsed save file with useful methods."""

    def __init__(
        self,
        file: str | Path,
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
        self._raw: Any | None = None

        self._version: int = 0

    @property
    def raw(self) -> Any:
        """Returns the raw parsed struct."""
        if not self._raw:
            try:
                self._raw_bytes, trailer_start = _decompress_savefile(self.file)
                self._raw = CivBeyondSwordSave.parse(
                    self._raw_bytes, trailer_start=trailer_start
                )
            except Exception as exc:
                raise NotASaveFile(f"{self.file}") from exc
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
    def map_size(self) -> tuple[int, int]:
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
    def players(self) -> dict[int, Player]:
        """Return players Dict."""
        return get_players(self.raw)

    @LazyProperty
    def teams(self) -> dict[int, Team]:
        """Return all team slots keyed by ID, including inactive/barbarian teams.

        A player's team is available as ``save.teams[player.team]``.
        """
        return {record.id: Team.from_struct(record) for record in self.raw.team_records}

    @property
    def plots(self) -> list[Plot]:
        """Return the Plots list."""
        return [Plot.from_struct(p) for p in self.raw.plots]

    def get_plot(self, x: int, y: int) -> Plot | None:
        """Return `Plot` matching the given coordinates (x, y)."""
        plot_index = utils.calc_plot_index(self.map_size[0], x, y)
        try:
            return self.plots[plot_index]
        except IndexError:
            return None

    def get_player(self, player_idx: int) -> Player | None:
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
