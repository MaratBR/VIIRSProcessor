import numpy
from matplotlib import offsetbox, image, patches
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
    if not isinstance(img, numpy.ndarray):
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


def draw_text(text, xy, ax, invert_y=False, **kw):
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