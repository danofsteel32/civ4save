"""Context is used in parsing."""

import importlib
import types


class Context:
    """Object that gets passed to structs to set runtime context.

    Many of the arrays in the save file have their size set by the value
    of max_players and max_teams. There are also many arrays whose size
    is set by the number of items in the enums generated at runtime from
    the XML files. For example the `unit_created_counts` array is sized
    based on the number of unit types in the `UnitType` enum.
    """
    def __init__(
        self, max_players: int = 19, max_teams: int = 0, ai_survivor: bool = False
    ):
        """Initialize a new Context object.

        Args:
            max_players (int): Civ4 DLL can be compiled with a different
                MAX_PLAYERS value. Default is 19.
            max_teams (int): Optional arg to override default of
                max_teams == max_players.
            ai_survivor (bool): Whether or not to use enums created from
                ai survivor XML files. Defaults to False.
        """
        self.max_players = max_players
        self.max_teams = max_teams if max_teams else max_players
        self.ai_survivor = ai_survivor
        self.enums: types.ModuleType
        if ai_survivor:
            self._module = "ai_survivor"
        else:
            self._module = "vanilla"
        self.enums = importlib.import_module(f"civ4save.enums.{self._module}")

    def __str__(self):
        """Return string representation of the Context."""
        mp = self.max_players
        mt = self.max_teams
        ai = self.ai_survivor
        m = self._module
        return f"Context(max_players={mp}, max_teams={mt}, ai_survivor={ai}, enums={m})"
