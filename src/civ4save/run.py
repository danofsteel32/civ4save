from pathlib import Path

from civ4save import utils

from . import struct
# from civ4save.save_file import SaveFile
from .models import Context

if __name__ == "__main__":
    context = Context(max_players=19)
