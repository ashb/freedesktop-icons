import pathlib

import pytest

from freedesktop_icons import icons
from freedesktop_icons.theme import Theme


@pytest.fixture(scope='module')
def theme():
    path = pathlib.Path(__file__).parent / "data" / "test-theme"
    return Theme(path)


def test_subdirs(theme):
    assert list(theme._all_icon_dirs()) == ['16x16/actions']
    assert '16x16/actions' in theme.subdirs
    theme_dir = theme.subdirs['16x16/actions']
    assert theme_dir.size == 16
    assert theme_dir.type == icons.Type.FIXED
    # Not specified, spec default
    assert theme_dir.threshold == 2
