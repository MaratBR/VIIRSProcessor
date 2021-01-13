import io

import numpy as np
from PIL import Image
from matplotlib import offsetbox, image, patches, pyplot
from matplotlib.figure import Figure


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

_TOP = 1
_RIGHT = 2

TOP_LEFT = _TOP
TOP_RIGHT = _TOP | _RIGHT
BOTTOM_LEFT = 0
BOTTOM_RIGHT = _RIGHT


def apply_origin(fig, xy, origin, w, h, area_origin):
    figw, figh = fig.get_size_inches()
    if origin & _TOP:
        # координаты начинаются сверху, а не снизу
        xy = xy[0], figh - xy[1]
    if origin & _RIGHT:
        xy = figw - xy[0], xy[1]

    if area_origin is None:
        area_origin = origin

    if area_origin & _TOP:
        # координаты начинаются сверху, а не снизу
        xy = xy[0], xy[1] - h
    if area_origin & _RIGHT:
        xy = xy[0] - w, xy[1]

    return xy


def draw_image(img, xy, ax, *, max_width=None, max_height=None, origin=BOTTOM_LEFT, area_origin=None):
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
    axImg = get_axes_area(ax.figure, xy, w, h, origin, area_origin)
    axImg.set_axis_off()
    axImg.imshow(img)


def _draw_text_as_image(text, size, **kwargs):
    ha = kwargs.get('ha', kwargs.get('horizontalalignment', 'left'))
    va = kwargs.get('va', kwargs.get('verticalalignment', 'bottom'))
    x, y = .00001, .00001
    if va =='center':
        y = .5
    elif va == 'top':
        y = .99999

    if ha == 'center':
        x = .5
    elif ha == 'right':
        x = .99999

    f = pyplot.figure(figsize=size)
    ax = f.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.text(x, y, text, **kwargs)
    buf = io.BytesIO()
    f.savefig(buf, format='png', transparent=True)
    buf.seek(0)
    pyplot.close(f)
    im = Image.open(buf, formats=['PNG'])

    data = np.fromstring(im.tobytes(), dtype=np.uint8)
    data = data.reshape((im.size[1], im.size[0], 4))
    buf.close()
    return data


def draw_text(text, xy, ax, max_size=None, invert_y=False, **kw):
    if max_size:
        im = _draw_text_as_image(text, max_size, **kw)
        ha = kw.get('ha', kw.get('horizontalalignment', 'left'))
        va = kw.get('va', kw.get('verticalalignment', 'bottom'))
        if ha == 'center':
            xy = xy[0] - max_size[0] / 2, xy[1]
        elif ha == 'right':
            xy = xy[0] - max_size[0], xy[1]

        if va == 'top':
            if not invert_y:
                xy = xy[0], xy[1] - max_size[1]
        elif va == 'center':
            xy = xy[0], xy[1] + (-max_size[1] if invert_y else max_size[1]) / 2

        draw_image(im, xy, ax, origin=TOP_LEFT if invert_y else BOTTOM_LEFT)
    else:
        xy = inches2axes(ax, xy)
        if invert_y:
            xy = xy[0], 1 - xy[1]
        return ax.text(xy[0], xy[1], text, **kw)
        #txt._get_wrap_line_width = lambda: wrapping_width


def get_axes_area(fig, xy, w, h, origin=BOTTOM_LEFT, area_origin=None):
    xy = apply_origin(fig, xy, origin, w, h, area_origin)
    xy = inches2axes(fig, xy)
    w, h = inches2axes(fig, (w, h))
    return fig.add_axes([*xy, w, h])


def draw_rect_with_outside_border(xy, w, h, ax):
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