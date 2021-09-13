import os

from gdal_viirs.config import req_resource_path as __resource_path

__BASE_DIR = os.path.dirname(__file__)


def __resource(res):
    """
    Возвращает путь до ресурса, который находится в папке ресурсов (required_resources)
    :param res:
    :return:
    """
    return str(__resource_path(res))


# import datetime
# SKIP_FILES_BEFORE = datetime.datetime(year=2021, month=8, day=5)

# сколько дней приходит на один композит NDVI
# например, если поставить 3 дня то прога будет каждый день
# делать композит за последние 3 дня
NDVI_MERGE_PERIOD_IN_DAYS = 4

# сколько дней должно пройти между началом одного композита и концом другого
# значение по умолчанию в 2 раза больше, чем NDVI_MERGE_PERIOD_IN_DAYS, поэтому
# менять это значение лучше не стоит
# NDVI_DYNAMICS_PERIOD = NDVI_MERGE_PERIOD_IN_DAYS * 2

# Если True будет генерировать проекцию с облачностью,
# даже если она уже сгенерирована (по-умолчанию False)
FORCE_CLOUD_MASK_PROCESSING = False

# Если True динамика NDVI будет пересчитана, каждый раз когда программа запускается
FORCE_NDVI_DYNAMICS_PROCESSING = True

# Если True композит NDVI будет пересоздаваться, каждый раз, когда
# программа запускается
FORCE_NDVI_COMPOSITE_PROCESSING = True

# Если True карты будут пересоздаваться, даже если уни уже были созданы
FORCE_MAPS_REGENERATION = True

# Если установить значение в True (по-умолчанию False) маска облачности будет сохраняться в /tmp
# в один и тот же файл, то есть каждый раз будет перезаписываться
SINGLE_CLOUD_MASK_FILE = False

# число на которуе будет умножен масштаб при подсчете
# не может быть меньше 1
SCALE_MULTIPLIER = 1

LOGO_PATH = __resource('logo.png')
ISO_QUALITY_SIGN = __resource('iso_sign.jpg')
IS_DEBUG = True


MAPS_FILENAME_PATTERN = {
    'ndvi': '{yymmdd}2359_{ka}_{ndvi}_{name}.png',
    'ndvi_dynamics': '{yymmdd}2359_{ka}_{ndvi_dynamics}_{name}.png'
}
MAPS_PARAMS = {
    'ka': 's',
    'ndvi_dynamics': 'd',
    'ndvi': 'c'
}

# дата обработки
# DATE_OFFSET = 0
# DATE = '22-02-2021'

# ширина и высота (по-умолчанию, горизонтальный макет)
WIDTH = 3500
HEIGHT = 2695

# градации значений на карте
GRADATIONS = {
    'default': __resource('Gradatsii_VIIRS_2021.csv'),
    'krasnoyarsk': __resource('Gradatsii_VIIRS_2021_Krasnoyarsk.csv')
}

# входые данные и папка с выходными
OUTPUTS = {
    'ndvi': '/mnt/100Tb/Suomi_NPP/Products_NEW/NDVI_maps',
    'ndvi_dynamics': '/mnt/100Tb/Suomi_NPP/Products_NEW/Dynamics_of_crops_ndvi_maps',
    'processed_data': '/mnt/100Tb/Suomi_NPP/Products_NEW/Processed_files_series'
}

INPUTS = {
    'data': '/mnt/100Tb/Suomi_NPP/Sources/output'
}

# КА заголовок
SPACECRAFT_NAME = 'KA Suomi NPP/VIIRS'

FONT_FAMILY = __resource('times.ttf')
STATES_BORDER_COLOR = '#a80000'
REGIONS_BORDER_COLOR = '#9c9c9c'

# region layers

__NSK_BORDER_LAYER = {
    'file': __resource('russia_adm/nsk_border.shp'),
    'lw': 3,
    'ec': STATES_BORDER_COLOR
}

__NSK_REGIONS_LAYER = {
    'file': __resource('russia_adm/nsk_admpol.shp'),
    'lw': 1,
    'ec': REGIONS_BORDER_COLOR
}

