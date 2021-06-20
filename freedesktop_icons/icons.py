from enum import Enum


class Type(str, Enum):
    FIXED = "fixed"
    SCALABLE = "scalable"
    THRESHOLD = "threshold"
