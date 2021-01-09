SIBERIA_CITIES = [
    (84.948197, 56.484680, 'Томск'),
    (73.368212, 54.989342, 'Омск'),
    (86.087314, 55.354968, 'Кемерово'),
    (82.933952, 55.018803, 'Новосибирск')
]


def add_points(builder, points):
    for p in points:
        builder.add_point(*p)