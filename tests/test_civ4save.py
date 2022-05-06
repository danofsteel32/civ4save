import pytest
from pathlib import Path

from civ4save import __version__
from civ4save import save_file, organize
from civ4save.structure import SaveFormat


def test_version():
    assert __version__ == '0.1.0'


def full_run_through(file):
    max_players = 19
    save_bytes = save_file.read(file)
    data = SaveFormat.parse(save_bytes, max_players=max_players)
    assert data is not None

    organize.default(data, max_players)
    organize.just_settings(data)
    organize.just_players(data, max_players)
    for p in organize.player_list(data, max_players):
        organize.player(data, max_players, p['idx'])


def test_real_save_files():
    for f in Path('tests/saves').iterdir():
        if f.name == 'not-a-real.CivBeyondSwordSave':
            continue
        print(f'testing {f.name}')
        full_run_through(f)


def test_not_save_file():
    with pytest.raises(Exception):
        save_file.read('tests/saves/not-a-real.CivBeyondSwordSave')
