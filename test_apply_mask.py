from gdal_viirs.utility import apply_mask
import numpy as np
from matplotlib import pyplot
from matplotlib.patches import Rectangle

plt, ax = pyplot.subplots(figsize=(4, 4))
ax.set_xlim((0, 20))
ax.set_ylim((0, 20))

scalex, scaley = -1, -1

x1, y1 = 8, 8
w1, h1 = 3, 4

x2, y2 = 10, 10
w2, h2 = 3, 4

rect1 = Rectangle((x1, y1), w1 * scalex, h1 * scaley, ec='red', fc='none', lw=3)
rect2 = Rectangle((x2, y2), w2 * scalex, h2 * scaley, ec='blue', fc='none', lw=3)

ax.add_patch(rect1)
ax.add_patch(rect2)

ax.plot(x1, y1, marker='o', color='k')
ax.plot(x2, y2, marker='s', color='k')

left1 = max(0.0, x2 - x1)
left2 = max(0.0, x1 - x2)

right1 = max(0.0, x1 + w1 * abs(scalex) - x2 - w2 * abs(scalex))
right2 = max(0.0, x2 + w2 * abs(scalex) - x1 - w1 * abs(scalex))

top1 = max(0.0, y1 + h1 * abs(scalex) - y2 - h2 * abs(scaley))
top2 = max(0.0, y2 + h2 * abs(scalex) - y1 - h1 * abs(scalex))

bottom1 = max(0.0, y2 - y1)
bottom2 = max(0.0, y1 - y2)

ax.plot(*p1, marker='o', color='green')
ax.plot(*p2, marker='o', color='green')


plt.show()