__OMSK_BORDER_LAYER = {
    'file': __resource('russia_adm/omsk_border.shp'),
    'lw': 3,
    'ec': STATES_BORDER_COLOR
}

__OMSK_REGIONS_LAYER = {
    'file': __resource('russia_adm/omsk_admpol.shp'),
    'lw': 1,
    'ec': REGIONS_BORDER_COLOR
}

__ALTKRAI_BORDER_LAYER = {
    'file': __resource('russia_adm/altkrai_border.shp'),
    'lw': 3,
    'ec': STATES_BORDER_COLOR
}

__ALTKRAI_REGIONS_LAYER = {
    'file': __resource('russia_adm/altkrai_admpol.shp'),
    'lw': 1,
    'ec': REGIONS_BORDER_COLOR
}

__KRASN_BORDER_LAYER = {
    'file': __resource('russia_adm/krasn_border.shp'),
    'lw': 3,
    'ec': STATES_BORDER_COLOR
}

__KRASN_GROUPS_BORDER_LAYER = {
    'file': __resource('russia_adm/krasn_groups_border.shp'),
    'lw': 3,
    'ec': REGIONS_BORDER_COLOR
}

__KRASN_REGIONS_LAYER = {
    'file': __resource('russia_adm/krasn_admpol.shp'),
    'lw': 1,
    'ec': REGIONS_BORDER_COLOR
}

__NSK_LAYERS = [
    __NSK_REGIONS_LAYER,
    __NSK_BORDER_LAYER
]

__KEM_REGIONS_LAYER = {
    'file': __resource('russia_adm/kem_admpol.shp'),
    'lw': 1,
    'ec': REGIONS_BORDER_COLOR
}

__KEM_BORDER_LAYER = {
    'file': __resource('russia_adm/kem_border.shp'),
    'lw': 3,
    'ec': STATES_BORDER_COLOR
}

__KEM_LAYERS = [
    __KEM_REGIONS_LAYER,
    __KEM_BORDER_LAYER
]

# endregion

