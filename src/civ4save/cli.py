import json
from functools import partial
from pathlib import Path

import click
from rich import print

from . import __version__, utils
from .contrib.civs import get_civ, get_civs
from .contrib.leaders import get_leader, leader_attributes, rank_leaders
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
    max_players,
    settings,
    spoilers,
    player,
    list_players,
    ai_survivor,
    debug,
    json_,
    file,
):
    """Parses a .CivBeyondSwordSave file

    FILE is a save file or directory of save files
    """
    context = Context(max_players=max_players, ai_survivor=ai_survivor)
    save = SaveFile(file=file, context=context, debug=debug)
    print(save)
    save.parse()

    print_fn = print
    if json_:
        # call json.dumps on the arg before calling print
        j = partial(json.dumps, indent=4, cls=utils.CustomJsonEncoder)
        print_fn = partial(print, j)

    if spoilers:
        print_fn(save.game_state)
    if player > -1:
        print_fn(save.get_player(player))
    if list_players:
        print_fn(save.players)
    print_fn(save.settings)
    return


@cli.command(help="Find and print relevant game files paths.")
def gamefiles():
    print("[bold]Game Folder[/bold]")
    print("[bold]-----------[/bold]")
    try:
        game_dir = utils.get_game_dir()
        print(utils.renderable_filepath(game_dir))
    except FileNotFoundError:
        pass

    print()
    print("[bold]Saves Folder[/bold]")
    print("[bold]------------[/bold]")
    try:
        saves_dir = utils.get_saves_dir()
        print(utils.renderable_filepath(saves_dir))
    except FileNotFoundError:
        pass

    print()
    print("[bold]XML Folder[/bold]")
    print("[bold]----------[/bold]")
    try:
        xml_dir = utils.get_xml_dir()
        print(utils.renderable_filepath(xml_dir))
    except FileNotFoundError:
        pass


@cli.command(help="Convert XML files to Enums (does not modify your files)." "")
def make_enums():
    write_enums()


@cli.command(help="Get information about the Leaders.")
@click.option("--sort-by", type=str, required=False, default=None)
@click.option("-r", "--reverse", is_flag=True, default=False)
@click.option("-l", "--list", "list_", is_flag=True, default=False)
@click.option("-a", "--attributes", is_flag=True, default=False)
@click.argument("leader_name", type=str, required=False, default=None)
def leaders(
    leader_name: str, sort_by: str | None, reverse: bool, list_: bool, attributes: bool
):
    """Inspect a specific leader or sort all of the leaders by
        the values of some leader attribute.

    LEADER_NAME examples: Shaka, 'Genghis Khan'
    """
    # List leaders alphabetically
    if list_:
        for ld, _ in rank_leaders("description"):
            print(ld)
        return
    # Rank leaders according to attribute passed to sort_by
    elif sort_by:
        try:
            for ld, val in rank_leaders(sort_by, reverse):
                print(f"{ld:17} {val}")
        except AttributeError:
            print(f"Leader has no attribute {sort_by}")
        return
    # List all attributes can sort by
    elif attributes:
        for attr in leader_attributes():
            print(attr)
        return
    # Otherwise print the passed Leader
    ld = get_leader(leader_name)
    if not ld:
        print(f"Leader name {leader_name} not recognized")
        return
    print(ld)


@cli.command(help="Print basic info about a Civilization.")
@click.option("-l", "--list", "list_", is_flag=True, default=False)
@click.argument("civ_name", type=str, required=False)
def civs(civ_name: str, list_: bool):
    """Inspect a specific Civ or list all civs.

    CIV_NAME examples: Germany, 'Holy Rome'
    """
    if list_:
        for civ_desc in get_civs():
            print(civ_desc)
        return
    civ = get_civ(civ_name)
    if not civ:
        print(f"Civilization name {civ} not recognized.")
        return
    print(civ)


if __name__ == "__main__":
    cli()
