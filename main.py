#!/usr/bin/python3
import sys
from io import StringIO

import gdal
import loguru

import gdal_viirs as viirs
import argparse

is_color_output_enabled = True

try:
    from termcolor import colored

    def _color(text: str, color: str) -> str:
        if is_color_output_enabled:
            return colored(text, color)
        return text
except ImportError:
    colored = None

    def _color(text, _):
        return text


def main():
    parser = argparse.ArgumentParser()

    subcommands = parser.add_subparsers()

    process_parser = subcommands.add_parser('process', help='Обработка данных')
    process_parser.set_defaults(func=process)

    process_parser.add_argument('src_dir', help='Папка с VIIRS файлами')
    process_parser.add_argument('-o', help='Папка, куда поместить готовые файлы', required=False)
    process_parser.add_argument('-E', '--no_exc', help='Не вызывать gdal.UseExceptions() при старте',
                                action="store_true")
    process_parser.add_argument('--ext', help='Расширение выходных файлов', default='tiff')
    process_parser.add_argument('--types', help='Типы файлов для обработки')
    process_parser.add_argument('-C', '--no_colors', help='Не выводить в цвете', action='store_true')
    process_parser.add_argument('-v', '--verbose', help='Подробный вывод в консоль', action='store_true')

    analyze_parser = subcommands.add_parser('analyze', help='Анализ данных')
    analyze_parser.set_defaults(func=analyze)

    analyze_parser.add_argument('src_dir', help='Папка с VIIRS файлами')
    analyze_parser.add_argument('-b', '--bands', help='Вывести список band-файлов', action='store_true')
    analyze_parser.add_argument('-C', '--no_colors', help='Не выводить в цвете', action='store_true')

    args: argparse.Namespace = parser.parse_args(sys.argv[1:])

    args.func(args)


def shorten_name(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len-2] + '..'


def analyze(args):
    if args.no_colors:
        global is_color_output_enabled
        is_color_output_enabled = False

    files = viirs.find_sdr_viirs_filesets(args.src_dir)

    files_total = 0

    ss = StringIO()

    for fileset in files.values():
        ss.write('=======================\n')
        ss.write(_color(fileset.geoloc_file.record_type, 'blue') + ' ' + _color(fileset.geoloc_file.name, 'cyan') + '\n')
        ss.write(f' Band: {fileset.geoloc_file.band}, {fileset.geoloc_file.band_verbose}\n')
        ss.write(f' Полный путь: {fileset.geoloc_file.path}\n')
        ss.write(f' Номер орбиты: {fileset.geoloc_file.orbit_number}\n')
        ss.write(f' Дата: {fileset.geoloc_file.date.date()}\n')
        ss.write(f' Время: {fileset.geoloc_file.t_start} - {fileset.geoloc_file.t_end}\n')
        ss.write(f' ID спутника: {fileset.geoloc_file.sat_id}\n')
        ss.write(f' {fileset.geoloc_file.band}-band: {len(fileset.band_files)} файлов{" (не полный)" if not fileset.is_full() else ""}\n')
        if args.bands:
            for f in fileset.band_files:
                files_total += 1
                ss.write(f'  {shorten_name(f.name, 40)}\n')
        else:
            files_total += len(fileset.band_files)

    print(f'Наборов файлов: {len(files)}')
    print(f'Всего файлов: {files_total}')
    ss.seek(0)
    print(ss.read()[:-1])


def process(args):
    if not args.no_exc:
        gdal.UseExceptions()

    if args.no_colors:
        loguru.logger.remove()
        loguru.logger.add(sys.stdout, colorize=False)

    if not args.verbose:
        loguru.logger.remove()
        loguru.logger.add(sys.stdout, colorize=not args.no_colors, level='INFO')

    files = viirs.find_sdr_viirs_filesets('/home/marat/Documents/npp')
    loguru.logger.debug(f'Нашел {len(files)} наборов файлов')
    for dataset in files.values():
        processed_fileset = viirs.hlf_process_fileset(dataset)
        if processed_fileset is None:
            continue
        viirs.save_as_tiff('/tmp', processed_fileset)


if __name__ == '__main__':
    main()
