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

processor = gdal_viirs.hl.NPPProcessor('/папка/содержащая/данные/со/спутника', '/папка/для/выходных/данных')

while True:
    processor.process_recent()
    time.sleep(3600)
```

По умолчанию NPPProcessor будет хранить информацию в SQLite БД в `~/.viirs_processor/store.db`. Расположение
файла БД можно изменить, передав папку с файлом третьим аргументом в конструктор `NPPProcessor`:
```python
processor = gdal_viirs.hl.NPPProcessor(
    '/папка/содержащая/данные/со/спутника', 
    '/папка/для/выходных/данных',
    '/etc/viirs_config')
```

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

_Примечание:_ если при обрезке по маске облачности происходит ошибку ПО продолжает работать и логирует
ошибку. В выходном файле NDVI не будет значений -2, обозначающих облачность.