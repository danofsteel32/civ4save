from enum import Enum

from civ4save import utils


class MyEnum(Enum):
    NEG_VALUE = -1
    SIMPLE_CASE = 1
    MORE_COMPLEX_CASE = 2


def test_get_enum_length():
    assert utils.get_enum_length(MyEnum) == 2


def test_unenumify():
    simple = utils.unenumify(MyEnum.SIMPLE_CASE)
    complex = utils.unenumify(MyEnum.MORE_COMPLEX_CASE)
    assert simple == "Case"
    assert complex == "Complex Case"


def test_next_plot():
    assert (1, 0) == utils.next_plot(0, 0, 84, 52)
    assert (0, 1) == utils.next_plot(83, 0, 84, 52)


def test_get_game_dir():
    assert utils.get_game_dir()


def test_get_saves_dir():
    assert utils.get_saves_dir()
