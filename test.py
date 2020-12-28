from gdal_viirs.hl import ViirsProcessor


processor = ViirsProcessor('/media/marat/Quack/Projects/GDAL_Data/NPP', '~/Documents')
processor.process_recent()
