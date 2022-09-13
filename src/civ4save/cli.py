import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum

from . import organize, save_file, utils
from .structure import get_format
from .xml_files import make_enums


def unenumify(e) -> str:
    strip_leading = str(e).split("_")[1:]
    return " ".join(strip_leading).title()


class CustomJsonEncoder(json.JSONEncoder):
    """
    Enables serializing dataclasses and Enums
    """

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        elif isinstance(o, Enum):
            if o.name == "NO_RELIGION":
                return "No Religion"
            return unenumify(o.name)
        return super().default(o)


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Extract data from .CivBeyondSwordSave file"
    )
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "--max-players",
        dest="max_players",
        type=int,
        default=19,
        help="Needed if you have changed your MAX_PLAYERS value in CvDefines.h",
    )
    group.add_argument(
        "--gen-enums",
        dest="gen_enums",
        action="store_true",
        default=False,
        help="Create enums file from XML files",
    )
    group.add_argument(
        "--gamefiles",
        action="store_true",
        default=False,
        help="Find and print relevant game files paths",
    )
    group.add_argument(
        "--plots",
        dest="plots",
        action="store_true",
        default=False,
        help="Attempt to parse the plot data. WARNING: still buggy!",
    )
    group.add_argument(
        "--settings",
        dest="settings",
        action="store_true",
        default=False,
        help="Only return the games settings. No game state or player data",
    )
    group.add_argument(
        "--player",
        dest="player",
        type=int,
        default=-1,
        help="Only return the player data for a specific player idx",
    )
    group.add_argument(
        "--list-players",
        dest="list_players",
        action="store_true",
        default=False,
        help="List all player idx, name, leader, civ in the game",
    )
    parser.add_argument(
        "--ai-survivor",
        dest="ai_survivor",
        action="store_true",
        default=False,
        help="Use XML settings from AI Survivor series",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Print debug info",
    )
    parser.add_argument(
        "file", type=str, help="Target save file", const=None, nargs="?"
    )
    return parser.parse_args(args)


def run():
    args = parse_args(sys.argv[1:])

    if args.gamefiles:
        print(utils.get_game_dir())
        print(utils.get_saves_dir())
        return

    if args.gen_enums:
        make_enums(args.ai_survivor)
        return

    if not args.file:
        print("Save file is a required argument")
        sys.exit(1)

    save_bytes = save_file.read(args.file)
    fmt = get_format(args.ai_survivor, args.plots, args.debug)

    try:
        data = fmt.parse(save_bytes, max_players=args.max_players)
    except Exception as e:
        print(e)
        if args.with_plots:
            print("Probably the plots bug")

    out: dict | list[dict]
    if args.settings:
        out = organize.just_settings(data)
    elif args.player >= 0:
        out = organize.player(data, args.max_players, args.player)
    elif args.list_players:
        out = organize.player_list(data, args.max_players)
    else:
        if args.plots:
            out = organize.with_plots(data, args.max_players)
        else:
            out = organize.default(data, args.max_players)
    print(json.dumps(out, indent=4, cls=CustomJsonEncoder))


if __name__ == "__main__":
    run()
