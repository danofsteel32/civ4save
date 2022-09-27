import typing
import zlib
from enum import Enum, auto
from functools import cached_property
from pathlib import Path

import construct as C

from . import structs, utils
from .objects import Context, GameState, Player, Plot, Settings, get_players


class NotASaveFile(Exception):
    pass


class ParserState(Enum):
    READY = auto()
    METADATA = auto()
    CV_INIT_CORE = auto()
    CV_GAME = auto()
    CV_MAP_BASE = auto()
    CV_MAP_PLOTS = auto()
    PARTIAL_PARSE = auto()
    FULL_PARSE = auto()


class SaveFile:
    """
    file: str | Path
    context: Context | None
    debug: bool
    """

    def __init__(
        self,
        file: str | Path,
        context: typing.Optional[Context] = None,
        debug: bool = False,
    ):
        """Read and decompress the file, but do not parse anything yet"""
        self.file = file
        self.context = context if context else Context()
        self.debug = debug

        self._idx: int = 0  # current index in the byte array

        self._z_start: int = 0
        self._z_end: int = 0

        self._raw_bytes: bytes
        self._header_bytes: bytes
        self._compressed_bytes: bytes
        self._uncompressed_bytes: bytes
        self._tail_bytes: bytes
        self._bytes: bytes = self._read()

        self._version: int = 0
        self._metadata: C.Container[typing.Any] = None
        self._cv_init_core_data: C.Container[typing.Any] = None
        self._cv_game_data: C.Container[typing.Any] = None

        self._cv_map_base_data: C.Container[typing.Any] = None
        self._plots: typing.List[C.Container[typing.Any]] = []
        self._areas: typing.List[C.Container[typing.Any]] = []

        self._parser_state: ParserState = ParserState.READY

    def _read(self, wbits: int = 15) -> bytes:
        """
        Find the index in where the zlib magic header is, then find the end
        of the compressed bytes. Then decompress and return the bytes.
        """
        with open(self.file, "rb") as f:
            data = f.read()
        self._raw_bytes = data

        magic_number = bytes.fromhex("789c")  # default compression
        z_start = data.find(magic_number)
        z_end = self._find_zlib_end(data, z_start)
        if z_start < 0 or z_end < 0:
            raise NotASaveFile("This is not a .CivBeyondSwordSave file")
        self._z_start = z_start
        self._z_end = z_end

        decomp_obj = zlib.decompressobj(wbits=wbits)
        uncompressed_data = decomp_obj.decompress(data[z_start:z_end])

        self._header_bytes = data[:z_start]
        self._compressed_bytes = data[z_start:z_end]
        self._uncompressed_bytes = uncompressed_data
        self._tail_bytes = data[z_end:]

        return data[:z_start] + uncompressed_data + data[z_end:]

    def parse(self) -> ParserState:
        while True:
            if self.debug:
                print(self._parser_state)
            match self._parser_state:
                case ParserState.READY:
                    self._parser_state = ParserState.METADATA
                case ParserState.METADATA:
                    self._metadata = self._parse_metadata()
                case ParserState.CV_INIT_CORE:
                    self._cv_init_core_data = self._parse_cv_init_core()
                case ParserState.CV_GAME:
                    self._cv_game_data = self._parse_cv_game()
                case ParserState.CV_MAP_BASE:
                    self._cv_map_base_data = self._parse_cv_map_base()
                case ParserState.CV_MAP_PLOTS:
                    self._cv_map_plots_data = self._parse_cv_map_plots()
                case ParserState.PARTIAL_PARSE:
                    break
                case ParserState.FULL_PARSE:
                    break
        return self._parser_state

    def _parse_metadata(self) -> C.Container[typing.Any]:
        """
        Parses just the first few bytes of CvInitCore.
        Fail loud and early if the version number is unrecognized.
        """
        struct = structs.metadata()
        data = struct.parse(self._bytes)
        self._idx += data._idx

        if data.version != 302:
            raise NotImplementedError(f"Unkown {self.version=}")
        self._version = data.version
        # Move to next state
        self._parser_state = ParserState.CV_INIT_CORE
        return data

    def _parse_cv_init_core(self) -> C.Container[typing.Any]:
        """Parses CvInitCore"""
        struct = structs.cv_init_core(self.context)
        data = struct.parse(self._bytes[self._idx : self._z_start])
        self._idx += data._idx
        # Move to next state
        self._parser_state = ParserState.CV_GAME
        return data

    def _parse_cv_game(self) -> C.Container[typing.Any]:
        """Parses CvGame"""
        struct = structs.cv_game(self.context)
        data = struct.parse(self._bytes[self._idx :])
        self._idx += data._idx
        # Move to next state
        self._parser_state = ParserState.CV_MAP_BASE
        return data

    def _parse_cv_map_base(self) -> C.Container[typing.Any]:
        """Parses everything in CvMap up to the plots array"""
        struct = structs.cv_map_base(self.context)
        data = struct.parse(self._bytes[self._idx :])
        self._idx += data._idx
        # Move to next state
        self._parser_state = ParserState.PARTIAL_PARSE
        return data

    def _parse_cv_map_plots(
        self, x: typing.Optional[int] = None, y: typing.Optional[int] = None
    ) -> typing.List[C.Container[typing.Any]]:
        """
        Parses plots one at a time checking that at least the x, y coords are
        correct. If self.debug=True print detailed debugging info on failure
        to parse else just stop and return the plots that could be parsed.
        """
        self._start_cv_map_plots = self._idx
        struct = structs.cv_plot(self.context)

        grid_width, grid_height = self.map_size
        if x and y:
            num = utils.calc_plot_index(grid_width, x, y)
        else:
            num = grid_width * grid_height

        next_x, next_y = 0, 0
        for n in range(num):
            try:
                plot = struct.parse(self._bytes[self._idx :])
                assert (plot.x, plot.y) == (next_x, next_y)
            except (C.ConstructError, AssertionError) as ex:
                self._parser_state = ParserState.PARTIAL_PARSE
                if self.debug:
                    self._print_debug_plot(n, ex)
                break
            next_x, next_y = utils.next_plot(plot.x, plot.y, grid_width, grid_height)

            self._idx += plot.end_plot_index
            self._plots.append(plot)

        if len(self._plots) == grid_width * grid_height:
            self._parser_state = ParserState.FULL_PARSE

        return self._plots

    # METHODS UNDER CONSTRUCTION
    # def _parse_cv_map_areas(self):
    #     data = struct.CvMapAreas.parse(self._bytes[self._idx :], **self.context)
    #     self._idx += data._idx
    #     for area in data.areas:
    #         print(
    #             area.num_tiles,
    #             area.num_owned_tiles,
    #             area.num_units,
    #             area.num_cities,
    #             area.water,
    #         )
    #     print(data.peek)
    #     return data

    # def _parse_cv_team(self):
    #     data = struct.CvTeam.parse(self._bytes[self._idx :], **self.context)
    #     self._idx += data._idx
    #     print(data)
    #     return data

    # def _merge_construct_containers(self, containers):
    #     merged = containers[0]
    #     for c in containers[1:]:
    #         merged.update(c)
    #     return merged

    def _print_debug_plot(self, num: int, ex: Exception):
        """Logs the last successfully parsed plot, failing plot, and exception."""
        struct = structs.cv_plot_debug(self.context)
        grid_width, grid_height = self.map_size
        last_plot = self._plots[-1]
        print(f"Parsed {len(self._plots)}/{num} plots")
        print(f"Parsed {self._idx}/{len(self._bytes)} bytes")
        print(f"map_size={grid_width}x{grid_height}")
        print(f"Last good plot: x={last_plot.x} y={last_plot.y}")
        print(last_plot)
        print()
        debug_plot = struct.parse(self._bytes[self._idx :])
        print("Failing Plot")
        print("------------")
        print(debug_plot)
        print(ex)
        self._idx += debug_plot._idx
        print(self._idx)

    @staticmethod
    def _find_zlib_end(data: bytes, z_start: int) -> int:
        """
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
        raise NotASaveFile("Could not find zlib end byte index")

    @property
    def version(self) -> int:
        """Returns the version of the save file, 302 for BTS vanilla."""
        if self._parser_state.value < ParserState.PARTIAL_PARSE.value:
            self.parse()
        return self._version

    @property
    def current_turn(self) -> int:
        """Returns the current turn."""
        if self._parser_state.value < ParserState.PARTIAL_PARSE.value:
            self.parse()
        return self._cv_init_core_data.game_turn

    @property
    def map_size(self) -> tuple[int, int]:
        """Returns map grid size (width x height)."""
        if self._parser_state.value < ParserState.FULL_PARSE.value:
            self._parser_state = ParserState.CV_MAP_PLOTS
            self.parse()
        grid_width = self._cv_map_base_data.grid_width
        grid_height = self._cv_map_base_data.grid_height
        return grid_width, grid_height

    @cached_property
    def settings(self) -> Settings:
        """Returns the game's settings"""
        if self._parser_state.value < ParserState.PARTIAL_PARSE.value:
            self.parse()
        return Settings.from_struct(
            self._cv_init_core_data, self._cv_game_data, self._cv_map_base_data
        )

    @cached_property
    def game_state(self) -> GameState:
        if self._parser_state.value < ParserState.PARTIAL_PARSE.value:
            self.parse()
        return GameState.from_struct(self._cv_game_data, self._cv_map_base_data)

    @cached_property
    def players(self) -> dict[int, Player]:
        if self._parser_state.value < ParserState.PARTIAL_PARSE.value:
            self.parse()
        return get_players(self._cv_init_core_data, self._cv_game_data)

    @cached_property
    def plots(self) -> list[Plot]:
        if self._parser_state.value < ParserState.FULL_PARSE.value:
            self._parser_state = ParserState.CV_MAP_PLOTS
            self.parse()
        return [Plot.from_struct(p) for p in self._plots]

    def get_plot(self, x: int, y: int) -> typing.Optional[Plot]:
        if self._parser_state.value < ParserState.FULL_PARSE.value:
            self._parser_state = ParserState.CV_MAP_PLOTS
            self.parse()
        plot_index = utils.calc_plot_index(self.map_size[0], x, y)
        try:
            return self.plots[plot_index]
        except IndexError:
            return None

    def get_player(self, player_idx: int) -> typing.Optional[Player]:
        if self._parser_state.value < ParserState.PARTIAL_PARSE.value:
            self.parse()
        try:
            return self.players[player_idx]
        except KeyError:
            return None

    @property
    def file_layout(self) -> str:
        """Returns formatted str showing the files byte layout."""
        compression_ratio = len(self._uncompressed_bytes) / len(self._compressed_bytes)
        strings = [
            f"\traw bytes: {len(self._raw_bytes)}",
            f"\theader bytes (no compression): {len(self._header_bytes)}",
            f"\tzlib compressed bytes: {len(self._compressed_bytes)}",
            f"\tzlib after decompression bytes: {len(self._uncompressed_bytes)}",
            f"\ttail bytes (no compression): {len(self._tail_bytes)}",
            f"\tcompression ratio: {compression_ratio}",
        ]
        return "\n".join(strings)

    def __str__(self) -> str:
        v = self.version
        sz = len(self._raw_bytes)
        try:
            n = self.file.name  # type: ignore
            return f"SaveFile(file={n}, version={v}, size={sz})"
        except AttributeError:
            f = self.file
            return f"SaveFile(file={f}, version={v}, size={sz})"
