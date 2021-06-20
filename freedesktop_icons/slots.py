from functools import cache


def slotted_cached_property(user_function):
    """
    Cached property for slotted classes.

    :method:`functools.cached_property` doesn't work on slotted-classes, and
    mypy complains about using additional decorators in ``@property``.
    """
    return property(cache(user_function))  # type: ignore
