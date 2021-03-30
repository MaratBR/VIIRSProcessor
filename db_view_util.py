#!/usr/bin/python3
import json
import os

from gdal_viirs.hl.shortcuts import setup_env
from gdal_viirs.persistence.models import *


def print_help():
    print()
    print('Пометка (БИТЫЙ) означает, что файл есть в БД но отсутвует в файловой системе')
    print()


def print_l1():
    l1 = ProcessedViirsL1.select()

    print('level1 обработанные файлы')
    print('========================')

    for record in l1:
        if not os.path.isfile(record.output_file):
            print('(БИТЫЙ)', end=' ')
        print(f'{record.type}, файл: {record.output_file}')

    print('\n')


def print_ndvi_composites():
    composites = NDVIComposite.select().order_by(NDVIComposite.created_at)

    print('композиты')
    print('========================')

    for record in composites:
        if not os.path.isfile(record.output_file):
            print('(БИТЫЙ)', end=' ')
        print(f'id={record.id}, файл: {record.output_file} создано {record.created_at}')
        print(f'\tДанный композит состоит из {len(record.components)} компонентов')

        for component in record.components:
            c = component.component
            print('\t', end='')
            if not os.path.isfile(c.output_file):
                print('(БИТЫЙ)', end=' ')
            print(f'id={c.id}, {c.output_file} создано {c.created_at}')
    print()


def print_ndvi_dynamics():
    dynamics = NDVIDynamicsTiff.select().order_by(NDVIDynamicsTiff.created_at)

    print('динамика')
    print('========================')

    for d in dynamics:
        if not os.path.isfile(d.output_file):
            print('(БИТЫЙ)', end=' ')
        print(f'id={d.id}, {d.output_file}')
        print(f'\tПериод: {d.date_text}')
        print(f'\tb1: id={d.b1_composite.id}, {d.b1_composite.output_file} период: {d.b1_composite.date_text}')
        print(f'\tb2: id={d.b2_composite.id}, {d.b2_composite.output_file} период: {d.b2_composite.date_text}')

    print()


def print_meta():
    print('мета-данные')
    print('========================')
    for meta in MetaData.select():
        print(f'{meta.key} = {json.dumps(meta.value)}')
    print()


if __name__ == '__main__':
    with setup_env('config'):
        print_help()
        print_l1()
        print_ndvi_composites()
        print_ndvi_dynamics()
        print_meta()
        print_help()
