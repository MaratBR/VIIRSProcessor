import os
from collections import OrderedDict
from glob import glob

import fiona


def main():
    location = os.path.expanduser('~/Downloads/Вектора_Lambert')
    admpol = glob(os.path.join(location, '**/*_admpol.shp'), recursive=True)
    meta = fiona.open(admpol[0]).meta.copy()
    d = OrderedDict()
    d['name_adm1'] = 'str:254'
    d['name_adm2'] = 'str:254'
    meta['schema']['properties'] = d
    with fiona.open('/tmp/admpol.shp', 'w', **meta) as out:
        for ap in admpol:
            with fiona.open(ap) as f:
                for feature in f:
                    new_props = OrderedDict()
                    new_props['name_adm1'] = feature['properties']['name_adm1']
                    new_props['name_adm2'] = feature['properties']['name_adm2']
                    feature['properties'] = new_props
                    out.write(feature)

    border = glob(os.path.join(location, '**/*_border.shp'), recursive=True)
    meta = fiona.open(border[0]).meta.copy()
    d = OrderedDict()
    meta['schema']['properties'] = d
    with fiona.open('/tmp/border.shp', 'w', **meta) as out:
        for brd in border:
            with fiona.open(brd) as f:
                for feature in f:
                    new_props = OrderedDict()
                    feature['properties'] = new_props
                    out.write(feature)


if __name__ == '__main__':
    main()
