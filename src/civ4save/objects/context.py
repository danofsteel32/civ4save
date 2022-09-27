import importlib
import types


class Context:
    """
    max_players: int
    max_teams: int
    ai_survivor: bool
    """

    def __init__(
        self, max_players: int = 19, max_teams: int = 0, ai_survivor: bool = False
    ):
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
        mp = self.max_players
        mt = self.max_teams
        ai = self.ai_survivor
        m = self._module
        return f"Context(max_players={mp}, max_teams={mt}, ai_survivor={ai}, enums={m})"
