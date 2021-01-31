from gdal_viirs.config import req_resource_path


def get_russia_admin_shp(level):
    return str(req_resource_path(f'russia_adm/admin_level_{level}.shp'))


