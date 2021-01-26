import os
import re
from glob import glob
from pathlib import Path
import subprocess

res = Path(__file__).parent.parent / 'required_resources' / 'maps'

names = {'region': None, 'altkrai': 'Алтайский край', 'novosib': 'Новосибирская область', 'severn_nso': 'Северный район', 'cherep_nso': 'Черепановский район', 'ust_tar_nso': 'Усть-Таркский район', 'kupino_nso': 'Купинский район', 'tatarsk_nso': 'Татарский район', 'karasuk_nso': 'Карасукский район', 'kolivan_nso': 'Коливанский район', 'kuibichev_nso': 'Куйбышевский район', 'iskitim_nso': 'Искитимский район', 'susun_nso': 'Сузунский район', 'mochkov_nso': 'Мошковский район', 'chistoz_nso': 'Чистоозёрный район', 'kichtov_nso': 'Кыштовский район', 'zdvinsk_nso': 'Здвинский район', 'kochki': 'Кочковский район', 'kargat_nso': 'Каргатский район', 'bolotno_nso': 'Болотнинский район', 'barabin_nso': 'Барабинский район', 'maslyan_nso': 'Маслянинский район', 'toguchi_nso': 'Тогучинский район', 'chani_nso': 'Чановский район', 'chulim_nso': 'Чулымский район', 'ordinsk_nso': 'Ординский район', 'krasnoz_nso': 'Краснозёрский район', 'ubinsk_nso': 'Убинский район', 'vengero_nso': 'Венгеровский район', 'dovolno_nso': 'Доволенский район', 'kochene_nso': 'Коченёвский район', 'bagan_nso': 'Баганский район', 'novosib_nso': 'Новосибирский район', 'kem': 'Кемеровская область', 'krasn': 'Красноярский край', 'Kansk': 'Канский район', 'Krasn_Gr': 'Красноярская группа районов', 'Achinsk': 'Ачинский район', 'Minusinsk': 'Минусинский район', 'omsk': 'Омская область'}
strings = ['PNG_CONFIG = [\n\t']


def get_entry_repr(shp):
    proc = subprocess.Popen(['ogrinfo', '-ro', '-so', '-al', shp],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    data = proc.stdout.read().decode('utf-8')
    data = data.split('Extent: ')
    if len(data) == 1:
        print(data[0])
    data = data[1].split('\n', 1)[0]

    match = re.match(r'\((.*)\) - \((.*)\)', data)
    xlim, ylim = match.groups()
    xlim = xlim.split(', ')
    ylim = ylim.split(', ')
    xlim = float(xlim[0]), float(xlim[1])
    ylim = float(ylim[0]), float(ylim[1])
    xlim, ylim = (xlim[0], ylim[0]), (xlim[1], ylim[1])
    xsize = abs(xlim[0] - xlim[1])
    ysize = abs(ylim[0] - ylim[1])
    padding = max(ysize * 0.025, xsize * 0.025)
    xlim = xlim[0] - padding, xlim[1] + padding
    ylim = ylim[0] - padding, ylim[1] + padding
    xlim = f'{xlim[0]}, {xlim[1]}'
    ylim = f'{ylim[0]}, {ylim[1]}'

    p = Path(shp)
    name = p.parts[-1].split('_agro')[0]
    shp_file = str(p).split('required_resources/')[1]

    water_part = ''
    water_shp = glob(str(p.parent / '*_vodoem.shp'))
    if len(water_shp) != 0:
        water_part = """,
        'water_shapefile': __resource('%s')""" % water_shp[0].split('required_resources/')[1]

    return '''
    {
        'name': '%s',
        'display_name': %s,
        'xlim': (%s),
        'ylim': (%s),
        'mask_shapefile': __resource('%s')%s
    },''' % (name, names[name] if names[name] is None else f"'{names[name]}'", xlim, ylim, shp_file, water_part)


for f in os.listdir(res):
    shp = glob(str(res / f / '*_agro.shp'))
    if len(shp) == 0:
        raise RuntimeError()
    strings.append(get_entry_repr(shp[0]))

    for sf in os.listdir(res / f):
        p = res / f / sf
        if p.is_file():
            continue
        shp = glob(str(res / f / sf / '*_agro.shp'))
        if len(shp) == 0:
            raise RuntimeError()
        strings.append(get_entry_repr(shp[0]))

strings.append('\n]')
print(''.join(strings))


