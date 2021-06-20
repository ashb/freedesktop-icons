import configparser
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Optional

import attr
from attr.converters import pipe

from . import icons


@attr.define
class Theme:
    theme_dir: Path = attr.ib(converter=Path)
    config: Optional[configparser.ConfigParser] = attr.ib(
        default=attr.Factory(lambda self: self._load_config(), takes_self=True),
        repr=False,
    )
    subdirs: Mapping[str, "ThemeDirectory"] = attr.ib(
        default=attr.Factory(lambda self: self.ThemeDirs(self.config), takes_self=True),
        repr=False,
    )

    def _load_config(self) -> Optional[configparser.ConfigParser]:
        config = configparser.ConfigParser(interpolation=None, strict=False)
        # Don't lowercase names
        config.optionxform = str  # type: ignore
        try:
            with (self.theme_dir / 'index.theme').open() as fh:
                config.read_file(fh)

                return config
        except FileNotFoundError:
            return None

    def _all_icon_dirs(self):
        # filter(None,) because some themes have a trailing , which we want to exclude!
        yield from map(str.strip, filter(None, self.config['Icon Theme']['Directories'].split(',')))

    @attr.define(repr=False, hash=True)
    class ThemeDirs:
        """
        Helper
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
    :meta: private
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
    min_size: Optional[int] = attr.ib(converter=attr.converters.optional(int), default=None)
    max_size: Optional[int] = attr.ib(converter=attr.converters.optional(int), default=None)
