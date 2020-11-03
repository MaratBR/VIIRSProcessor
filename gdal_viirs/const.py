from gdal_viirs.types import Number

ND_NA = 65535
ND_MISS = 65534
ND_OBPT = 65533
ND_OGPT = 65532
ND_ERR = 65531
ND_ELINT = 65530
ND_VDNE = 65529
ND_SOUB = 65528
_ND_MIN_VALUE = 65528


def is_nodata(v):
    return v >= _ND_MIN_VALUE

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
     PARAMETER["Central_Meridian",79.950619],
     PARAMETER["Standard_Parallel_1",67.41206675],
     PARAMETER["Standard_Parallel_2",43.58046825],
     PARAMETER["Scale_Factor",1.0],
     PARAMETER["Latitude_Of_Origin",55.4962675],
     UNIT["Meter",%(scale)d]
]'''

PROJ_WGS = '''GEOGCS["WGS 84",
DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],
AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]
'''


def lcc_proj(scale: Number):
    return PROJ_LCC % {'scale': scale}


GITCO = 'GITCO'
GMTCO = 'GMTCO'
GIMGO = 'GIMGO'
GMODO = 'GMODO'
GDNBO = 'GDNBO'

GIGTO = 'GIGTO'
GMGTO = 'GMGTO'
GNCCO = 'GNCCO'
