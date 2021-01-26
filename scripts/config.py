import os
__BASE_DIR = os.path.dirname(__file__)


def __resource(path):
    return os.path.join(__BASE_DIR, 'required_resources', path)


# по умолчанию 1000
SCALE = 2000
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
        'xlim': (-590979.828106725, -510118.41845727497),
        'ylim': (566920.691299275, 315700.586223725),
        'mask_shapefile': __resource('maps/Region/region_agro.shp'),
        'water_shapefile': __resource('maps/Region/region_vodoem.shp')
    },
    {
        'name': 'altkrai',
        'display_name': 'Алтайский край',
        'xlim': (-148102.793476925, -502728.790396075),
        'ylim': (432583.353721075, -99442.617680075),
        'mask_shapefile': __resource('maps/Altai/altkrai_agro.shp'),
        'water_shapefile': __resource('maps/Altai/altkrai_vodoem.shp')
    },
    {
        'name': 'novosib',
        'display_name': 'Новосибирская область',
        'xlim': (-303641.2442337, -226221.31209030002),
        'ylim': (319054.12354530004, 175142.7566267),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib_vodoem.shp')
    },
    {
        'name': 'severn_nso',
        'display_name': 'Северный район',
        'xlim': (-144872.63989185, 34108.16014785),
        'ylim': (-75406.72442085, 137717.07231885),
        'mask_shapefile': __resource('maps/Novosibirsk/severn/severn_nso_agro.shp')
    },
    {
        'name': 'cherep_nso',
        'display_name': 'Черепановский район',
        'xlim': (162439.479753725, -155758.454927725),
        'ylim': (249930.246342725, -95483.78728772499),
        'mask_shapefile': __resource('maps/Novosibirsk/cherep/cherep_nso_agro.shp')
    },
    {
        'name': 'ust_tar_nso',
        'display_name': 'Усть-Таркский район',
        'xlim': (-305716.2565267, 6564.049252700001),
        'ylim': (-223781.2379157, 82945.45362670001),
        'mask_shapefile': __resource('maps/Novosibirsk/ust_tar/ust_tar_nso_agro.shp')
    },
    {
        'name': 'kupino_nso',
        'display_name': 'Купинский район',
        'xlim': (-226179.783778925, -175153.574072075),
        'ylim': (-109929.382896925, -80264.584666075),
        'mask_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kupino/kupino_nso_vodoem.shp')
    },
    {
        'name': 'tatarsk_nso',
        'display_name': 'Татарский район',
        'xlim': (-305677.932378375, -73327.166827625),
        'ylim': (-223207.210485375, 21393.623448375),
        'mask_shapefile': __resource('maps/Novosibirsk/tatarsk/tatarsk_nso_agro.shp')
    },
    {
        'name': 'karasuk_nso',
        'display_name': 'Карасукский район',
        'xlim': (-179367.734905475, -228709.97336552502),
        'ylim': (-83226.30091247501, -131471.092668525),
        'mask_shapefile': __resource('maps/Novosibirsk/karasuk/karasuk_nso_agro.shp')
    },
    {
        'name': 'Коливанский район',
        'display_name': 'ЗАПОЛНИТЬ',
        'xlim': (137017.7268518, -27975.5317218),
        'ylim': (215584.0865258, 52682.374418199994),
        'mask_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kolivan/kolivan_nso_vodoem.shp')
    },
    {
        'name': 'kuibichev_nso',
        'display_name': 'Куйбышевский район',
        'xlim': (-160528.2169963, -12572.3551957),
        'ylim': (-23511.9806123, 77566.07821729999),
        'mask_shapefile': __resource('maps/Novosibirsk/kuibichev/kuibichev_nso_agro.shp')
    },
    {
        'name': 'iskitim_nso',
        'display_name': 'Искитимский район',
        'xlim': (148252.715804925, -123779.393348925),
        'ylim': (248912.39565392502, -57668.818682925004),
        'mask_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/iskitim/iskitim_nso_vodoem.shp')
    },
    {
        'name': 'susun_nso',
        'display_name': 'Сузунский район',
        'xlim': (106175.09002999999, -195061.34933000003),
        'ylim': (171997.432196, -107532.353548),
        'mask_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/susun/susun_nso_vodoem.shp')
    },
    {
        'name': 'mochkov_nso',
        'display_name': 'Мошковский район',
        'xlim': (188216.58796590002, -30256.494466899996),
        'ylim': (254403.0774229, 20437.678351100003),
        'mask_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/mochkov/mochkov_nso_vodoem.shp')
    },
    {
        'name': 'chistoz_nso',
        'display_name': 'Чистоозёрный район',
        'xlim': (-270168.902683125, -127609.713583875),
        'ylim': (-180631.266423125, -44575.712019875005),
        'mask_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chistoz/chistoz_nso_vodoem.shp')
    },
    {
        'name': 'kichtov_nso',
        'display_name': 'Кыштовский район',
        'xlim': (-253542.105538825, 112606.847777825),
        'ylim': (-149215.194718825, 180073.447613825),
        'mask_shapefile': __resource('maps/Novosibirsk/kichtov/kichtov_nso_agro.shp')
    },
    {
        'name': 'zdvinsk_nso',
        'display_name': 'Здвинский район',
        'xlim': (-121907.963106575, -133560.167608425),
        'ylim': (-38710.440200575, -49326.414720425),
        'mask_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/zdvinsk/zdvinsk_nso_vodoem.shp')
    },
    {
        'name': 'kochki',
        'display_name': 'Кочковский район',
        'xlim': (-11482.061918475, -168195.284252525),
        'ylim': (64283.369734525, -96553.828279525),
        'mask_shapefile': __resource('maps/Novosibirsk/kochki/kochki_agro.shp')
    },
    {
        'name': 'kargat_nso',
        'display_name': 'Каргатский район',
        'xlim': (-26224.859732075, -111730.14511692499),
        'ylim': (55107.477228925, -7226.578838924999),
        'mask_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/kargat/kargat_nso_vodoem.shp')
    },
    {
        'name': 'bolotno_nso',
        'display_name': 'Болотнинский район',
        'xlim': (222909.2040709, 2845.0257781),
        'ylim': (292103.5849019, 56387.3284201),
        'mask_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/bolotno/bolotno_nso_vodoem.shp')
    },
    {
        'name': 'barabin_nso',
        'display_name': 'Барабинский район',
        'xlim': (-159355.35279560002, -85593.0944804),
        'ylim': (-62087.9236256, -5393.8211634),
        'mask_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/barabin/barabin_nso_vodoem.shp')
    },
    {
        'name': 'maslyan_nso',
        'display_name': 'Маслянинский район',
        'xlim': (232666.36851554998, -126983.07929855),
        'ylim': (298299.68774655, -79692.33751254999),
        'mask_shapefile': __resource('maps/Novosibirsk/maslyan/maslyan_nso_agro.shp')
    },
    {
        'name': 'toguchi_nso',
        'display_name': 'Тогучинский район',
        'xlim': (210597.35966480002, -59581.6017018),
        'ylim': (315011.73607680004, 17489.645355200002),
        'mask_shapefile': __resource('maps/Novosibirsk/toguchi/toguchi_nso_agro.shp')
    },
    {
        'name': 'chani_nso',
        'display_name': 'Чановский район',
        'xlim': (-230245.35850792498, -53767.905513075),
        'ylim': (-152071.496872925, 19111.587813924998),
        'mask_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/chani/chani_nso_vodoem.shp')
    },
    {
        'name': 'chulim_nso',
        'display_name': 'Чулымский район',
        'xlim': (31828.030834725, -111423.412601725),
        'ylim': (99850.882786725, -19404.295438725),
        'mask_shapefile': __resource('maps/Novosibirsk/chulim/chulim_nso_agro.shp')
    },
    {
        'name': 'ordinsk_nso',
        'display_name': 'Ординский район',
        'xlim': (57983.786390575, -141301.250373575),
        'ylim': (148653.711000575, -75192.02113357499),
        'mask_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ordinsk/ordinsk_nso_vodoem.shp')
    },
    {
        'name': 'krasnoz_nso',
        'display_name': 'Краснозёрский район',
        'xlim': (-94260.84489215, -199418.94297884998),
        'ylim': (-4140.57785315, -121599.33884685),
        'mask_shapefile': __resource('maps/Novosibirsk/krasnoz/krasnoz_nso_agro.shp')
    },
    {
        'name': 'ubinsk_nso',
        'display_name': 'Убинский район',
        'xlim': (-62140.193145774996, -74687.515055225),
        'ylim': (530.992663225, 24647.139141775002),
        'mask_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/ubinsk/ubinsk_nso_vodoem.shp')
    },
    {
        'name': 'vengero_nso',
        'display_name': 'Венгеровский район',
        'xlim': (-239793.858216425, 10801.876967425),
        'ylim': (-146771.048538425, 87423.278182425),
        'mask_shapefile': __resource('maps/Novosibirsk/vengerovo/vengero_nso_agro.shp')
    },
    {
        'name': 'dovolno_nso',
        'display_name': 'Доволенский район',
        'xlim': (-67701.8091283, -145305.42283969998),
        'ylim': (25894.5638077, -63935.31291569999),
        'mask_shapefile': __resource('maps/Novosibirsk/dovolno/dovolno_nso_agro.shp')
    },
    {
        'name': 'kochene_nso',
        'display_name': 'Коченёвский район',
        'xlim': (88732.57968455, -78537.32141155),
        'ylim': (161100.97820955, -9006.623005550002),
        'mask_shapefile': __resource('maps/Novosibirsk/kochenev/kochene_nso_agro.shp')
    },
    {
        'name': 'bagan_nso',
        'display_name': 'Баганский район',
        'xlim': (-185275.48916235002, -192341.68476765),
        'ylim': (-103403.92129335, -125752.43589665),
        'mask_shapefile': __resource('maps/Novosibirsk/bagan/bagan_nso_agro.shp')
    },
    {
        'name': 'novosib_nso',
        'display_name': 'Новосибирский район',
        'xlim': (135108.24265705, -84647.79236305),
        'ylim': (212901.03586305, -19412.209843049997),
        'mask_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_agro.shp'),
        'water_shapefile': __resource('maps/Novosibirsk/novosib/novosib_nso_vodoem.shp')
    },
    {
        'name': 'kem',
        'display_name': 'Кемеровская область',
        'xlim': (265534.3107002, -216959.5405482),
        'ylim': (560834.5400842, 153226.68767780002),
        'mask_shapefile': __resource('maps/Kemerovo/kem_agro.shp'),
        'water_shapefile': __resource('maps/Kemerovo/kem_vodoem.shp')
    },
    {
        'name': 'krasn',
        'display_name': 'Красноярский край',
        'xlim': (523074.070054225, -182100.79533722502),
        'ylim': (995242.1542762249, 342286.38582377497),
        'mask_shapefile': __resource('maps/Krasnoyarsk/krasn_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/krasn_vodoem.shp')
    },
    {
        'name': 'Kansk',
        'display_name': 'Канский район',
        'xlim': (827847.4384193, 77644.0579567),
        'ylim': (994057.1933533, 317536.25096870004),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Kansk/Kansk_vodoem.shp')
    },
    {
        'name': 'Krasn_Gr',
        'display_name': 'Красноярская группа районов',
        'xlim': (640057.0566891751, -13783.035892174998),
        'ylim': (847932.030080175, 322745.413372825),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Krasn_Gr/Krasn_Gr_vodoem.shp')
    },
    {
        'name': 'Achinsk',
        'display_name': 'Ачинский район',
        'xlim': (527845.18318045, 3972.6165855500003),
        'ylim': (661948.53069045, 176224.72016955),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Achinsk/Achinsk_vodoem.shp')
    },
    {
        'name': 'Minusinsk',
        'display_name': 'Минусинский район',
        'xlim': (693713.656557325, -177725.421324325),
        'ylim': (837011.367947325, 4260.758101675001),
        'mask_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_agro.shp'),
        'water_shapefile': __resource('maps/Krasnoyarsk/Minusinsk/Minusinsk_vodoem.shp')
    },
    {
        'name': 'omsk',
        'display_name': 'Омская область',
        'xlim': (-597593.7247870001, -194040.69868600002),
        'ylim': (-233133.50433, 322314.482904),
        'mask_shapefile': __resource('maps/Omsk/omsk_agro.shp'),
        'water_shapefile': __resource('maps/Omsk/omsk_vodoem.shp')
    },
]

