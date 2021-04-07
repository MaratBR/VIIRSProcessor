import numpy as np
import rasterio
from rasterio.plot import show
from matplotlib import pyplot

f = rasterio.open('/media/marat/Quack/Projects/GDAL_Data/NPP/NPP_48293_21-FEB-2021_082144/viirs/level1/GIMGO_npp_d20210221_t0821238_e0832466_b00001_c20210221100336573000_ipop_dev.h5')

# тут короче список датасетов, которые есть в h5 файле
subdatasets = f.subdatasets
# для примера я достану долготу и её буду использовать
latitude = next(d for d in subdatasets if d.endswith('Latitude'))
print(latitude)

f.close()
f = rasterio.open(latitude)

# достаю данные (если указать число, как я это сделал, то прочитает указанные канал (band в GDAL),
# если не указывать число прочитает все каналы и вернет 3-х мерный массив)
data = f.read(1)  # получаем 1 канал
show(data, cmap='Purples')
# рисуем данные
# cmap - то, как отображать данные (в данном случае предустановленный градиент от белого к пурпурному)
pyplot.imsave('test.png')
f.close()
