"""
const.py содержит определение констант, которые используются
в библиотеке
"""

ND_NA = 65535
ND_MISS = 65534
ND_OBPT = 65533
ND_OGPT = 65532
ND_ERR = 65531
ND_ELINT = 65530
ND_VDNE = 65529
ND_SOUB = 65528


def is_nodata(v):
    """
    Создает маску nodata значений или (если передано число) возвращает True или False,
    в зависимости от того является значение nodata или нет
    :param v:
    :return:
    """
    return v >= ND_SOUB  # минимальное значение 65528


# Проекция по умолчанию
PROJ_LCC = '''PROJCS["Lambert_Conformal_Conic",
     GEOGCS["GCS_WGS_1984",
         DATUM["WGS_1984",
             SPHEROID["WGS_84",6378137.0,298.252223563]
         ],
         PRIMEM["Greenwich",0.0],
         UNIT["Degree",0.0174532925199433]
     ],
     PROJECTION["Lambert_Conformal_Conic_2SP"],
     PARAMETER["False_Easting",0.0],
     PARAMETER["False_Northing",0.0],
     PARAMETER["Central_Meridian",80],
     PARAMETER["Standard_Parallel_1",67.41206675],
     PARAMETER["Standard_Parallel_2",43.58046825],
     PARAMETER["Scale_Factor",1],
     PARAMETER["Latitude_Of_Origin",55.4962675],
     UNIT["Meter",1.0]
]'''

# Типы VIIRS файлов

GITCO = 'GITCO'
GMTCO = 'GMTCO'
GIMGO = 'GIMGO'
GMODO = 'GMODO'
GDNBO = 'GDNBO'
GIGTO = 'GIGTO'
GMGTO = 'GMGTO'
GNCCO = 'GNCCO'