# GDAL VIIRS

Библиотека на python для привязки, изменения проекции 
и ковертации VIIRS датасетов в tiff.

## Использование

### Простой пример

```python
import gdal_viirs
folder = '/путь/к/папке/с_viirs_данными'
datasets = gdal_viirs.utility.find_sdr_viirs_filesets(folder)

for filename, dataset in datasets.items():
    print(f"обработка {filename}...")
    gdal_viirs.process.process_fileset(dataset, "/папка/куда/положить/данные")
``` 

### Пример с БД

```python
import gdal_viirs
import time

def get_data_directories():
    # данная функция должна вернуть список всех папок, в которых 
    # следует искать датасеты
    # например можно использовать glob
    # return glob.glob('/mnt/199/NPP/NPP_*/viirs/level1')
    return [
        '/путь/к/папке/с_viirs_данными_1',
        '/путь/к/папке/с_viirs_данными_2',
        '/путь/к/папке/с_viirs_данными_3',
        '/путь/к/папке/с_viirs_данными_4',
    ]

processor = gdal_viirs.hl.ViirsProcessor(get_data_directories, '/папка/для/выходных/данных')

while True:
    # данная функция получит список всех датасетов и обработает те, которые еще не были обработаны
    # подробнее см. секцию "ViirsProcessor"
    processor.process_recent_files()
    time.sleep(3600)
```

### Пример с ООП
coming soon™

## Документация
coming soon™
