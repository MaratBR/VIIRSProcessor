import csv

import typing
from datetime import date

from loguru import logger

from gdal_viirs.misc import julian2date


def read_cvs_gradation_file(filename, delimiter=';') -> typing.Dict[str, typing.Tuple[float, float]]:
    gradations = {}
    with open(filename) as f:
        reader = csv.reader(f, delimiter=delimiter)
        line = 1
        rows = list(reader)[1:]
        for row in rows:
            try:
                d = julian2date(row[0])
                bad = float(row[1])
                good = float(row[2])
                gradations[d.strftime('%m%d')] = bad, good
                line += 1
            except Exception as exc:
                logger.error(f'Не удалось обработать строку {line} из файла {filename}: {exc}')
    return gradations
