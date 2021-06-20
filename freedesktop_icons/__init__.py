"""**freedesktop-icons**

Find icon paths according to the freedesktop icon theme specification.
"""

import os
from collections.abc import Iterator, Sequence
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:  # pragma: no cover
    from .icons import Icon
    from .theme import Theme


def __getattr__(name):  # pragma: no cover
    if name == "__version__":
        # Lazy load the version only if someone asks for it
        from importlib import metadata

        try:
            __version__ = metadata.version("freedesktop-icons")
        except metadata.PackageNotFoundError:
            __version__ = "0.0.0dev0"
        globals()["__version__"] = __version__
        return __version__
    if name == "Icon":
        from .icons import Icon

        globals()["Icon"] = Icon
    if name == "Theme":
        from .theme import Theme

        globals()["Theme"] = Theme

    raise AttributeError(f"module {__name__} has no attribute {name}")


@cache
def get_theme(name: str) -> "Theme":  # pragma: no cover
    from .theme import Theme

    return Theme(name)


def lookup(icon: Union[str, "Icon"], themename: str, extensions: Sequence[str] = ["svg", "png", "xpm"]) -> "Path | None":  # noqa: B006
    """
    Lookup the specified icon in the theme and it's parents, returning the best match.

    If the theme doesn't have this icon then the ``hicolor` theme is searched, and finally an icon is searched for in ``/usr/share/pixmaps``.

    For simple cases the icon name can be passed, but for more complex
    filtering (such as using an icon in a particular size) an instance of
    :py:class:`~icons.Icon` should be passed:

    Example
    -------

    .. code-block:: python

        from freedesktop_icons import lookup

        lookup("org.mozilla.firefox", "Adwaita")

    or if you know you are going to use this in a specific size and want the closest one:

    .. code-block:: python

        from freedesktop_icons import lookup, Icon

        lookup(Icon("org.mozilla.firefox", size=72), "Adwaita")


    Args:
        icon: icon name or object to search for
        themename: name of theme to start searching in
        extensions: List of file extensions to search for
    Returns:
        path to best matching icon, or None
    """
    from .icons import Icon

    if isinstance(icon, str):
        icon = Icon(icon)

    theme = get_theme(themename)

    if file := theme.lookup(icon, extensions):
        return file

    for parent in theme.parents:
        theme = get_theme(parent)

        if file := theme.lookup(icon, extensions):
            return file

    theme = get_theme("hicolor")

    if file := theme.lookup(icon, extensions):
        return file

    return lookup_fallback(icon.name, extensions)


def lookup_fallback(icon_name: str, extensions: Sequence[str]):
    for dir in fallback_paths():
        for extension in extensions:
            file = dir / f'{icon_name}.{extension}'
            if file.exists():
                return file


def theme_search_dirs() -> Iterator[Path]:
    """
    Return list of folders to search for themes in.

    This is ``$HOME/.icons`` (for backwards compatibility), and then in exach directory in ``$XDG_DATA_DIRS/icons``.

    Directories are not checked for existence.
    """
    # https://specifications.freedesktop.org/icon-theme-spec/icon-theme-spec-latest.html#directory_layout
    yield Path.home() / '.icons'
    for dir in os.environ.get('XDG_DATA_DIRS', '').split(':'):
        if not dir:
            continue
        yield Path(dir) / 'icons'


def fallback_paths() -> Iterator[Path]:  # pragma: no cover
    yield Path('/usr/share/pixmaps')
