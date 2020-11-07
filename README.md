# GDAL VIIRS

Библиотека на python для привязки, изменения проекции 
и ковертации VIIRS датасетов в tiff.

## Использование 

### `gdal_viirs.py show`

Получает список VIIRS файлов и формирует наборы файлов (геолакоционный
файл и несколько Band-файлов: M или I)

Пример:
```
$ ./gdal_viirs.py show ~/Documents/npp
```

Вывод:

```
Наборов файлов: 3
Всего файлов: 22
=======================
SDR GMODO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
 Band: M, M-band
 Полный путь: /home/marat/Documents/npp/GMODO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
 Номер орбиты: 00001
 Дата: 2020-10-20
 Время: 07:06:41.500000 - 07:19:29.700000
 ID спутника: npp
 M-band: 16 файлов
=======================
SDR GIMGO_npp_d20201013_t0557093_e0609574_b00001_c20201013052242733000_ipop_dev.h5
 Band: I, I-band
 Полный путь: /home/marat/Documents/npp/GIMGO_npp_d20201013_t0557093_e0609574_b00001_c20201013052242733000_ipop_dev.h5
 Номер орбиты: 00001
 Дата: 2020-10-13
 Время: 05:57:09.300000 - 06:09:57.400000
 ID спутника: npp
 I-band: 5 файлов
=======================
SDR GDNBO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
 Band: DN, Day/Night
 Полный путь: /home/marat/Documents/npp/GDNBO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
 Номер орбиты: 00001
 Дата: 2020-10-20
 Время: 07:06:41.500000 - 07:19:29.700000
 ID спутника: npp
 DN-band: 1 файлов
```

### `gdal_viirs.py process`

Производит обработку файлов в указанной папке:

```
$ ./gdal_viirs.py process ~/Documents/npp
```

```
Папка с файлами: /home/marat/Documents/npp
Папка вывода: /tmp
2020-11-07 16:27:42.934 | INFO     | gdal_viirs.process:hlf_process_geoloc_file:56 - ОБРАБОТКА GMODO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:44.014 | INFO     | gdal_viirs.process:hlf_process_geoloc_file:71 - ПРОЕКЦИЯ...
2020-11-07 16:27:51.373 | INFO     | gdal_viirs.process:hlf_process_geoloc_file:73 - ПРОЕКЦИЯ. ГОТОВО: 7s
2020-11-07 16:27:51.550 | INFO     | gdal_viirs.process:hlf_process_geoloc_file:82 - ОБРАБОТКА ЗАВЕРШЕНА GMODO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:51.551 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM01_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:52.925 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 373.316ms
2020-11-07 16:27:52.926 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM02_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:54.103 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 175.774ms
2020-11-07 16:27:54.105 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM03_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:55.279 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 172.861ms
2020-11-07 16:27:55.281 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM04_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:56.451 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 169.641ms
2020-11-07 16:27:56.454 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM05_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:57.602 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 147.824ms
2020-11-07 16:27:57.605 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM06_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:27:58.854 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 249.099ms
2020-11-07 16:27:58.856 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM07_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:00.079 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 222.024ms
2020-11-07 16:28:00.081 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM08_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:01.258 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 177.163ms
2020-11-07 16:28:01.260 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM09_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:02.569 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 308.273ms
2020-11-07 16:28:02.571 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM10_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:03.892 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 320.78ms
2020-11-07 16:28:03.894 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM11_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:05.312 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 417.698ms
2020-11-07 16:28:05.314 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM12_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:06.481 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 166.697ms
2020-11-07 16:28:06.484 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM13_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:07.658 | WARNING  | gdal_viirs.process:hlf_process_band_file:132 - Не удалось получить BrightnessTemperatureFactors
2020-11-07 16:28:07.658 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 173.723ms
2020-11-07 16:28:07.663 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM14_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:08.924 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 260.639ms
2020-11-07 16:28:08.926 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM15_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:10.105 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 178.288ms
2020-11-07 16:28:10.107 | INFO     | gdal_viirs.process:hlf_process_band_file:94 - ОБРАБОТКА M-band: SVM16_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5
2020-11-07 16:28:11.343 | INFO     | gdal_viirs.process:hlf_process_band_file:134 - ОБРАБОТАН M-band: 236.007ms
2020-11-07 16:28:11.346 | INFO     | gdal_viirs.save:save_as_tiff:16 - Записываем: /tmp/GMODO_npp_d20201020_t0706415_e0719297_b00001_c20201020063255132000_ipop_dev.h5--M
2020-11-07 16:28:12.098 | INFO     | gdal_viirs.process:hlf_process_geoloc_file:56 - ОБРАБОТКА GIMGO_npp_d20201013_t0557093_e0609574_b00001_c20201013052242733000_ipop_dev.h5
....
```

Папка, куда будут помещены файлы может быть установлена с помощь флага `-o`:

```

```
$ ./gdal_viirs.py process ~/Documents/npp -o /path/to/my/folder
```
Папка с файлами: /home/marat/Documents/npp
Папка вывода: /path/to/my/folder
...
```

## TODO

- [ ] Масштаб можно регулировать через аргументы CLI 
- [ ] Поддержка crud или тип того
- [ ] Сразу сбрасывать результаты на диск, чтобы не забивать память
- [ ] ???