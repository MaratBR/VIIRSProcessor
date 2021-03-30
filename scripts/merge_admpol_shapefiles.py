import os
from collections import OrderedDict
from glob import glob
from pathlib import Path

import fiona


def merge_shapefiles(files, output):
    print(f'merging {files}')
    meta = fiona.open(files[0]).meta.copy()
    d = OrderedDict()
    d['name_adm1'] = 'str:254'
    d['name_adm2'] = 'str:254'
    meta['schema']['properties'] = d
    with fiona.open(output, 'w', **meta) as out:
        for ap in files:
            with fiona.open(ap) as f:
                for feature in f:
                    new_props = OrderedDict()
                    new_props['name_adm1'] = feature['properties'].get('name_adm1')
                    new_props['name_adm2'] = feature['properties'].get('name_adm2')
                    feature['properties'] = new_props
                    out.write(feature)


def main():
    location = os.path.expanduser('~/Downloads/Вектора_Lambert')
    Path('/tmp/adm').mkdir(exist_ok=True)
    merge_shapefiles(glob(os.path.join(location, 'Krasnoyarsk/*/*_border.shp')), '/tmp/adm/krasn_groups_border.shp')
    merge_shapefiles(glob(os.path.join(location, 'Krasnoyarsk/krasn_border.shp')), '/tmp/adm/krasn_border.shp')
    merge_shapefiles(glob(os.path.join(location, 'Krasnoyarsk/**/*_admpol.shp'), recursive=True),
                     '/tmp/adm/krasn_admpol.shp')
    merge_shapefiles(glob(os.path.join(location, 'Novosibirsk/**/*_admpol.shp'), recursive=True),
                     '/tmp/adm/nsk_admpol.shp')
    merge_shapefiles(glob(os.path.join(location, 'Novosibirsk/novosib_border.shp'), recursive=True),
                     '/tmp/adm/nsk_border.shp')
    merge_shapefiles(glob(os.path.join(location, 'Kemerovo/kem_border.shp'), recursive=True), '/tmp/adm/kem_border.shp')
    merge_shapefiles(glob(os.path.join(location, 'Kemerovo/*_admpol.shp'), recursive=True), '/tmp/adm/kem_admpol.shp')
    merge_shapefiles(glob(os.path.join(location, 'Omsk/*_admpol.shp'), recursive=True), '/tmp/adm/omsk_admpol.shp')
    merge_shapefiles(glob(os.path.join(location, 'Omsk/omsk_border.shp'), recursive=True), '/tmp/adm/omsk_border.shp')
    merge_shapefiles(glob(os.path.join(location, 'Region/region_border.shp'), recursive=True),
                     '/tmp/adm/region_border.shp')
    merge_shapefiles(glob(os.path.join(location, 'Altai/altkrai_admpol.shp'), recursive=True),
                     '/tmp/adm/altkrai_admpol.shp')
    merge_shapefiles(glob(os.path.join(location, 'Altai/altkrai_border.shp'), recursive=True),
                     '/tmp/adm/altkrai_border.shp')


if __name__ == '__main__':
    main()
