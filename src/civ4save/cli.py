from functools import partial
from pathlib import Path
import json

import click
from rich import print

from . import __version__, utils
from .objects import Context
from .save_file import SaveFile
from .xml_files import make_enums as write_enums


@click.group()
@click.version_option(__version__)
def cli():
    pass


@cli.command()
@click.option(
    "--max-players",
    default=19,
    type=int,
    help="Needed if you have changed your MAX_PLAYERS value in CvDefines.h",
)
@click.option(
    "--settings",
    is_flag=True,
    show_default=True,
    default=False,
    help="Basic info and settings only. Nothing that would be unknown to the human player",
)
@click.option(
    "--spoilers",
    is_flag=True,
    show_default=True,
    default=False,
    help="Extra info that could give an advantage to human player.",
)
@click.option(
    "--player",
    default=-1,
    type=int,
    help="Only show data for a specific player idx. Defaults to the human player",
)
@click.option(
    "--list-players",
    is_flag=True,
    show_default=True,
    default=False,
    help="List all player (idx, name, leader, civ) in the game",
)
@click.option(
    "--ai-survivor",
    is_flag=True,
    show_default=True,
    default=False,
    help="Use XML settings from AI Survivor series",
)
@click.option(
    "--debug",
    is_flag=True,
    show_default=True,
    default=False,
    help="Print detailed debugging info",
)
@click.option(
    "--json",
    "json_",
    is_flag=True,
    show_default=True,
    default=False,
    help="Format output as JSON",
)
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def parse(
    max_players, settings, spoilers, player, list_players, ai_survivor, debug, json_, file
):
    """Parses a .CivBeyondSwordSave file

    FILE is a save file or directory of save files
    """
    context = Context(max_players=max_players, ai_survivor=ai_survivor)
    save = SaveFile(file=file, context=context, debug=debug)
    print(save)
    save.parse()

    if json_:
        j = partial(json.dumps, indent=4, cls=utils.CustomJsonEncoder)
    if spoilers:
        if json_:
            print(j(save.game_state))
            return
        print(save.game_state)
        return
    if player > -1:
        if json_:
            print(j(save.get_player(player)))
            return
        print(save.get_player(player))
        return
    if list_players:
        if json_:
            print(j(save.players))
            return
        print(save.players)
        return

    if json_:
        print(j(save.settings))
        return
    print(save.settings)
    return
    # pprint(save.settings)
    # pprint(save.game_state)
    # pprint(save.players)
    # pprint(save.plots)


@cli.command(help="Find and print relevant game files paths")
def gamefiles():
    game_dir = utils.get_game_dir()
    saves_dir = utils.get_saves_dir()
    xml_dir = utils.get_xml_dir()
    print("[bold]Game Folder[/bold]")
    print("[bold]-----------[/bold]")
    print(utils.renderable_filepath(game_dir))
    print()
    print("[bold]Saves Folder[/bold]")
    print("[bold]------------[/bold]")
    print(utils.renderable_filepath(saves_dir))
    print()
    print("[bold]XML Folder[/bold]")
    print("[bold]----------[/bold]")
    print(utils.renderable_filepath(xml_dir))
    print()


@cli.command(help="Convert XML files to Enums (does not modify your files)." "")
def make_enums():
    write_enums()


if __name__ == "__main__":
    cli()
