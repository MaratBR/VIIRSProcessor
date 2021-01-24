__all__ = (
    'BOTTOM',
    'TOP',
    'LEFT',
    'RIGHT',
    'BOTTOM_LEFT',
    'BOTTOM_RIGHT',
    'TOP_LEFT',
    'TOP_RIGHT',
    'VCENTER',
    'HCENTER'
)

from .types import *

BOTTOM_LEFT: Origin = Origin.BOTTOM_LEFT
BOTTOM_RIGHT: Origin = Origin.BOTTOM_RIGHT
TOP_LEFT: Origin = Origin.TOP_LEFT
TOP_RIGHT: Origin = Origin.TOP_RIGHT

LEFT: HorizontalAlignment = HorizontalAlignment.LEFT
RIGHT: HorizontalAlignment = HorizontalAlignment.RIGHT
TOP: VerticalAlignment = VerticalAlignment.TOP
BOTTOM: VerticalAlignment = VerticalAlignment.BOTTOM

VCENTER = VerticalAlignment.CENTER
HCENTER = HorizontalAlignment.CENTER