# конфигурация PNG файлов, где
# name - уникальный идентификатор изображения
# display_name - имя, которое будет размещено на изображении
# xlim и ylim - массив с 2 элементами (предел по X и Y в проекции)
# points - точки, которые надо отметить на карте и их координаты (см. пример ниже)
PNG_CONFIG = [
    {
        'name': 'region',
        'display_name': 'Юг Западной Сибири',
        'xlim': (-613316.28569515, 602479.25968115),
        'ylim': (-545676.98683915, 416000),
        'mask_shapefile': __resource('maps/Region/region_agro.shp'),
        'water_shapefile': __resource('maps/Region/region_vodoem.shp'),
        'points': (
            (54.989342, 73.368212, 'Омск'),
            (53.348053, 83.779875, 'Барнаул'),
            (55.354968, 86.087314, 'Кемерово'),
            (55.030199, 82.920430, 'Новосибирск'),
        ),
        'layers': [
            __ALTKRAI_REGIONS_LAYER,
            __OMSK_REGIONS_LAYER,
            __NSK_REGIONS_LAYER,
            __KEM_REGIONS_LAYER,
            __ALTKRAI_BORDER_LAYER,
            __OMSK_BORDER_LAYER,
            __NSK_BORDER_LAYER,
            __KEM_BORDER_LAYER
        ]
    },
    {
        'name': 'altkrai',
        'display_name': 'Алтайский край',
        'xlim': (-149377.89400075, 492205.03323275),
        'ylim': (-536293.76858875, -85966.64381524999),
        'mask_shapefile': __resource('maps/Altai/altkrai_agro.shp'),
        'water_shapefile': __resource('maps/Altai/altkrai_vodoem.shp'),
        'points': (
            (53.348053, 83.779875, 'Барнаул'),
            (52.999369, 78.645913, 'Славгород'),
            (51.501235, 81.207774, 'Рубцовск'),
            (52.539308, 85.213829, 'Бийск'),
            (51.996094, 84.983959, 'Белокуриха'),
            (53.791470, 81.354603, 'Камень-на-Оби'),
        ),
        'layers': [
            __ALTKRAI_REGIONS_LAYER,
            __ALTKRAI_BORDER_LAYER
        ]
    },
    {
        'name': 'novosib',
        'display_name': 'Новосибирская область',
        'xlim': (-316567.241833225, 343436.059154225),
        'ylim': (-253848.664476225, 211203.086691225),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib_vodoem.shp'),
        'points': (
            (53.789135, 82.316124, 'Сузун'),
            (53.734326, 78.042362, 'Карасук'),
            (55.030199, 82.920430, 'Новосибирск'),
            (55.351508, 78.346415, 'Барабинск'),
            (55.238039, 84.402856, 'Тогучин'),
            (55.194476, 80.283039, 'Каргат'),
            (55.214532, 75.974090, 'Татарск'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'severn_nso',
        'display_name': 'Северный район Новосибирской области',
        'xlim': (-165870.98043732502, 41442.032910325),
        'ylim': (20749.377785675002, 181982.751752325),
        'mask_shapefile': __resource('maps/Novosibirsk/severn/severn_nso_agro.shp'),
        'points': (
            (56.348242, 78.363070, 'Северное'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'cherep_nso',
        'display_name': 'Черепановский район Новосибирской области',
        'xlim': (169212.532337925, 261630.003207075),
        'ylim': (-167048.713891075, -102373.214304925),
        'mask_shapefile': __resource('maps/Novosibirsk/cherep/cherep_nso_agro.shp'),
        'points': (
            (54.220642, 83.372516, 'Черепаново'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'ust_tar_nso',
        'display_name': 'Усть-Таркский район Новосибирской области',
        'xlim': (-300796.969113425, -213728.704623575),
        'ylim': (-4009.4215864250004, 81463.362073425),
        'mask_shapefile': __resource('maps/Novosibirsk/ust_tar/ust_tar_nso_agro.shp'),
        'points': (
            (55.565784, 75.708207, 'Усть-Тарка'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kupino_nso',
        'display_name': 'Купинский район Новосибирской области',
        'xlim': (-228024.6804622, -105513.1297638),
        'ylim': (-189762.4321762, -61250.5617718),
        'mask_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_vodoem.shp'),
        'points': (
            (54.366046, 77.297254, 'Купино'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'tatarsk_nso',
        'display_name': 'Татарский район',
        'xlim': (-303334.657773325, -214901.60085667498),
        'ylim': (-84293.370283325, 19941.400188325002),
        'mask_shapefile': __resource('maps/Novosibirsk/tatarsk/tatarsk_nso_agro.shp'),
        'points': (
            (55.214532, 75.974090, 'Татарск'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'karasuk_nso',
        'display_name': 'Карасукский район Новосибирской области',
        'xlim': (-182886.80055355, -79069.92339445),
        'ylim': (-240859.65378555, -126394.80180645),
        'mask_shapefile': __resource('maps/Novosibirsk/karasuk/karasuk_nso_agro.shp'),
        'points': (
            (53.734326, 78.042362, 'Карасук'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kolivan_nso',
        'display_name': 'Колыванский район Новосибирской области',
        'xlim': (94886.615990825, 229870.737833175),
        'ylim': (-36396.492768175, 122493.272413175),
        'mask_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_vodoem.shp'),
        'points': (
            (55.308859, 82.738647, 'Колывань'),
        ),
        'layers': __NSK_LAYERS,
        'invert_ratio': True
    },
    {
        'name': 'kuibichev_nso',
        'display_name': 'Куйбышевский район Новосибирской области',
        'xlim': (-161002.857039125, -8908.278327875001),
        'ylim': (-24102.947505125, 80793.133523125),
        'mask_shapefile': __resource('maps/Novosibirsk/kuibichev/kuibichev_nso_agro.shp'),
        'points': (
            (55.4475300, 78.3218100, 'Куйбышев'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'iskitim_nso',
        'display_name': 'Искитимский район Новосибирской области',
        'xlim': (151315.23419695, 263273.74619305),
        'ylim': (-134512.99889905, -46621.15050795),
        'mask_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_vodoem.shp'),
        'points': (
            (54.642582, 83.306382, 'Искитим'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'susun_nso',
        'display_name': 'Сузунский район Новосибирской области',
        'xlim': (110810.56911910001, 201616.3944279),
        'ylim': (-217893.04922490002, -112954.4985891),
        'mask_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_vodoem.shp'),
        'points': (
            (53.789135, 82.316124, 'Сузун'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'mochkov_nso',
        'display_name': 'Мошковский район Новосибирской области',
        'xlim': (184901.8786716, 262852.0669344),
        'ylim': (-40496.937208400006, 21095.425694399997),
        'mask_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_vodoem.shp'),
        'points': (
            (55.305338, 83.608638, 'Мошково'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'chistoz_nso',
        'display_name': 'Чистоозёрный район Новосибирской области',
        'xlim': (-275062.752540875, -169322.98050612502),
        'ylim': (-143702.895532875, -39415.461283125),
        'mask_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_vodoem.shp'),
        'points': (
            (54.707390, 76.581818, 'Чистоозёрное'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kichtov_nso',
        'display_name': 'Кыштовский район Новосибирской области',
        'xlim': (-251865.297145175, -83828.806571825),
        'ylim': (79057.944320825, 199489.591205175),
        'mask_shapefile': __resource('maps/Novosibirsk/kichtov/kichtov_nso_agro.shp'),
        'points': (
            (56.563467, 76.626626, 'Кыштовка'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'zdvinsk_nso',
        'display_name': 'Здвинский район Новосибирской области',
        'xlim': (-128673.912968175, -20622.098418825),
        'ylim': (-137434.978554175, -46701.036308824994),
        'mask_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_vodoem.shp'),
        'points': (
            (54.7020600, 78.6610500, 'Здвинск'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kochki',
        'display_name': 'Кочковский район Новосибирской области',
        'xlim': (-9154.60709825, 70859.71983624999),
        'ylim': (-174332.94511725, -98389.99774975001),
        'mask_shapefile': __resource('maps/Novosibirsk/kochki/kochki_agro.shp'),
        'points': (
            (54.3358300, 80.4805600, 'Кочки'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kargat_nso',
        'display_name': 'Каргатский район Новосибирской области',
        'xlim': (-28074.928551725, 77726.494692725),
        'ylim': (-117498.456205725, 19979.735206725),
        'mask_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_vodoem.shp'),
        'points': (
            (55.194476, 80.283039, 'Каргат'),
        ),
        'invert_ratio': True,
        'layers': __NSK_LAYERS
    },
    {
        'name': 'bolotno_nso',
        'display_name': 'Болотнинский район Новосибирской области',
        'xlim': (223041.62064502502, 300321.00832597504),
        'ylim': (-5217.242184975001, 70754.170131975),
        'mask_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_vodoem.shp'),
        'points': (
            (55.669336, 84.390711, 'Болотное'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'barabin_nso',
        'display_name': 'Барабинский район Новосибирской области',
        'xlim': (-162017.3781791, -57851.5403849),
        'ylim': (-91934.8670441, -4017.2766579),
        'mask_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_vodoem.shp'),
        'points': (
            (55.351508, 78.346415, 'Барабинск'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'maslyan_nso',
        'display_name': 'Маслянинский район Новосибирской области',
        'xlim': (239819.0050041, 329865.6628899),
        'ylim': (-145613.40960389999, -70184.9529101),
        'mask_shapefile': __resource('maps/Novosibirsk/maslyan/maslyan_nso_agro.shp'),
        'points': (
            (54.346444, 84.182266, 'Маслянино'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'toguchi_nso',
        'display_name': 'Тогучинский район Новосибирской области',
        'xlim': (212672.662816725, 325528.303852275),
        'ylim': (-96873.919128275, 12347.155724275002),
        'mask_shapefile': __resource('maps/Novosibirsk/toguchi/toguchi_nso_agro.shp'),
        'points': (
            (55.238039, 84.402856, 'Тогучин'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'chani_nso',
        'display_name': 'Чановский район Новосибирской области',
        'xlim': (-235010.750734925, -127849.090790075),
        'ylim': (-83508.187980925, 18449.927417925),
        'mask_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_vodoem.shp'),
        'points': (
            (55.309146, 76.761320, 'Чаны'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'chulim_nso',
        'display_name': 'Чулымский район Новосибирской области',
        'xlim': (27251.655499825, 139549.789971175),
        'ylim': (-119463.712203175, 57852.263662175),
        'mask_shapefile': __resource('maps/Novosibirsk/chulim/chulim_nso_agro.shp'),
        'points': (
            (55.091258, 80.963288, 'Чулым'),
        ),
        'layers': __NSK_LAYERS,
        'invert_ratio': True
    },
    {
        'name': 'ordinsk_nso',
        'display_name': 'Ордынский район Новосибирской области',
        'xlim': (61154.6513246, 164189.90070740003),
        'ylim': (-174940.9038554, -78629.4780716),
        'mask_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_vodoem.shp'),
        'points': (
            (54.367147, 81.899566, 'Ордынское'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'krasnoz_nso',
        'display_name': 'Краснозёрский район Новосибирской области',
        'xlim': (-97794.9177679, 1760.0604779),
        'ylim': (-204880.3196299, -120887.0480601),
        'mask_shapefile': __resource('maps/Novosibirsk/krasnoz/krasnoz_nso_agro.shp'),
        'points': (
            (53.983815, 79.238604, 'Краснозёрское'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'ubinsk_nso',
        'display_name': 'Убинский район',
        'xlim': (-69735.6433484, 117123.4020454),
        'ylim': (-81663.9118714, 118903.50012740001),
        'mask_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_vodoem.shp'),
        'points': (
            (55.299542, 79.685893, 'Убинское'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'vengero_nso',
        'display_name': 'Венгеровский район Новосибирской области',
        'xlim': (-237834.94982735, -122704.04081465),
        'ylim': (413.38085164999984, 104231.43515835001),
        'mask_shapefile': __resource('maps/Novosibirsk/vengerovo/vengero_nso_agro.shp'),
        'points': (
            (55.684193, 76.747827, 'Венгерово'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'dovolno_nso',
        'display_name': 'Доволенский район Новосибирской области',
        'xlim': (-70489.7536817, 30667.0021177),
        'ylim': (-150077.86114969998, -63890.762854299996),
        'mask_shapefile': __resource('maps/Novosibirsk/dovolno/dovolno_nso_agro.shp'),
        'points': (
            (54.496233, 79.664648, 'Довольное'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kochene_nso',
        'display_name': 'Коченёвский район Новосибирской области',
        'xlim': (83018.067547825, 181159.487381175),
        'ylim': (-93186.525050175, 6417.943781175),
        'mask_shapefile': __resource('maps/Novosibirsk/kochenev/kochene_nso_agro.shp'),
        'points': (
            (55.0218000, 82.2020000, 'Коченёво'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'bagan_nso',
        'display_name': 'Баганский район Новосибирской области',
        'xlim': (-190470.044692725, -100098.473512275),
        'ylim': (-196259.17270172498, -124188.85062627499),
        'mask_shapefile': __resource('maps/Novosibirsk/bagan/bagan_nso_agro.shp'),
        'points': (
            (54.097380, 77.665573, 'Баган'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'novosib_nso',
        'display_name': 'Новосибирский район Новосибирской области',
        'xlim': (138851.080401375, 224516.346140625),
        'ylim': (-100137.867436625, -569.7811283749998),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_vodoem.shp'),
        'points': (
            (55.030199, 82.920430, 'Новосибирск'),
        ),
        'layers': __NSK_LAYERS
    },
    {
        'name': 'kem',
        'display_name': 'Кемеровская область',
        'xlim': (262005.925617675, 624824.167033325),
        'ylim': (-341203.729077325, 189546.408784325),
        'mask_shapefile': __resource('maps/Kemerovo/kem_agro.shp'),
        'water_shapefile': __resource('maps/Kemerovo/kem_vodoem.shp'),
        'points': (
            (55.354968, 86.087314, 'Кемерово'),
            (56.209250, 87.735094, 'Мариинск'),
            (53.757547, 87.136044, 'Новокузнецк'),
            (53.686596, 88.070372, 'Междуреченск'),
            (54.663609, 86.162243, 'Ленинск-Кузнецкий'),
            (56.078684, 86.020129, 'Анжеро-Судженск'),
        ),
        'layers': __KEM_LAYERS,
        'invert_ratio': True
    },
    {
        'name': 'krasn',
        'display_name': 'Красноярский край',
        'xlim': (489112.0617009, 1091895.9732661),
        'ylim': (-351189.4183711, 365774.4729971),
        'mask_shapefile': __resource('maps/Krasnoyarsk/krasn_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/krasn_vodoem.shp'),
        'points': (
            (56.010569, 92.852545, 'Красноярск'),
            (56.205060, 95.705109, 'Канск'),
            (53.710548, 91.687250, 'Минусинск'),
            (56.269496, 90.495231, 'Ачинск'),
            (57.7004000, 93.2809000, 'Казачинское'),

        ),
        'layers': [
            __KRASN_REGIONS_LAYER,
            __KRASN_GROUPS_BORDER_LAYER,
            __KRASN_BORDER_LAYER
        ],
        'invert_ratio': True,
        'gradation': 'krasnoyarsk'
    },
    {
        'name': 'Kansk',
        'display_name': 'Канская группа районов Красноярского края',
        'xlim': (796749.38408605, 1080482.03001695),
        'ylim': (-36760.36386395, 352867.94135394995),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_vodoem.shp'),
        'points': (
            (56.205060, 95.705109, 'Канск'),
        ),
        'layers': [
            __KRASN_REGIONS_LAYER,
            __KRASN_GROUPS_BORDER_LAYER,
            __KRASN_BORDER_LAYER
        ],
        'invert_ratio': True,
        'gradation': 'krasnoyarsk'
    },
    {
        'name': 'Krasn_Gr',
        'display_name': 'Красноярская группа районов Красноярского края',
        'xlim': (646535.490693525, 890239.042102475),
        'ylim': (-48776.367270475, 358398.544921475),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_vodoem.shp'),
        'points': (
            (56.010569, 92.852545, 'Красноярск'),
        ),
        'layers': [
            __KRASN_REGIONS_LAYER,
            __KRASN_GROUPS_BORDER_LAYER,
            __KRASN_BORDER_LAYER
        ],
        'invert_ratio': True,
        'gradation': 'krasnoyarsk'
    },
    {
        'name': 'Achinsk',
        'display_name': 'Ачинская группа районов Красноярского края',
        'xlim': (498434.2118042, 691928.8637658),
        'ylim': (-19775.0070318, 305658.5799978),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_vodoem.shp'),
        'points': (
            (56.269496, 90.495231, 'Ачинск'),
        ),
        'layers': [
            __KRASN_REGIONS_LAYER,
            __KRASN_GROUPS_BORDER_LAYER,
            __KRASN_BORDER_LAYER
        ],
        'invert_ratio': True,
        'gradation': 'krasnoyarsk'
    },
    {
        'name': 'Minusinsk',
        'display_name': 'Минусинская группа районов Красноярского края',
        'xlim': (684541.3474266, 1084344.5277654),
        'ylim': (-343637.9728704, 22131.7323654),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_vodoem.shp'),
        'points': (
            (53.710548, 91.687250, 'Минусинск'),
        ),
        'layers': [
            __KRASN_REGIONS_LAYER,
            __KRASN_GROUPS_BORDER_LAYER,
            __KRASN_BORDER_LAYER
        ],
        'invert_ratio': False,
        'gradation': 'krasnoyarsk'
    },
    {
        'name': 'omsk',
        'display_name': 'Омская область',
        'xlim': (-602432.28927165, -204825.23171335002),
        'ylim': (-221580.57819765, 379646.37405765004),
        'mask_shapefile': __resource('maps/Omsk/omsk_agro.shp'),
        'water_shapefile': __resource('maps/Omsk/omsk_vodoem.shp'),
        'points': (
            (54.989342, 73.368212, 'Омск'),
            (56.897015, 74.370795, 'Тара'),
            (55.568853, 71.350344, 'Называевск'),
            (55.051608, 74.578467, 'Калачинск'),
            (54.909168, 71.267475, 'Исилькуль'),
        ),
        'layers': [
            __OMSK_REGIONS_LAYER,
            __OMSK_BORDER_LAYER
        ],
        'invert_ratio': True
    },
]
