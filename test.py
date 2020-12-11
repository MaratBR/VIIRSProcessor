import gdal_viirs.v2 as gv
import gdal_viirs.persistence.db as p

db = p.GDALViirsDB('test.db')
filesets = gv.utility.find_sdr_viirs_filesets('/home/marat/Documents/npp')

for fs in filesets.values():
    db.add_fileset(fs)

