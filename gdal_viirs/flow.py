import inspect
from typing import Union, List, Callable

import luigi
import gdal_viirs.utility as _utils


class FindDatasets(luigi.Task):
    directories: Union[List[str], Callable[[], List[str]]] = luigi.Parameter(significant=True, description='список папок, где искать датасеты или функция возвращающая список папок')

    def run(self):
        if inspect.isfunction(self.directories):
            dirs = self.directories()
        else:
            dirs = self.directories

        datasets = [_utils.find_sdr_viirs_filesets(d) for d in dirs]
        datasets = [item for sublist in datasets for item in sublist.values()]
        return datasets
