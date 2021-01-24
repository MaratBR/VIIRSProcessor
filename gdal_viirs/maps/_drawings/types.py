import enum
from typing import Tuple, NamedTuple


class Origin(enum.Enum):
    _TOP = 1
    _RIGHT = 2

    BOTTOM_LEFT = 0
    BOTTOM_RIGHT = 2
    TOP_LEFT = 1
    TOP_RIGHT = 3

    @property
    def is_top(self):
        return bool(self.value & Origin._TOP.value)

    @property
    def is_bottom(self):
        return not self.is_top

    @property
    def is_right(self):
        return bool(self.value & Origin._RIGHT.value)

    @property
    def is_left(self):
        return not self.is_right

    def to_alignment(self):
        return Alignment(
            hor=HorizontalAlignment.RIGHT if self.is_right else HorizontalAlignment.LEFT,
            ver=VerticalAlignment.TOP if self.is_top else VerticalAlignment.BOTTOM,
        )


class HorizontalAlignment(enum.Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


class VerticalAlignment(enum.Enum):
    TOP = 0
    CENTER = 1
    BOTTOM = 2


class Alignment(NamedTuple):
    hor: HorizontalAlignment
    ver: VerticalAlignment

    @classmethod
    def from_ha_va(cls, ha, va):
        if ha == 'right':
            ha = HorizontalAlignment.RIGHT
        elif ha == 'center':
            ha = HorizontalAlignment.CENTER
        else:
            ha = HorizontalAlignment.LEFT

        if va == 'top':
            va = VerticalAlignment.TOP
        elif va == 'center':
            va = VerticalAlignment.CENTER
        else:
            va = VerticalAlignment.BOTTOM

        return cls(hor=ha, ver=va)
