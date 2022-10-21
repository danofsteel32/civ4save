"""Provides civ4save command line tool.

Commands:
    parse: Uncompress and parse a .CivBeyondSwordSave file.
    gamefiles: Find and print commonly used game folders.
    leaders: List on or all of the Leaders found in the XML files.
    civs: List one or all of the Civilizations found in the XML files.
    xml: Generate python code or JSON from XML files.

Examples:
```
$ civ4save parse Rome.CivBeyondSwordSave
$ civ4save gamefiles
$ civ4save leaders Shaka
$ civ4save civs Germany
$ civ4save xml --text-map --lang Spanish
```
"""

import json
from functools import partial
from pathlib import Path
from typing import Callable, List, Tuple

import click
from rich import print

from . import __version__, utils
from .contrib.civs import get_civ, get_civs
from .contrib.leaders import get_leader, leader_attributes, rank_leaders
from .objects import Context
from .save_file import SaveFile
from .xml_files import make_enums as write_enums

TEXT_MAP_LANGS = ["English", "French", "German", "Italian", "Spanish"]


@click.group()
@click.version_option(__version__)
def cli():  # noqa: D103
    pass


@cli.command()
@click.option(
    "--max-players",
    default=19,
    type=int,
    help="Needed if you have changed MAX_PLAYERS value in CvDefines.h",
)
@click.option(
    "--settings",
    is_flag=True,
    show_default=True,
    default=False,
    help="Basic settings only. Nothing that would be unknown to the human player",
)
@click.option(
    "--spoilers",
    is_flag=True,
    show_default=True,
    default=False,
    help="Extra info that could give an advantage to human player",
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
    help="Format output as JSON. Default is text",
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
) -> None:
    """Parse a .CivBeyondSwordSave file.

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
        return
    if player > -1:
        print_fn(save.get_player(player))
        return
    if list_players:
        print_fn(save.players)
        return
    print_fn(save.settings)
    return


@cli.command(help="Find and print relevant game files paths.")
def gamefiles():
    """Print commonly used Civ4 file paths to `stdout`."""
    names_and_getters: List[Tuple[str, Callable[[], Path]]] = [
        ("Game Folder", utils.get_game_dir),
        ("Saves Folder", utils.get_saves_dir),
        ("XML Folder", utils.get_xml_dir),
    ]

    for name, get_dir_func in names_and_getters:
        print(f"[bold]{name}[/bold]")
        print(f"[bold]{'-'*len(name)}[/bold]")
        try:
            dir = get_dir_func()
            print(utils.renderable_filepath(dir))
        except FileNotFoundError:
            pass


@cli.command()
@click.option(
    "--enums", is_flag=True, default=False, help="Transform XML files into Python Enums"
)
@click.option(
    "--text-map",
    is_flag=True,
    default=False,
    help="Create JSON mapping TEXT_KEY to LANG.",
)
@click.option(
    "--lang",
    type=click.Choice(TEXT_MAP_LANGS),
    default="English",
    help="Language to map TEXT_KEY's to",
)
def xml(enums: bool, text_map: bool, lang: str):
    """Generate python code or JSON from the XML files."""
    if enums:
        write_enums()
        return
    if text_map:
        mapping = utils.make_text_map(lang)
        print(json.dumps(mapping, indent=4))
        return


@cli.command()
@click.option(
    "--sort-by",
    type=str,
    required=False,
    default="",
    help="Leader attribute to sort by. Ex. base_peace_weight",
)
@click.option(
    "-r", "--reverse", is_flag=True, default=False, help="Reverse the sort order"
)
@click.option(
    "-l", "--list", "list_", is_flag=True, default=False, help="List all leaders"
)
@click.option(
    "-a", "--attributes", is_flag=True, default=False, help="List all leader attributes"
)
@click.argument("leader_name", type=str, required=False, default="")
def leaders(
    leader_name: str, sort_by: str, reverse: bool, list_: bool, attributes: bool
):
    """Show Leader or list Leaders optionally sorted by attribute.

    LEADER_NAME examples: Shaka, 'Genghis Khan'
    """
    # List leaders alphabetically
    if list_:
        for ld, _ in rank_leaders("description"):
            print(ld)
        return
    # Rank leaders according to attribute passed to sort_by
    if sort_by:
        try:
            for ld, val in rank_leaders(sort_by, reverse):
                print(f"{ld:17} {val}")
        except AttributeError:
            print(f"Leader has no attribute {sort_by}")
        return
    # List all attributes can sort by
    if attributes:
        for attr in leader_attributes():
            print(attr)
        return
    # Otherwise print the passed Leader
    ld = get_leader(leader_name)
    if not ld:
        print(f"Leader name {leader_name} not recognized")
        return
    print(ld)


@cli.command()
@click.option(
    "-l", "--list", "list_", is_flag=True, default=False, help="List all civs"
)
@click.argument("civ_name", type=str, required=False)
def civs(civ_name: str, list_: bool):
    """Show details for a Civ or list all Civs.

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
