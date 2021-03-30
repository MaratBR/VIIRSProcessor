import os
import re
import subprocess
from glob import glob


def main():
    borders = glob('/home/marat/Downloads/Вектора_Lambert/**/*_admpol.shp', recursive=True)

    for file in borders:
        proc = subprocess.Popen(['ogrinfo', '-ro', '-so', '-al', file],
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

        print(os.path.basename(file), xlim, ylim)


if __name__ == '__main__':
    main()
