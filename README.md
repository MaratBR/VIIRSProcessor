# GDAL VIIRS

Библиотека на python для привязки, изменения проекции 
и ковертации VIIRS датасетов в tiff.

## Использование

### Простой пример

```python
from gdal_viirs.hl.shortcuts import process_recent
import my_config

process_recent(my_config)
```

`my_config.py`:
```python
import os
__BASE_DIR = os.path.dirname(__file__)

# по умолчанию 1000
SCALE = 2000

LOGO_PATH = os.path.join(__BASE_DIR, 'required_resources/logo.png')
ISO_QUALITY_SIGN = os.path.join(__BASE_DIR, 'required_resources/iso_sign.jpg')
IS_DEBUG = True

# конфигурация PNG файлов, где
# name - уникальный идентификатор изображения
# display_name - имя, которое будет размещено на изображении
# xlim и ylim - массив или кортеж с 2 элементами (предел по X и Y в проекции)
# mask_shapefile - shp файл с маской посевов
# можно добавлять несколько конфигураций в список, чтобы сгенерировать несколько изображений
PNG_CONFIG = [
    {
        'name': 'novosibirsk',
        'display_name': 'Новосибирская область',
        'xlim': (-300000, 350000),
        'ylim': (-280000, 240000),
        'mask_shapefile': os.path.join(__BASE_DIR, 'required_resources/novosib/novosib_agro.shp')
    }
]

# входые данные и папка с выходными
INPUT_DIR = '/media/marat/Quack/Projects/GDAL_Data/NPP/'
OUTPUT_DIR = '/home/marat/Documents'

FONT_FAMILY = '/home/marat/Downloads/Agro/Font/times.ttf'

# дополнительный точки на карте (Томск уже есть по-умолчанию и показан просто как пример)
# MAP_POINTS = [
#     (84.948197, 56.484680, 'Томск')
# ]

# папка с БД файлом (по умолчанию ~/.config/viirs_processor)
# CONFIG_DIR = ''
```


### Еще более простой пример
1. Отредактировать config.py
2. `python3 processor.py`
3. PROFIT

## Обработка файлов
При структуре папок:
```
/корневая
    /NPP_47470_25-DEC-2020_080844
        /viirs
            /level1
            /level2
    /NPP_47498_27-DEC-2020_073021
        /viirs
            /level1
            /level2
```

`NPPProcessor` создаст следующие файлы:

| Файл                                                  | Назначение                                      | Прочее  
|-------------------------------------------------------|-------------------------------------------------|----------
| NPP_47470_25-DEC-2020_080844.GIMGO.tiff               |Файл содержащий проецированные данные с привязкой|
| NPP_47470_25-DEC-2020_080844.NDVI.tiff                |NDVI с наложением маски облачности               |Значения от -1 до 1, -2 обозначает закрытую облачностью зону
| NPP_47470_25-DEC-2020_080844.PROJECTED_CLOUDMASK.tiff |Проецированная маска облачности                  |
| Папка PNG.2021_Jan_13                                 |Изображения с картой                             |

_Примечание:_ если при обрезке по маске облачности происходит ошибку ПО продолжает работать и логирует
ошибку. В выходном файле NDVI не будет значений -2, обозначающих облачность.

## Траблшутинг

## Minimum supported proj version is 7.2.0, installed version is #.#.#

```
Collecting pyproj
  Using cached https://files.pythonhosted.org/packages/17/e5/3f5cdff3e955bcd768cdb0f4236f2d6e022aaa72f57caf7f4d5f552c88fc/pyproj-3.0.0.post1.tar.gz
    Complete output from command python setup.py egg_info:
    ERROR: Minimum supported proj version is 7.2.0, installed version is 4.9.3. For more information see: https://pyproj4.github.io/pyproj/stable/installation.html
    
    ----------------------------------------
Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-hmj8c_nf/pyproj/
```
Проблема: версия PROJ не поддерживается, необходимо изменить версию PROJ или установить более старую версию pyproj.
Решение: обновить PROJ или закомментировать `pyproj` в requirements.txt и установить pyproj нужной версии в ручную 
(подробнее: https://pyproj4.github.io/pyproj/stable/installation.html). 