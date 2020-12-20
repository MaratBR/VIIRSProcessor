import time

from gdal_viirs.hl import ViirsProcessor

proc = ViirsProcessor('~/Downloads', '~/Documents', make_ndvi=True)
proc.reset_counter()

while True:
    proc.process_recent_files()
    time.sleep(60 * 60)