import os
__BASE_DIR = os.path.dirname(__file__)


def __resource(path):
    return os.path.join(__BASE_DIR, 'required_resources', path)


# по умолчанию 1000
SCALE = 2000
LOGO_PATH = __resource('logo.png')
ISO_QUALITY_SIGN = __resource('iso_sign.jpg')
IS_DEBUG = True

# конфигурация PNG файлов, где
# name - уникальный идентификатор изображения
# display_name - имя, которое будет размещено на изображении
# xlim и ylim - массив с 2 элементами (предел по X и Y в проекции)
PNG_CONFIG = [
    {
        'name': 'novosibirsk',
        'display_name': 'Новосибирская область',
        'xlim': (-300000, 350000),
        'ylim': (-280000, 240000),
        'mask_shapefile': __resource('novosib/novosib_agro.shp')
    },
    {
        'name': 'altai',
        'display_name': 'Алтайский край',
        'xlim': (-155000, 490000),
        'ylim': (-690000, -100000),
        'mask_shapefile': __resource('altai/altkrai_agro.shp')
    },
    {
        'name': 'omsk',
        'display_name': 'Омская область',
        'xlim': (-700000, -150000),
        'ylim': (-300000, 390000),
        'mask_shapefile': __resource('omsk/omsk_agro.shp')
    },
    {
        'name': 'kemerovo',
        'display_name': 'Кемеровская область',
        'xlim': (255000, 615000),
        'ylim': (-350000, 200000),
        'mask_shapefile': __resource('kemerovo/kem_agro.shp')
    },
    {
        'name': 'krasnoyarsk',
        'display_name': 'Красноярский край',
        'xlim': (525000, 1090000),
        'ylim': (-345000, 370000),
        'mask_shapefile': __resource('krasnoyarsk/krasn_agro.shp')
    },
    {
        'name': 'region',
        'display_name': '',
        'xlim': (-606000, 612000),
        'ylim': (-575000, 317000),
        'mask_shapefile': os.path.join(__BASE_DIR, 'required_resources/region/region_agro.shp')
    }
]

# входые данные и папка с выходными

OUTPUTS = {
    'ndvi': '~/Documents/viirs/processed/products',
    '': '',
    'processed_data': '~/Documents/viirs/processed/data'
}

INPUTS = {
    'data': '/media/marat/Quack/Projects/GDAL_Data/NPP/'
}

FONT_FAMILY = '/home/marat/Downloads/Agro/Font/times.ttf'

# дополнительный точки на карте (Томск уже есть по-умолчанию и показан просто как пример)
# MAP_POINTS = [
#     (84.948197, 56.484680, 'Томск')
# ]

# папка с БД файлом
# CONFIG_DIR = ''
