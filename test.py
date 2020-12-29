import time

from gdal_viirs.hl import NPPProcessor


processor = NPPProcessor('/media/marat/Quack/Projects/GDAL_Data/NPP', '~/Documents')
while True:
    processor.process_recent()
    time.sleep(3600)
