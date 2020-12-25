import cartopy

from gdal_viirs.maps.builder import MapBuilder


class NovosibirskMapBuilder(MapBuilder):
    def __init__(self):
        super(NovosibirskMapBuilder, self).__init__()
        self.xlim = -1500000, 2100000
        self.ylim = 800000, 3000000

        self.add_point(84.948197, 56.484680, 'Томск')
        self.add_point(73.368212, 54.989342, 'Омск')
        self.add_point(86.087314, 55.354968, 'Кемерово')
        self.add_point(82.933952, 55.018803, 'Новосибирск')

    def get_projection(self, file):
        return cartopy.crs.LambertConformal(standard_parallels=(67.41206675, 43.58046825), central_longitude=79.950619)