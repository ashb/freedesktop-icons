from pathlib import Path
from unittest import mock

import pytest

from freedesktop_icons import Icon, Theme, lookup, lookup_fallback, theme_search_dirs


@pytest.mark.parametrize(
    ("env", "expected"),
    (
        ("", [Path.home() / '.icons']),
        ("/foo:", [Path.home() / '.icons', Path('/foo/icons')]),
    ),
)
def test_theme_search_dirs(env, expected, monkeypatch):
    monkeypatch.setenv('XDG_DATA_DIRS', env)
    assert list(theme_search_dirs()) == expected


def _stub_get_theme(get_theme, **kwargs):
    get_theme.side_effect = kwargs.get


@mock.patch("freedesktop_icons.get_theme", autospec=True)
def test_lookup(get_theme):
    real_theme = mock.create_autospec(Theme, name="real_theme")
    real_theme.parents = ['parent', 'hicolor']

    _stub_get_theme(get_theme, Adwaita=real_theme)

    lookup("org.mozilla.firefox", "Adwaita")
    assert get_theme.mock_calls == [mock.call('Adwaita')]


@mock.patch("freedesktop_icons.get_theme", autospec=True)
def test_lookup_icon(get_theme):
    real_theme = mock.create_autospec(Theme, name="real_theme")
    real_theme.parents = []

    _stub_get_theme(get_theme, Adwaita=real_theme)

    icon = Icon("org.mozilla.firefox")
    lookup(icon, "Adwaita")
    assert get_theme.mock_calls == [mock.call('Adwaita')]


@mock.patch("freedesktop_icons.get_theme", autospec=True)
def test_lookup_in_parent(get_theme):
    real_theme = mock.create_autospec(Theme, name="real_theme")
    real_theme.parents = ['parent']
    real_theme.lookup.return_value = None
    parent_theme = mock.create_autospec(Theme, name="parent_theme")

    _stub_get_theme(get_theme, Adwaita=real_theme, parent=parent_theme)

    lookup("org.mozilla.firefox", "Adwaita")
    assert get_theme.mock_calls == [mock.call('Adwaita'), mock.call('parent')]


@mock.patch("freedesktop_icons.get_theme", autospec=True)
def test_lookup_in_hicolor(get_theme):
    real_theme = mock.create_autospec(Theme, name="real_theme")
    real_theme.parents = ['parent']
    real_theme.lookup.return_value = None
    parent_theme = mock.create_autospec(Theme, name="parent_theme")
    parent_theme.lookup.return_value = None
    hicolor = mock.create_autospec(Theme, name="hicolor")
    hicolor.lookup.return_value = mock.MagicMock()

    _stub_get_theme(get_theme, Adwaita=real_theme, parent=parent_theme, hicolor=hicolor)

    path = lookup("org.mozilla.firefox", "Adwaita")
    assert get_theme.mock_calls == [mock.call('Adwaita'), mock.call('parent'), mock.call('hicolor')]
    assert path is hicolor.lookup.return_value


@mock.patch("freedesktop_icons.get_theme", autospec=True)
@mock.patch("freedesktop_icons.lookup_fallback", autospec=True)
def test_lookup_in_fallback(lookup_fallback, get_theme):
    real_theme = mock.create_autospec(Theme, name="real_theme")
    real_theme.lookup.return_value = None
    hicolor = mock.create_autospec(Theme, name="hicolor")
    hicolor.lookup.return_value = None

    _stub_get_theme(get_theme, Adwaita=real_theme, hicolor=hicolor)

    lookup_fallback.return_value = mock.MagicMock()

    path = lookup("org.mozilla.firefox", "Adwaita")
    assert get_theme.mock_calls == [mock.call('Adwaita'), mock.call('hicolor')]
    assert lookup_fallback.mock_calls == [mock.call('org.mozilla.firefox', ['svg', 'png', 'xpm'])]
    assert path is lookup_fallback.return_value


@mock.patch("freedesktop_icons.fallback_paths")
def test_lookup_fallback(fallback_paths, tmpdir):
    file = tmpdir / 'org.mozilla.firefox.svg'
    file.open('w').close()

    fallback_paths.return_value = [tmpdir]

    assert lookup_fallback("not-there", ['svg']) is None
    assert lookup_fallback("org.mozilla.firefox", ['png']) is None
    assert lookup_fallback("org.mozilla.firefox", ['svg']) == file
