from . import save_file
from .structure import DebugPlots


save_bytes = save_file.read('tests/saves/roma.CivBeyondSwordSave')
data = DebugPlots.parse(save_bytes, max_players=19)
