import pathlib

import attr
import pytest

from freedesktop_icons import icons
from freedesktop_icons.cache import GtkIconCache
from freedesktop_icons.theme import Theme, ThemeDirectory


@pytest.fixture(scope='module')
def theme():
    path = pathlib.Path(__file__).parent / "data" / "test-theme"
    return Theme("test", theme_dir=path)


@pytest.fixture(scope='module')
def madeup_theme():
    return Theme("freedesktop-icons-pytest-testing-theme")


def test_subdirs(theme):
    assert list(theme._all_icon_dirs()) == ['16x16/actions']
    assert '16x16/actions' in theme.subdirs
    theme_dir = theme.subdirs['16x16/actions']
    assert theme_dir.size == 16
    assert theme_dir.type == icons.Type.FIXED
    # Not specified, spec default
    assert theme_dir.threshold == 2


def test_iconcache(theme):
    assert isinstance(theme.icon_cache, GtkIconCache)


def test_parent(theme):
    # hicolor should be excluded
    assert list(theme.parents) == ['Adwaita']


def test_iconcache_not_foun(madeup_theme):
    assert madeup_theme.icon_cache is None


def test_parent_no_theme(madeup_theme):
    assert list(madeup_theme.parents) == []


def theme_app():
    return ThemeDirectory(name="app", context="Applications", type=icons.Type.FIXED, size=64, scale=1)


def theme_app_hidpi():
    return ThemeDirectory(name="app@2x", context="Applications", type=icons.Type.FIXED, size=64, scale=2)


def theme_scalable():
    return ThemeDirectory(
        name="scalable",
        type=icons.Type.SCALABLE,
        size=48,
        min_size=32,
        max_size=64,
    )


def theme_threshold():
    return ThemeDirectory(
        name="threshold",
        type=icons.Type.THRESHOLD,
        size=48,
        threshold=8,
        min_size=32,
        max_size=64,
    )


def theme_fixed():
    return ThemeDirectory(
        name="fixed",
        type=icons.Type.FIXED,
        size=64,
    )


@pytest.fixture
def theme_directory(request):
    if callable(request.param):
        return request.param()
    return request.getfixturevalue(request.param)


def _name_icon(arg):
    # id generator for parametrized fixtures
    if isinstance(arg, icons.Icon):

        def flt(att, val):
            return val is not att.default and att.name != "name"

        return "-".join(map(str, filter(None, attr.astuple(arg, filter=flt))))


@pytest.mark.parametrize(
    ["theme_directory", "icon", "should_match"],
    (
        (theme_app, icons.Icon(name="a"), True),
        (theme_app, icons.Icon(name="a", type=icons.Type.FIXED), True),
        (theme_app, icons.Icon(name="a", type=icons.Type.SCALABLE), False),
        (theme_app, icons.Icon(name="a", type=icons.Type.THRESHOLD), False),
        (theme_app, icons.Icon(name="a", context="applications"), True),
        (theme_app, icons.Icon(name="a", context="devices"), False),
        (theme_app, icons.Icon(name="a", scale=1), True),
        (theme_app, icons.Icon(name="a", scale=2), False),
        (theme_app, icons.Icon(name="a", size=32), False),
        (theme_app, icons.Icon(name="a", size=64), True),
        (theme_app_hidpi, icons.Icon(name="a"), False),
        (theme_app_hidpi, icons.Icon(name="a", scale=1), False),
        (theme_app_hidpi, icons.Icon(name="a", scale=2), True),
        (theme_scalable, icons.Icon(name="a", size=31), False),
        (theme_scalable, icons.Icon(name="a", size=32), True),
        (theme_scalable, icons.Icon(name="a", size=64), True),
        (theme_scalable, icons.Icon(name="a", size=65), False),
        (theme_threshold, icons.Icon(name="a", size=39), False),
        (theme_threshold, icons.Icon(name="a", size=40), True),
        (theme_threshold, icons.Icon(name="a", size=56), True),
        (theme_threshold, icons.Icon(name="a", size=57), False),
    ),
    indirect=["theme_directory"],
    ids=_name_icon,
)
def test_matches_icon(theme_directory, icon, should_match):
    assert theme_directory.matches_icon(icon) is should_match


@pytest.mark.parametrize(
    ["theme_directory", "icon", "expected"],
    (
        (theme_fixed, icons.Icon(name="a", type=icons.Type.SCALABLE), None),
        (theme_app, icons.Icon(name="a", type=icons.Type.SCALABLE), None),
        (theme_fixed, icons.Icon(name="a", size=32), 32),
        (theme_fixed, icons.Icon(name="a", size=96), 32),
        (theme_scalable, icons.Icon(name="a", size=16), 16),
        (theme_scalable, icons.Icon(name="a", size=31), 1),
        (theme_scalable, icons.Icon(name="a", size=32), 0),
        (theme_scalable, icons.Icon(name="a", size=64), 0),
        (theme_scalable, icons.Icon(name="a", size=65), 1),
        (theme_scalable, icons.Icon(name="a", size=80), 16),
        (theme_threshold, icons.Icon(name="a", size=16), 16),
        (theme_threshold, icons.Icon(name="a", size=39), -7),
        (theme_threshold, icons.Icon(name="a", size=40), 0),
        (theme_threshold, icons.Icon(name="a", size=56), 0),
        (theme_threshold, icons.Icon(name="a", size=57), -7),
        (theme_threshold, icons.Icon(name="a", size=80), 16),
    ),
    indirect=["theme_directory"],
    ids=_name_icon,
)
def test_size_diff(theme_directory, icon, expected):
    assert theme_directory.size_diff(icon) == expected
