import os
__BASE_DIR = os.path.dirname(__file__)


def __resource(path):
    return os.path.join(__BASE_DIR, 'required_resources', path)


# по умолчанию 1000
SCALE = 750
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

FONT_FAMILY = '/home/marat/Downloads/Agro/Font/times.ttf'

# дополнительный точки на карте (Томск уже есть по-умолчанию и показан просто как пример)
# MAP_POINTS = [
#     (84.948197, 56.484680, 'Томск')
# ]

# папка с БД файлом
# CONFIG_DIR = ''

# конфигурация PNG файлов, где
# name - уникальный идентификатор изображения
# display_name - имя, которое будет размещено на изображении
# xlim и ylim - массив с 2 элементами (предел по X и Y в проекции)
PNG_CONFIG = [
    {
        'name': 'region',
        'display_name': None,
        'xlim': (-613316.28569515, 602479.25968115),
        'ylim': (-545676.98683915, 338037.04381214996),
        'mask_shapefile': __resource('maps/Region/region_agro.shp'),
        'water_shapefile': __resource('maps/Region/region_vodoem.shp')
    },
    {
        'name': 'altkrai',
        'display_name': 'Алтайский край',
        'xlim': (-148619.26369895, 461101.19085894997),
        'ylim': (-531246.62753395, -98926.14745804999),
        'mask_shapefile': __resource('maps/Altai/altkrai_agro.shp'),
        'water_shapefile': __resource('maps/Altai/altkrai_vodoem.shp')
    },
    {
        'name': 'novosib',
        'display_name': 'Новосибирская область',
        'xlim': (-315421.487193475, 338408.64897447504),
        'ylim': (-245575.837519475, 186922.999586475),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib_vodoem.shp')
    },
    {
        'name': 'severn_nso',
        'display_name': 'Северный район',
        'xlim': (-142388.486583275, -67742.125503725),
        'ylim': (26443.561230725, 135232.91901027499),
        'mask_shapefile': __resource('maps/Novosibirsk/severn/severn_nso_agro.shp')
    },
    {
        'name': 'cherep_nso',
        'display_name': 'Черепановский район',
        'xlim': (169342.053579275, 261207.358497725),
        'ylim': (-167035.567082725, -102386.361113275),
        'mask_shapefile': __resource('maps/Novosibirsk/cherep/cherep_nso_agro.shp')
    },
    {
        'name': 'ust_tar_nso',
        'display_name': 'Усть-Таркский район',
        'xlim': (-300329.386616275, -214297.617074725),
        'ylim': (-2919.571588274999, 77558.583716275),
        'mask_shapefile': __resource('maps/Novosibirsk/ust_tar/ust_tar_nso_agro.shp')
    },
    {
        'name': 'kupino_nso',
        'display_name': 'Купинский район',
        'xlim': (-227871.13404605, -105808.21311995),
        'ylim': (-179274.74384905, -78573.23439895),
        'mask_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_vodoem.shp')
    },
    {
        'name': 'tatarsk_nso',
        'display_name': 'Татарский район',
        'xlim': (-302222.12275589997, -215015.36134909999),
        'ylim': (-81519.0159639, 17937.8138259),
        'mask_shapefile': __resource('maps/Novosibirsk/tatarsk/tatarsk_nso_agro.shp')
    },
    {
        'name': 'karasuk_nso',
        'display_name': 'Карасукский район',
        'xlim': (-180500.226963425, -79496.848935575),
        'ylim': (-232439.425342425, -130338.600610575),
        'mask_shapefile': __resource('maps/Novosibirsk/karasuk/karasuk_nso_agro.shp')
    },
    {
        'name': 'kolivan_nso',
        'display_name': 'Коливанский район',
        'xlim': (139343.20705549998, 221942.46203650002),
        'ylim': (-34333.9072325, 50356.8942145),
        'mask_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_vodoem.shp')
    },
    {
        'name': 'kuibichev_nso',
        'display_name': 'Куйбышевский район',
        'xlim': (-160430.8642916, -16563.8160884),
        'ylim': (-19520.5197196, 77468.7255126),
        'mask_shapefile': __resource('maps/Novosibirsk/kuibichev/kuibichev_nso_agro.shp')
    },
    {
        'name': 'iskitim_nso',
        'display_name': 'Искитимский район',
        'xlim': (153804.150501775, 259496.814343225),
        'ylim': (-134363.812038225, -63220.25337977501),
        'mask_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_vodoem.shp')
    },
    {
        'name': 'susun_nso',
        'display_name': 'Сузунский район',
        'xlim': (111914.13985544999, 182112.93181054998),
        'ylim': (-205176.84894455, -113271.40337345),
        'mask_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_vodoem.shp')
    },
    {
        'name': 'mochkov_nso',
        'display_name': 'Мошковский район',
        'xlim': (192718.909915575, 262214.723845425),
        'ylim': (-38068.140889425, 15935.356401425),
        'mask_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_vodoem.shp')
    },
    {
        'name': 'chistoz_nso',
        'display_name': 'Чистоозёрный район',
        'xlim': (-269013.0771825, -174998.5591095),
        'ylim': (-133242.4208975, -45731.5375205),
        'mask_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_vodoem.shp')
    },
    {
        'name': 'kichtov_nso',
        'display_name': 'Кыштовский район',
        'xlim': (-247432.44608750002, -137889.1897265),
        'ylim': (101280.8427855, 173963.78816250002),
        'mask_shapefile': __resource('maps/Novosibirsk/kichtov/kichtov_nso_agro.shp')
    },
    {
        'name': 'zdvinsk_nso',
        'display_name': 'Здвинский район',
        'xlim': (-123707.1699682, -36297.959417800004),
        'ylim': (-135972.6483912, -47527.2078588),
        'mask_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_vodoem.shp')
    },
    {
        'name': 'kochki',
        'display_name': 'Кочковский район',
        'xlim': (-9143.639867325, 70410.06336832499),
        'ylim': (-174321.977886325, -98892.250330675),
        'mask_shapefile': __resource('maps/Novosibirsk/kochki/kochki_agro.shp')
    },
    {
        'name': 'kargat_nso',
        'display_name': 'Каргатский район',
        'xlim': (-26587.309799950002, 59970.20547495),
        'ylim': (-116592.87336294999, -6864.12877105),
        'mask_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_vodoem.shp')
    },
    {
        'name': 'bolotno_nso',
        'display_name': 'Болотнинский район',
        'xlim': (227382.403931225, 300036.50380377495),
        'ylim': (-5087.8931237749985, 51914.128559774996),
        'mask_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_vodoem.shp')
    },
    {
        'name': 'barabin_nso',
        'display_name': 'Барабинский район',
        'xlim': (-160030.79427925, -57899.99365075),
        'ylim': (-89781.02445525001, -4718.37967975),
        'mask_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_vodoem.shp')
    },
    {
        'name': 'maslyan_nso',
        'display_name': 'Маслянинский район',
        'xlim': (240972.69409422498, 309887.679286775),
        'ylim': (-138571.07083877502, -87998.663091225),
        'mask_shapefile': __resource('maps/Novosibirsk/maslyan/maslyan_nso_agro.shp')
    },
    {
        'name': 'toguchi_nso',
        'display_name': 'Тогучинский район',
        'xlim': (215816.5289577, 325451.6241903),
        'ylim': (-70021.48981530001, 12270.4760623),
        'mask_shapefile': __resource('maps/Novosibirsk/toguchi/toguchi_nso_agro.shp')
    },
    {
        'name': 'chani_nso',
        'display_name': 'Чановский район',
        'xlim': (-227997.860929875, -145915.306213125),
        'ylim': (-59924.096172875, 16864.090235875),
        'mask_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_vodoem.shp')
    },
    {
        'name': 'chulim_nso',
        'display_name': 'Чулымский район',
        'xlim': (33297.327732925, 105921.135543075),
        'ylim': (-117493.665358075, -20873.592336924998),
        'mask_shapefile': __resource('maps/Novosibirsk/chulim/chulim_nso_agro.shp')
    },
    {
        'name': 'ordinsk_nso',
        'display_name': 'Ординский район',
        'xlim': (61607.715436750004, 156811.13627724999),
        'ylim': (-149458.67565025, -78815.95017975),
        'mask_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_vodoem.shp')
    },
    {
        'name': 'krasnoz_nso',
        'display_name': 'Краснозёрский район',
        'xlim': (-93422.831541975, 1203.4488489750001),
        'ylim': (-204762.969680975, -122437.352197025),
        'mask_shapefile': __resource('maps/Novosibirsk/krasnoz/krasnoz_nso_agro.shp')
    },
    {
        'name': 'ubinsk_nso',
        'display_name': 'Убинский район',
        'xlim': (-64049.365536925, 3588.552981925),
        'ylim': (-77745.075373925, 26556.311532925003),
        'mask_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_vodoem.shp')
    },
    {
        'name': 'vengero_nso',
        'display_name': 'Венгеровский район',
        'xlim': (-236152.86333494997, -138478.91317305),
        'ylim': (2509.74160205, 83782.28330095),
        'mask_shapefile': __resource('maps/Novosibirsk/vengerovo/vengero_nso_agro.shp')
    },
    {
        'name': 'dovolno_nso',
        'display_name': 'Доволенский район',
        'xlim': (-67677.7743274, 30598.4172554),
        'ylim': (-150009.2762874, -63959.347716599994),
        'mask_shapefile': __resource('maps/Novosibirsk/dovolno/dovolno_nso_agro.shp')
    },
    {
        'name': 'kochene_nso',
        'display_name': 'Коченёвский район',
        'xlim': (91399.885542875, 167386.703994125),
        'ylim': (-84823.047196125, -11673.928863875),
        'mask_shapefile': __resource('maps/Novosibirsk/kochenev/kochene_nso_agro.shp')
    },
    {
        'name': 'bagan_nso',
        'display_name': 'Баганский район',
        'xlim': (-186734.159553725, -100769.013291275),
        'ylim': (-194976.59276972502, -124293.76550527499),
        'mask_shapefile': __resource('maps/Novosibirsk/bagan/bagan_nso_agro.shp')
    },
    {
        'name': 'novosib_nso',
        'display_name': 'Новосибирский район Новосбирской области',
        'xlim': (139276.92929285, 220959.36215914998),
        'ylim': (-92706.11865915, -23580.896478849998),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_vodoem.shp')
    },
    {
        'name': 'kem',
        'display_name': 'Кемеровская область',
        'xlim': (268976.86160635, 582786.40240165),
        'ylim': (-238911.40286565, 149784.13677165),
        'mask_shapefile': __resource('maps/Kemerovo/kem_agro.shp'),
        'water_shapefile': __resource('maps/Kemerovo/kem_vodoem.shp')
    },
    {
        'name': 'krasn',
        'display_name': 'Красноярский край',
        'xlim': (528521.623824975, 1026909.0671050249),
        'ylim': (-213767.708166025, 336838.83205302496),
        'mask_shapefile': __resource('maps/Krasnoyarsk/krasn_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/krasn_vodoem.shp')
    },
    {
        'name': 'Kansk',
        'display_name': 'Канский район',
        'xlim': (841592.3278167, 1019796.6924013),
        'ylim': (51904.5589087, 303791.3615713),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_vodoem.shp')
    },
    {
        'name': 'Krasn_Gr',
        'display_name': 'Красноярская группа районов красноярского края',
        'xlim': (648850.163683375, 873551.559537625),
        'ylim': (-39402.565349625, 313952.306378625),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_vodoem.shp')
    },
    {
        'name': 'Achinsk',
        'display_name': 'Ачинский район',
        'xlim': (537325.0007644, 680040.9534535999),
        'ylim': (-14119.8061776, 166744.9025856),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_vodoem.shp')
    },
    {
        'name': 'Minusinsk',
        'display_name': 'Минусинский район',
        'xlim': (712096.60938435, 864493.62974565),
        'ylim': (-205207.68312265002, -14122.19472535),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_vodoem.shp')
    },
    {
        'name': 'omsk',
        'display_name': 'Омская область',
        'xlim': (-597277.6522497501, -206999.67271325),
        'ylim': (-220174.53030275, 321998.41036675),
        'mask_shapefile': __resource('maps/Omsk/omsk_agro.shp'),
        'water_shapefile': __resource('maps/Omsk/omsk_vodoem.shp')
    },
]

