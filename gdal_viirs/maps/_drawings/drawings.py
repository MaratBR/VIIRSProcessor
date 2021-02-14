import io
from functools import partial
import enum
import numpy as np
from PIL import Image
from matplotlib import offsetbox, image, patches, pyplot
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.transforms import Bbox

from .types import *

__all__ = (
    'inches2axes',
    'draw_text',
    'draw_legend',
    'draw_image',
    'draw_rect_with_outside_border',
    'apply_origin',
    'get_axes_area'
)


def _mkfig(**kwargs):
    # TODO понять, почему данная функция иногда
    f = pyplot.figure(**kwargs)
    ax = f.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    return f, ax


def _mkimg(f: Figure, savefig_kw=None, crop=None):
    savefig_kw = savefig_kw or {}
    if crop:
        if isinstance(crop, Artist):
            f.canvas.draw()
            crop = crop.get_window_extent(f._cachedRenderer).transformed(f.dpi_scale_trans.inverted())

        if not isinstance(crop, Bbox):
            raise TypeError('crop должен быть экземпляром Bbox')
        savefig_kw['bbox_inches'] = crop

    buf = io.BytesIO()
    f.savefig(buf, format='png', transparent=True, **savefig_kw)
    buf.seek(0)
    im = Image.open(buf, formats=['PNG'])
    data = np.fromstring(im.tobytes(), dtype=np.uint8)
    data = data.reshape((im.size[1], im.size[0], 4))
    buf.close()
    return data


def inches2axes(ax, xy):
    if isinstance(ax, Figure):
        transform = ax.transFigure
        fig = ax
    else:
        transform = ax.transAxes
        fig = ax.figure
    xy = fig.dpi_scale_trans.transform(xy)
    xy = transform.inverted().transform(xy)
    return tuple(xy)


def apply_origin(fig, xy, origin: Origin, w, h, align: Alignment):
    figw, figh = fig.get_size_inches()
    if origin.is_top:
        # координаты начинаются сверху, а не снизу
        xy = xy[0], figh - xy[1]

    if origin.is_right:
        xy = figw - xy[0], xy[1]

    if align is None:
        align = origin.to_alignment()

    if align.ver == VerticalAlignment.TOP:
        # координаты начинаются сверху, а не снизу
        xy = xy[0], xy[1] - h
    elif align.ver == VerticalAlignment.CENTER:
        xy = xy[0], xy[1] - h / 2

    if align.hor == HorizontalAlignment.RIGHT:
        xy = xy[0] - w, xy[1]
    elif align.hor == HorizontalAlignment.CENTER:
        xy = xy[0] - w / 2, xy[1]

    return xy


def draw_image(img, xy, ax, *, max_width=None,
               max_height=None,
               origin=Origin.BOTTOM_LEFT,
               align=None) -> Tuple[float, float]:
    if not isinstance(img, np.ndarray):
        img = image.imread(img)
    dpi = ax.figure.dpi
    w, h = img.shape[1] / dpi, img.shape[0] / dpi
    zoom = 1
    if max_width is not None:
        zoom = min(zoom, max_width / w)
    if max_height is not None:
        zoom = min(zoom, max_height / h)
    w *= zoom
    h *= zoom
    axImg = get_axes_area(ax.figure, xy, w, h, origin, align)
    axImg.set_axis_off()
    axImg.imshow(img)
    return w, h


def _draw_text_as_image(text, size=None, **kwargs) -> Tuple[np.ndarray, Tuple[float, float]]:
    """
    Рисует текст как изображение с указанием максимального размера текста.
    Если текст выходит за границу, он будет обрезан.

    :param text: текс
    :param size: кортеж вида (w, h) - максимальный размер текста
    :param kwargs: любые аргументы, которые будут переданы в Axes.text
    :return: numpy массив (изображение)
    """
    ha = kwargs.get('ha', kwargs.get('horizontalalignment', 'left'))
    va = kwargs.get('va', kwargs.get('verticalalignment', 'bottom'))
    x, y = 0, 0

    if va == 'center':
        y = .5
    elif va == 'top':
        y = .9999

    if ha == 'center':
        x = .5
    elif ha == 'right':
        x = 1

    f, ax = _mkfig(figsize=size)
    text = ax.text(x, y, text, **kwargs)
    crop = text if size is None else None
    data = _mkimg(f, crop=crop)
    size = data.shape[1] / ax.figure.dpi, data.shape[0] / ax.figure.dpi
    pyplot.close(f)
    return data, size


def draw_text(text, xy, ax, max_size=None, origin=None, align=None, **kw):
    im, size = _draw_text_as_image(text, max_size, **kw)
    if align is None:
        ha = kw.get('horizontalalignment', kw.get('ha', 'left'))
        va = kw.get('verticalalignment', kw.get('va', 'bottom'))
        align = Alignment.from_ha_va(ha, va)

    draw_image(im, xy, ax, origin=origin, align=align)
    return size


def get_axes_area(fig, xy, w, h, origin=Origin.BOTTOM_LEFT, align=None):
    xy = apply_origin(fig, xy, origin or Origin.BOTTOM_LEFT, w, h, align)
    xy = inches2axes(fig, xy)
    w, h = inches2axes(fig, (w, h))
    return fig.add_axes([*xy, w, h], label=f'{xy[0]}_{xy[1]}_{w}_{h}')


def draw_rect_with_outside_border(ax, xy, w, h):
    xy = inches2axes(ax, xy)
    w, h = inches2axes(ax, (w, h))
    frame = patches.Rectangle(xy, w, h, facecolor='none')
    offbox = offsetbox.AuxTransformBox(ax.transData)
    offbox.add_artist(frame)
    ab = offsetbox.AnnotationBbox(offbox,
                                  (xy[0] + w / 2., xy[1] + h / 2.),
                                  boxcoords="data", pad=0.52, fontsize=2,
                                  bboxprops=dict(fc="none", ec='k', lw=2))
    ax.add_artist(ab)


def _draw_legend_as_image(**kwargs):
    f, ax = _mkfig()
    kwargs['loc'] = (0, 0)
    legend = ax.legend(**kwargs)
    f.canvas.draw()
    bbox = legend.get_window_extent().transformed(f.dpi_scale_trans.inverted())
    data = _mkimg(f, savefig_kw={'bbox_inches': bbox})
    pyplot.close(f)
    return data


def draw_legend(ax, xy, origin=Origin.BOTTOM_LEFT, max_width=None, max_height=None, align=None,
                **kwargs):
    kwargs['loc'] = 'upper right'
    img = _draw_legend_as_image(**kwargs)
    size = draw_image(img, xy, ax, max_width=max_width, max_height=max_height, origin=origin, align=align)
    return size
