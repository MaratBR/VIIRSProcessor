import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

from loguru import logger

from gdal_viirs.types import ViirsFileset
from gdal_viirs.utility import find_sdr_viirs_filesets


@dataclass
class NPPViirsFileset(ViirsFileset):
    swath_id: Optional[str] = None

    @property
    def root_dir(self):
        return self.geoloc_file.path_obj.parent.parent.parent


def find_npp_viirs_filesets(root_dir, **kwargs) -> List[NPPViirsFileset]:
    filesets = []
    for fs in find_sdr_viirs_filesets(os.path.join(root_dir, 'viirs/level1'), **kwargs).values():
        dirname = fs.geoloc_file.path_obj.parts[-4]
        match = re.match(r'^[a-zA-Z]+_(\d+)_.*', dirname)
        if match:
            fs = NPPViirsFileset(**asdict(fs), swath_id=match.group(1))
            filesets.append(fs)
        else:
            logger.warning(f'Папка {dirname} не сооответствует шаблону и не начинается на ЧТОТО_12345_... (где 12345 - '
                           f'номер витка), папка будет проигнорирована)')
    return filesets


def today_folder_name():
    return datetime.now().strftime('%Y%m%d')