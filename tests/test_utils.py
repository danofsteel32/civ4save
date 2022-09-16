from enum import Enum

from civ4save import utils


class MyEnum(Enum):
    SIMPLE_CASE = 1
    MORE_COMPLEX_CASE = 2


def test_unenumify():
    simple = utils.unenumify(MyEnum.SIMPLE_CASE)
    complex = utils.unenumify(MyEnum.MORE_COMPLEX_CASE)
    assert simple == "Case"
    assert complex == "Complex Case"


def test_get_game_dir():
    assert utils.get_game_dir()


def test_get_saves_dir():
    assert utils.get_saves_dir()