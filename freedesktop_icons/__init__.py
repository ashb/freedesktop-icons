"""**freedesktop-icons**

Find icon paths according to the freedesktop icon theme specification.
"""


def __getattr__(name):
    if name == "__version__":
        # Lazy load the version only if someone asks for it
        from importlib import metadata

        try:
            __version__ = metadata.version("freedesktop-icons")
        except metadata.PackageNotFoundError:
            __version__ = "0.0.0dev0"
        globals()["__version__"] = __version__
        return __version__

    raise AttributeError(f"module {__name__} has no attribute {name}")
