from enum import Enum
from typing import Optional

import attr


class Type(str, Enum):
    """
    Enum of the possible types of icon
    """

    FIXED = "fixed"
    SCALABLE = "scalable"
    THRESHOLD = "threshold"


@attr.define
class Icon:
    """
    An Icon to lookup.

    Only name is required, everything else is optional, but can be used to
    control what is searched for.
    """

    name: str
    size: Optional[int] = None
    context: Optional[str] = attr.ib(
        converter=attr.converters.optional(str.lower),  # type: ignore
        default=None,
    )
    type: Optional[Type] = None
    scale: int = 1
    threshold: int = 2
