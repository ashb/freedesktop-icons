import pathlib

import pytest

from freedesktop_icons.cache import GtkIconCache


@pytest.fixture(scope='module')
def cache():
    path = pathlib.Path(__file__).parent / "data" / "test-theme"
    return GtkIconCache(path)


def test_lookup(cache):
    assert cache.header.version == (1, 0)
    assert list(cache.lookup("button-open")) == ['16x16/actions']


def test_lookup_not_found(cache):
    assert list(cache.lookup("not-found")) == []
