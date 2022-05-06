import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum

from . import organize
from . import save_file
from .structure import SaveFormat, WithPlots


def unenumify(e) -> str:
    strip_leading = str(e).split('_')[1:]
    return ' '.join(strip_leading).title()


class CustomJsonEncoder(json.JSONEncoder):
    """
    Enables serializing dataclasses and Enums
    """
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        elif isinstance(o, Enum):
            if o.name == 'NO_RELIGION':
                return 'No Religion'
            return unenumify(o.name)
        return super().default(o)


def parse_args(args):
    parser = argparse.ArgumentParser(description='Extract data from .CivBeyondSwordSave file')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        '--max-players',
        dest='max_players',
        type=int,
        default=19,
        help='Needed if you have changed your MAX_PLAYERS value in CvDefines.h'
    )
    group.add_argument(
        '--with-plots',
        dest='with_plots',
        action='store_true',
        default=False,
        help='Attempt to parse the plot data. WARNING: still buggy!'
    )
    group.add_argument(
        '--just-settings',
        dest='just_settings',
        action='store_true',
        default=False,
        help='Only return the games settings. No game state or player data'
    )
    group.add_argument(
        '--just-players',
        dest='just_players',
        action='store_true',
        default=False,
        help='Only return the player data'
    )
    group.add_argument(
        '--player',
        dest='player',
        type=int,
        help='Only return the player data for a specific player idx'
    )
    group.add_argument(
        '--list-players',
        dest='list_players',
        action='store_true',
        default=False,
        help='List all player idx, name, leader, civ in the game'
    )
    parser.add_argument('file', type=str, help='Target save file')
    return parser.parse_args(args)


def run():
    args = parse_args(sys.argv[1:])

    save_bytes = save_file.read(args.file)
    if args.with_plots:
        try:
            data = WithPlots.parse(save_bytes, max_players=args.max_players)
        except Exception:
            print('ERROR could not parse plot data')
    else:
        try:
            data = SaveFormat.parse(save_bytes, max_players=args.max_players)
        except Exception:
            print('This does not appear to be a .CivBeyondSwordSave file')

    out: dict | list[dict]
    if args.just_settings:
        out = organize.just_settings(data)
    elif args.just_players:
        out = organize.just_players(data, args.max_players)
    elif args.player:
        out = organize.player(data, args.max_players, args.player)
    elif args.list_players:
        out = organize.player_list(data, args.max_players)
    else:
        if args.with_plots:
            out = organize.with_plots(data, args.max_players)
        else:
            out = organize.default(data, args.max_players)
    print(json.dumps(out, indent=4, cls=CustomJsonEncoder))


if __name__ == '__main__':
    run()
