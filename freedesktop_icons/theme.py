import configparser
import sys
from collections.abc import Iterator, Mapping, Sequence
from functools import cache
from pathlib import Path
from typing import Optional

import attr
from attr.converters import pipe

from . import icons, theme_search_dirs
from .cache import GtkIconCache
from .slots import slotted_cached_property


@attr.define(hash=True)
class Theme:
    """
    Information about a given FreeDesktop icon theme.

    If just given a name (the only required argument) argument then the ``index.theme`` file will be searched for in
    :py:func:`~freedesktop_icons.theme_search_dirs`
    """

    name: str
    theme_dir: Path = attr.ib(converter=attr.converters.optional(Path), default=None)
    """Override the search paths and only look in this specific folder"""
    config: configparser.ConfigParser = attr.ib(
        default=attr.Factory(lambda self: self._load_config(), takes_self=True),
        repr=False,
        init=False,
        hash=False,
    )
    subdirs: Mapping[str, "ThemeDirectory"] = attr.ib(
        default=attr.Factory(lambda self: self.ThemeDirs(self.config), takes_self=True),
        repr=False,
        hash=False,
    )

    @property
    def parents(self) -> Iterator[str]:
        """Name of themes this one inherits from"""
        for parent in self._config_list('Inherits'):
            if parent != 'hicolor':
                yield parent

    def _load_config(self) -> Optional[configparser.ConfigParser]:
        config = configparser.ConfigParser(interpolation=None, strict=False)
        # Don't lowercase names
        config.optionxform = str  # type: ignore

        # > In at least one of the theme directories there must be a file
        # > called index.theme that describes the theme. The first index.theme
        # > found while searching the base directories in order is used
        for dir in self._possible_theme_dirs():
            try:
                with (dir / 'index.theme').open() as fh:
                    config.read_file(fh)

                    return config
            except FileNotFoundError:
                pass
        return None

    def _all_icon_dirs(self) -> Iterator[str]:
        yield from self._config_list('Directories')

    def _config_list(self, name: str):
        if not self.config:
            return
        # filter(None,) because some themes have a trailing , which we want to exclude!
        yield from map(str.strip, filter(None, self.config['Icon Theme'][name].split(',')))

    def _possible_theme_dirs(self) -> Iterator[Path]:
        if self.theme_dir:
            yield self.theme_dir
        else:
            for dir in theme_search_dirs():
                yield dir / self.name

    @slotted_cached_property
    def icon_cache(self) -> Optional[GtkIconCache]:
        # index.cache could be in _any_ of the possible theme dirs!

        for dir in self._possible_theme_dirs():
            try:
                return GtkIconCache(dir)
            except FileNotFoundError:
                pass
        return None

    def lookup(self, icon: icons.Icon, exts: Sequence[str]) -> "Path | None":
        """
        Lookup the best matching icon in this theme.

        If there is an exact match, use that, else find the closest sized image

        Args:
            exts: List of file extensions to search for
        """
        if file := self.lookup_exact(icon, exts):
            return file
        if file := self.lookup_closest(icon, exts):
            return file
        return None

    def lookup_exact(self, icon: icons.Icon, exts: Sequence[str]) -> "Path | None":
        """
        Lookup an icon that matches exactly

        Args:
            exts: List of file extensions to search for
        Returns:
            Path object of matching icon
        """
        if self.icon_cache is not None:
            dirs: Iterator[str] = self.icon_cache.lookup(icon.name)
        else:
            dirs = self._all_icon_dirs()

        for dirname in dirs:
            dir = self.subdirs[dirname]
            if not dir.matches_icon(icon):
                continue

            for search_dir in self._possible_theme_dirs():
                search_dir /= dirname
                for ext in exts:
                    file = search_dir / f'{icon.name}.{ext}'
                    if file.exists():
                        return file
        return None

    def lookup_closest(self, icon: icons.Icon, exts) -> "Path | None":
        """
        Find the icon that closest matches the requested size.

        Args:
            exts: List of file extensions to search for
        Returns:
            Path object of closest matching icon
        """
        closest = None
        minimal_size = sys.maxsize

        if self.icon_cache is not None:
            dirs = self.icon_cache.lookup(icon.name)
        else:
            dirs = self._all_icon_dirs()

        for dirname in dirs:
            theme_dir = self.subdirs[dirname]

            for search_dir in self._possible_theme_dirs():
                search_dir /= dirname
                for ext in exts:
                    file = search_dir / f'{icon.name}.{ext}'
                    if (diff := theme_dir.size_diff(icon)) is not None and diff < minimal_size and file.exists():
                        closest = file
                        minimal_size = diff
        return closest

    @attr.define(repr=False, hash=True)
    class ThemeDirs:
        """
        Helper that creates ThemeDirectory objects on first access

        :meta private:
        """

        config: configparser.ConfigParser = attr.ib(hash=False)

        def __contains__(self, name):
            return self.config.has_section(name)

        @cache
        def __getitem__(self, name):
            section = self.config[name]
            return ThemeDirectory(
                name=name,
                size=section['Size'],
                context=section.get('Context'),
                type=section.get('Type'),
                min_size=section.get('MinSize'),
                max_size=section.get('MaxSize'),
                threshold=section.get('Threshold'),
                scale=section.get('Scale'),
            )


@attr.define
class ThemeDirectory:
    """
    :meta private:
    """

    name: str
    size: int = attr.ib(converter=int)
    context: str = attr.ib(
        converter=attr.converters.optional(str.lower),  # type: ignore
        default=None,
    )
    type: icons.Type = attr.ib(
        converter=pipe(  # type: ignore
            attr.converters.optional(str.lower),
            attr.converters.optional(icons.Type),
        ),
        default=icons.Type.THRESHOLD,
    )
    scale: int = attr.ib(converter=pipe(attr.converters.default_if_none(1), int), default=None)  # type: ignore
    threshold: int = attr.ib(converter=pipe(attr.converters.default_if_none(2), int), default=None)  # type: ignore
    min_size: int = attr.ib(converter=attr.converters.optional(int), default=None)
    max_size: int = attr.ib(converter=attr.converters.optional(int), default=None)

    def __attrs_post_init__(self):
        # Spec: Defaults to the value of Size if not present
        if self.min_size is None:
            self.min_size = self.size
        if self.max_size is None:
            self.max_size = self.size

    def matches_icon(self, icon: "icons.Icon") -> bool:
        if icon.type and icon.type != self.type or icon.context and icon.context != self.context or icon.scale != self.scale:
            return False

        if not icon.size:
            return True

        if self.type == icons.Type.FIXED:
            return icon.size == self.size
        if self.type == icons.Type.SCALABLE:
            return icon.size >= self.min_size and icon.size <= self.max_size
        # Threshold
        return icon.size >= self.size - self.threshold and icon.size <= self.size + self.threshold

    def size_diff(self, icon: "icons.Icon") -> Optional[int]:

        if icon.type and icon.type != self.type or icon.context and icon.context != self.context or icon.size is None:
            return None

        size = icon.size * icon.scale

        if self.type == icons.Type.FIXED:
            return abs(self.size * self.scale - size)

        if self.type == icons.Type.SCALABLE:
            if size < self.min_size * self.scale:
                return self.min_size * self.scale - size
            if size > self.max_size * self.scale:
                return size - self.max_size * self.scale
            return 0
        # Threshold
        if size < (self.size - self.threshold) * self.scale:
            return self.min_size * self.scale - size
        if size > (self.size + self.threshold) * self.scale:
            return size - self.max_size * self.scale
        return 0
