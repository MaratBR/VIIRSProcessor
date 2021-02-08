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

# сколько дней приходит на один композит NDVI
# например, если поставить 3 дня то прога будет каждый день
# делать композит за последние 3 дня
# NDVI_MERGE_PERIOD_IN_DAYS = 5

# сколько дней должно пройти между началом одного композита и концом другого
# значение по умолчанию в 2 раза больше, чем NDVI_MERGE_PERIOD_IN_DAYS, поэтому
# менять это значение лучше не стоит
# NDVI_DYNAMICS_PERIOD = NDVI_MERGE_PERIOD_IN_DAYS * 2


LOGO_PATH = __resource('logo.png')
ISO_QUALITY_SIGN = __resource('iso_sign.jpg')
IS_DEBUG = True

# входые данные и папка с выходными
OUTPUTS = {
    'ndvi': '~/Documents/viirs/processed/products/ndvi',
    'ndvi_dynamics': '~/Documents/viirs/processed/products/ndvi_dynamics',
    'processed_data': '~/Documents/viirs/processed/data'
}

INPUTS = {
    'data': '/media/marat/Quack/Projects/GDAL_Data/NPP/'
}

FONT_FAMILY = __resource('times.ttf')

# папка с БД файлом
# CONFIG_DIR = ''

# конфигурация PNG файлов, где
# name - уникальный идентификатор изображения
# display_name - имя, которое будет размещено на изображении
# xlim и ylim - массив с 2 элементами (предел по X и Y в проекции)
# points - точки, которые надо отметить на карте и их координаты (см. пример ниже)
PNG_CONFIG = [
    {
        'name': 'region',
        'display_name': None,
        'xlim': (-613316.28569515, 602479.25968115),
        'ylim': (-545676.98683915, 338037.04381214996),
        'mask_shapefile': __resource('maps/Region/region_agro.shp'),
        'water_shapefile': __resource('maps/Region/region_vodoem.shp'),
        'points': (
            (54.989342, 73.368212, 'Омск'),
            (53.348053, 83.779875, 'Барнаул'),
            (55.354968, 86.087314, 'Кемерово'),
            (55.030199, 82.920430, 'Новосибирск'),
        )
    },
    {
        'name': 'altkrai',
        'display_name': 'Алтайский край',
        'xlim': (-148619.26369895, 461101.19085894997),
        'ylim': (-531246.62753395, -98926.14745804999),
        'mask_shapefile': __resource('maps/Altai/altkrai_agro.shp'),
        'water_shapefile': __resource('maps/Altai/altkrai_vodoem.shp'),
        'points': (
            (53.348053, 83.779875, 'Барнаул'),
            (52.999369, 78.645913, 'Славгород'),
            (51.501235, 81.207774, 'Рубцовск'),
            (52.539308, 85.213829, 'Бийск'),
            (51.996094, 84.983959, 'Белокуриха'),
            (53.791470, 81.354603, 'Камень-на-Оби'),
        )
    },
    {
        'name': 'novosib',
        'display_name': 'Новосибирская область',
        'xlim': (-315421.487193475, 338408.64897447504),
        'ylim': (-245575.837519475, 186922.999586475),
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
        )
    },
    {
        'name': 'severn_nso',
        'display_name': 'Северный район',
        'xlim': (-142388.486583275, -67742.125503725),
        'ylim': (26443.561230725, 135232.91901027499),
        'mask_shapefile': __resource('maps/Novosibirsk/severn/severn_nso_agro.shp'),
        'points': (
            (56.348242, 78.363070, 'Северное'),
        )
    },
    {
        'name': 'cherep_nso',
        'display_name': 'Черепановский район',
        'xlim': (169342.053579275, 261207.358497725),
        'ylim': (-167035.567082725, -102386.361113275),
        'mask_shapefile': __resource('maps/Novosibirsk/cherep/cherep_nso_agro.shp'),
        'points': (
            (54.220642, 83.372516, 'Черепаново'),
        )
    },
    {
        'name': 'ust_tar_nso',
        'display_name': 'Усть-Таркский район',
        'xlim': (-300329.386616275, -214297.617074725),
        'ylim': (-2919.571588274999, 77558.583716275),
        'mask_shapefile': __resource('maps/Novosibirsk/ust_tar/ust_tar_nso_agro.shp'),
        'points': (
            (55.565784, 75.708207, 'Усть-Тарка'),
        )
    },
    {
        'name': 'kupino_nso',
        'display_name': 'Купинский район',
        'xlim': (-227871.13404605, -105808.21311995),
        'ylim': (-179274.74384905, -78573.23439895),
        'mask_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_vodoem.shp'),
        'points': (
            (54.366046, 77.297254, 'Купино'),
        )
    },
    {
        'name': 'tatarsk_nso',
        'display_name': 'Татарский район',
        'xlim': (-302222.12275589997, -215015.36134909999),
        'ylim': (-81519.0159639, 17937.8138259),
        'mask_shapefile': __resource('maps/Novosibirsk/tatarsk/tatarsk_nso_agro.shp'),
        'points': (
            (55.214532, 75.974090, 'Татарск'),
        )
    },
    {
        'name': 'karasuk_nso',
        'display_name': 'Карасукский район',
        'xlim': (-180500.226963425, -79496.848935575),
        'ylim': (-232439.425342425, -130338.600610575),
        'mask_shapefile': __resource('maps/Novosibirsk/karasuk/karasuk_nso_agro.shp'),
        'points': (
            (53.734326, 78.042362, 'Карасук'),
        )
    },
    {
        'name': 'kolivan_nso',
        'display_name': 'Коливанский район',
        'xlim': (139343.20705549998, 221942.46203650002),
        'ylim': (-34333.9072325, 50356.8942145),
        'mask_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_vodoem.shp'),
        'points': (
            (55.308859, 82.738647, 'Колывань'),
        )
    },
    {
        'name': 'kuibichev_nso',
        'display_name': 'Куйбышевский район',
        'xlim': (-160430.8642916, -16563.8160884),
        'ylim': (-19520.5197196, 77468.7255126),
        'mask_shapefile': __resource('maps/Novosibirsk/kuibichev/kuibichev_nso_agro.shp'),
        'points': (
            (55.4475300, 78.3218100, 'Куйбышево'),
        )
    },
    {
        'name': 'iskitim_nso',
        'display_name': 'Искитимский район',
        'xlim': (153804.150501775, 259496.814343225),
        'ylim': (-134363.812038225, -63220.25337977501),
        'mask_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_vodoem.shp'),
        'points': (
            (54.642582, 83.306382, 'Искитим'),
        )
    },
    {
        'name': 'susun_nso',
        'display_name': 'Сузунский район',
        'xlim': (111914.13985544999, 182112.93181054998),
        'ylim': (-205176.84894455, -113271.40337345),
        'mask_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_vodoem.shp'),
        'points': (
            (53.789135, 82.316124, 'Сузун'),
        )
    },
    {
        'name': 'mochkov_nso',
        'display_name': 'Мошковский район',
        'xlim': (192718.909915575, 262214.723845425),
        'ylim': (-38068.140889425, 15935.356401425),
        'mask_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_vodoem.shp'),
        'points': (
            (55.305338, 83.608638, 'Мошково'),
        )
    },
    {
        'name': 'chistoz_nso',
        'display_name': 'Чистоозёрный район',
        'xlim': (-269013.0771825, -174998.5591095),
        'ylim': (-133242.4208975, -45731.5375205),
        'mask_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_vodoem.shp'),
        'points': (
            (54.707390, 76.581818, 'Чистоозёрное'),
        )
    },
    {
        'name': 'kichtov_nso',
        'display_name': 'Кыштовский район',
        'xlim': (-247432.44608750002, -137889.1897265),
        'ylim': (101280.8427855, 173963.78816250002),
        'mask_shapefile': __resource('maps/Novosibirsk/kichtov/kichtov_nso_agro.shp'),
        'points': (
            (56.563467, 76.626626, 'Кыштовка'),
        )
    },
    {
        'name': 'zdvinsk_nso',
        'display_name': 'Здвинский район',
        'xlim': (-123707.1699682, -36297.959417800004),
        'ylim': (-135972.6483912, -47527.2078588),
        'mask_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_vodoem.shp'),
        'points': (
            (54.7020600, 78.6610500, 'Здвинск'),
        )
    },
    {
        'name': 'kochki',
        'display_name': 'Кочковский район',
        'xlim': (-9143.639867325, 70410.06336832499),
        'ylim': (-174321.977886325, -98892.250330675),
        'mask_shapefile': __resource('maps/Novosibirsk/kochki/kochki_agro.shp'),
        'points': (
            (54.3358300, 80.4805600, 'Кочки'),
        )
    },
    {
        'name': 'kargat_nso',
        'display_name': 'Каргатский район',
        'xlim': (-26587.309799950002, 59970.20547495),
        'ylim': (-116592.87336294999, -6864.12877105),
        'mask_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_vodoem.shp'),
        'points': (
            (55.194476, 80.283039, 'Каргат'),
        )
    },
    {
        'name': 'bolotno_nso',
        'display_name': 'Болотнинский район',
        'xlim': (227382.403931225, 300036.50380377495),
        'ylim': (-5087.8931237749985, 51914.128559774996),
        'mask_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_vodoem.shp'),
        'points': (
            (55.669336, 84.390711, 'Болотное'),
        )
    },
    {
        'name': 'barabin_nso',
        'display_name': 'Барабинский район',
        'xlim': (-160030.79427925, -57899.99365075),
        'ylim': (-89781.02445525001, -4718.37967975),
        'mask_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_vodoem.shp'),
        'points': (
            (55.351508, 78.346415, 'Барабинск'),
        )
    },
    {
        'name': 'maslyan_nso',
        'display_name': 'Маслянинский район',
        'xlim': (240972.69409422498, 309887.679286775),
        'ylim': (-138571.07083877502, -87998.663091225),
        'mask_shapefile': __resource('maps/Novosibirsk/maslyan/maslyan_nso_agro.shp'),
        'points': (
            (54.346444, 84.182266, 'Маслянино'),
        )
    },
    {
        'name': 'toguchi_nso',
        'display_name': 'Тогучинский район',
        'xlim': (215816.5289577, 325451.6241903),
        'ylim': (-70021.48981530001, 12270.4760623),
        'mask_shapefile': __resource('maps/Novosibirsk/toguchi/toguchi_nso_agro.shp'),
        'points': (
            (55.238039, 84.402856, 'Тогучин'),
        )
    },
    {
        'name': 'chani_nso',
        'display_name': 'Чановский район',
        'xlim': (-227997.860929875, -145915.306213125),
        'ylim': (-59924.096172875, 16864.090235875),
        'mask_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_vodoem.shp'),
        'points': (
            (55.309146, 76.761320, 'Чаны'),
        )
    },
    {
        'name': 'chulim_nso',
        'display_name': 'Чулымский район',
        'xlim': (33297.327732925, 105921.135543075),
        'ylim': (-117493.665358075, -20873.592336924998),
        'mask_shapefile': __resource('maps/Novosibirsk/chulim/chulim_nso_agro.shp'),
        'points': (
            (55.091258, 80.963288, 'Чулым'),
        )
    },
    {
        'name': 'ordinsk_nso',
        'display_name': 'Ордынский район',
        'xlim': (61607.715436750004, 156811.13627724999),
        'ylim': (-149458.67565025, -78815.95017975),
        'mask_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_vodoem.shp'),
        'points': (
            (54.367147, 81.899566, 'Ордынское'),
        )
    },
    {
        'name': 'krasnoz_nso',
        'display_name': 'Краснозёрский район',
        'xlim': (-93422.831541975, 1203.4488489750001),
        'ylim': (-204762.969680975, -122437.352197025),
        'mask_shapefile': __resource('maps/Novosibirsk/krasnoz/krasnoz_nso_agro.shp'),
        'points': (
            (53.983815, 79.238604, 'Краснозерское'),
        )
    },
    {
        'name': 'ubinsk_nso',
        'display_name': 'Убинский район',
        'xlim': (-64049.365536925, 3588.552981925),
        'ylim': (-77745.075373925, 26556.311532925003),
        'mask_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_vodoem.shp'),
        'points': (
            (55.299542, 79.685893, 'Убинское'),
        )
    },
    {
        'name': 'vengero_nso',
        'display_name': 'Венгеровский район',
        'xlim': (-236152.86333494997, -138478.91317305),
        'ylim': (2509.74160205, 83782.28330095),
        'mask_shapefile': __resource('maps/Novosibirsk/vengerovo/vengero_nso_agro.shp'),
        'points': (
            (55.684193, 76.747827, 'Венгерово'),
        )
    },
    {
        'name': 'dovolno_nso',
        'display_name': 'Доволенский район',
        'xlim': (-67677.7743274, 30598.4172554),
        'ylim': (-150009.2762874, -63959.347716599994),
        'mask_shapefile': __resource('maps/Novosibirsk/dovolno/dovolno_nso_agro.shp'),
        'points': (
            (54.496233, 79.664648, 'Довольное'),
        )
    },
    {
        'name': 'kochene_nso',
        'display_name': 'Коченёвский район',
        'xlim': (91399.885542875, 167386.703994125),
        'ylim': (-84823.047196125, -11673.928863875),
        'mask_shapefile': __resource('maps/Novosibirsk/kochenev/kochene_nso_agro.shp'),
        'points': (
            (55.0218000, 82.2020000, 'Коченёво'),
        )
    },
    {
        'name': 'bagan_nso',
        'display_name': 'Баганский район',
        'xlim': (-186734.159553725, -100769.013291275),
        'ylim': (-194976.59276972502, -124293.76550527499),
        'mask_shapefile': __resource('maps/Novosibirsk/bagan/bagan_nso_agro.shp'),
        'points': (
            (54.097380, 77.665573, 'Баган'),
        )
    },
    {
        'name': 'novosib_nso',
        'display_name': 'Новосибирский район Новосбирской области',
        'xlim': (139276.92929285, 220959.36215914998),
        'ylim': (-92706.11865915, -23580.896478849998),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_vodoem.shp'),
        'points': (
            (55.030199, 82.920430, 'Новосибирск'),
        )
    },
    {
        'name': 'kem',
        'display_name': 'Кемеровская область',
        'xlim': (268976.86160635, 582786.40240165),
        'ylim': (-238911.40286565, 149784.13677165),
        'mask_shapefile': __resource('maps/Kemerovo/kem_agro.shp'),
        'water_shapefile': __resource('maps/Kemerovo/kem_vodoem.shp'),
        'points': (
            (55.354968, 86.087314, 'Кемерово'),
            (56.209250, 87.735094, 'Мариинск'),
            (53.757547, 87.136044, 'Новокузнецк'),
            (53.686596, 88.070372, 'Междуречинск'),
            (54.663609, 86.162243, 'Ленинск-Кузнецкий'),
            (56.078684, 86.020129, 'Анжеро-Суджинск'),
        )
    },
    {
        'name': 'krasn',
        'display_name': 'Красноярский край',
        'xlim': (528521.623824975, 1026909.0671050249),
        'ylim': (-213767.708166025, 336838.83205302496),
        'mask_shapefile': __resource('maps/Krasnoyarsk/krasn_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/krasn_vodoem.shp'),
        'points': (
            (56.010569, 92.852545, 'Красноярск'),
            (56.205060, 95.705109, 'Канск'),
            (56.205060, 95.705109, 'Канск'),
            (56.269496, 90.495231, 'Ачинск'),
            (57.7004000, 93.2809000, 'Казаченское'),

        )
    },
    {
        'name': 'Kansk',
        'display_name': 'Канский район',
        'xlim': (841592.3278167, 1019796.6924013),
        'ylim': (51904.5589087, 303791.3615713),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_vodoem.shp'),
        'points': (
            (56.205060, 95.705109, 'Канск'),
        )
    },
    {
        'name': 'Krasn_Gr',
        'display_name': 'Красноярская группа районов красноярского края',
        'xlim': (648850.163683375, 873551.559537625),
        'ylim': (-39402.565349625, 313952.306378625),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_vodoem.shp'),
        'points': (
            (56.010569, 92.852545, 'Красноярск'),
        )
    },
    {
        'name': 'Achinsk',
        'display_name': 'Ачинский район',
        'xlim': (537325.0007644, 680040.9534535999),
        'ylim': (-14119.8061776, 166744.9025856),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_vodoem.shp'),
        'points': (
            (56.269496, 90.495231, 'Ачинск'),
        )
    },
    {
        'name': 'Minusinsk',
        'display_name': 'Минусинский район',
        'xlim': (712096.60938435, 864493.62974565),
        'ylim': (-205207.68312265002, -14122.19472535),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_vodoem.shp'),
        'points': (
            (53.710548, 91.687250, 'Минусинск'),
        )
    },
    {
        'name': 'omsk',
        'display_name': 'Омская область',
        'xlim': (-597277.6522497501, -206999.67271325),
        'ylim': (-220174.53030275, 321998.41036675),
        'mask_shapefile': __resource('maps/Omsk/omsk_agro.shp'),
        'water_shapefile': __resource('maps/Omsk/omsk_vodoem.shp'),
        'points': (
            (54.989342, 73.368212, 'Омск'),
            (56.897015, 74.370795, 'Тара'),
            (55.568853, 71.350344, 'Называевск'),
            (55.051608, 74.578467, 'Калачинск'),
            (54.909168, 71.267475, 'Исилькуль'),
        )
    },
]
