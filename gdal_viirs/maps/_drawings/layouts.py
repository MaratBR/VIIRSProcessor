from .drawings import *
from .types import Origin, Alignment, VerticalAlignment, HorizontalAlignment
from typing import *


T = TypeVar('T')


class LinearLayout(Generic[T]):
    def __init__(self, ax, xy, *, content_alignment: T = HorizontalAlignment.CENTER, origin=None,
                 is_reversed=False):
        self._ax = ax
        self._content_alignment = content_alignment
        self._xy_begin = xy
        self._origin = origin or Origin.BOTTOM_LEFT
        self._reversed = is_reversed
        self._offset = 0
        self._spacing = 0

    def set_spacing(self, inches):
        self._spacing = inches
        return self

    @property
    def _xy(self):
        diff = -self._offset if self._reversed else self._offset
        if self._is_horizontal:
            return self._xy_begin[0] + diff, self._xy_begin[1]
        else:
            return self._xy_begin[0], self._xy_begin[1] + diff

    @property
    def _is_horizontal(self):
        return isinstance(self._content_alignment, VerticalAlignment)

    def _get_align(self, content_alignment):
        if self._is_horizontal:
            return Alignment(
                ver=content_alignment or self._content_alignment,
                hor=HorizontalAlignment.RIGHT if self._reversed else HorizontalAlignment.LEFT
            )
        else:
            return Alignment(
                ver=VerticalAlignment.BOTTOM if self._reversed else VerticalAlignment.TOP,
                hor=content_alignment or self._content_alignment
            )

    def text(self, text, max_size=None, content_alignment=None, **kwargs):
        self._add_box(
            draw_text(text, self._xy, self._ax, max_size=max_size, origin=self._origin,
                      align=self._get_align(content_alignment), **kwargs)
        )
        return self

    def spacing(self, inches):
        self._offset += inches
        return self

    def legend(self, content_alignment=None, max_width=None, max_height=None, **kwargs):
        self._add_box(
            draw_legend(self._ax, self._xy, origin=self._origin, max_width=max_width, max_height=max_height,
                        align=self._get_align(content_alignment), **kwargs)
        )
        return self

    def _add_box(self, size, no_spacing=False):
        w, h = size
        if self._is_horizontal:
            self._offset += w
        else:
            self._offset += h
        self._offset += self._spacing
