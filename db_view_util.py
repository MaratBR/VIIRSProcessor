from gdal_viirs.persistence.models import *


def print_l1():
    l1 = ProcessedViirsL1.get()

    for record in l1:
        print(f'{record.type}, файл: {record.output_file}')


if __name__ == '__main__':
    print_l1()
