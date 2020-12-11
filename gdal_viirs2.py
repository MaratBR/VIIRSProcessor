#!/usr/bin/python3
import sys
from io import StringIO

import gdal
import loguru

import gdal_viirs.v2 as viirs
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


def check_int(value):
    try:
        int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not an int value" % value)
    return int(value)


def check_scale_int(value):
    v = check_int(value)
    if v < 1:
        raise argparse.ArgumentTypeError("%s is an invalid scale int value (must be 1 or greater)" % value)
    return v


def main():
    parser = argparse.ArgumentParser()

    subcommands = parser.add_subparsers()

    process_parser = subcommands.add_parser('process', help='Обработка данных')
    process_parser.set_defaults(func=process)

    process_parser.add_argument('src_dir', help='Папка с VIIRS файлами')
    process_parser.add_argument('--prefer',
                                choices=('e', 'p', 'b'),
                                default='e',
                                help='Определяет какой датасет выбрать, если есть альтернативы, p - обрабатывать '
                                     'параллакс-скорректированные сеты, e - спроецированные на еллипсоид WGS84, '
                                     'b - оба')
    process_parser.add_argument('-o', '--out_dir', default='/tmp', help='Папка, куда поместить готовые файлы', required=False)
    process_parser.add_argument('-E', '--no_exc', help='Не вызывать gdal.UseExceptions() при старте',
                                action="store_true")
    process_parser.add_argument('--ext', help='Расширение выходных файлов', default='tiff')
    process_parser.add_argument('--types', help='Типы файлов для обработки')
    process_parser.add_argument('-C', '--no_colors', help='Не выводить в цвете', action='store_true')
    process_parser.add_argument('-v', '--verbose', help='Подробный вывод в консоль', action='store_true')
    process_parser.add_argument('-S', '--scale', help='Масштаб выходного файла', default=2000, type=check_scale_int)
    process_parser.add_argument('-p', '--proj', help='Проекция, передоваемая в pyproj', default=viirs.const.PROJ_LCC)
    process_parser.add_argument('--proj_src', help='Файл с проекцией, если указано, флаг --proj игнорируется')

    show_parser = subcommands.add_parser('show', help='Анализ данных')
    show_parser.set_defaults(func=show)

    show_parser.add_argument('src_dir', help='Папка с VIIRS файлами')
    show_parser.add_argument('-b', '--bands', help='Вывести список band-файлов', action='store_true')
    show_parser.add_argument('-C', '--no_colors', help='Не выводить в цвете', action='store_true')
    show_parser.add_argument('--prefer',
                             choices=('e', 'p', 'b'),
                             default='e',
                             help='Определяет какой датасет выбрать, если есть альтернативы, p - обрабатывать '
                                  'параллакс-скорректированные сеты, e - спроецированные на еллипсоид WGS84, '
                                  'b - оба')

    args: argparse.Namespace = parser.parse_args(sys.argv[1:])

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


def shorten_name(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len-2] + '..'


def cnv_prefer_tag(v: str):
    if v == 'b':
        return None
    elif v == 'e':
        return False
    elif v == 'p':
        return True


def show(args):
    if args.no_colors:
        global is_color_output_enabled
        is_color_output_enabled = False

    files = viirs.utility.find_sdr_viirs_filesets(args.src_dir, prefer_parallax_corrected=cnv_prefer_tag(args.prefer))

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
    print(f'Папка с файлами: {args.src_dir}')
    print(f'Папка вывода: {args.out_dir}')
    print(f'Масштаб: {args.scale} метров/пиксель')

    if args.proj_src:
        with open(args.proj_src) as f:
            proj = f.read()
            print(f'Файл с проекцией: {args.proj_src}')
    else:
        proj = args.proj

    if not args.no_exc:
        gdal.UseExceptions()

    if args.no_colors:
        loguru.logger.remove()
        loguru.logger.add(sys.stdout, colorize=False)

    if not args.verbose:
        loguru.logger.remove()
        loguru.logger.add(sys.stdout, colorize=not args.no_colors, level='INFO')

    files = viirs.find_sdr_viirs_filesets(
        args.src_dir,
        prefer_parallax_corrected=cnv_prefer_tag(args.prefer)
    )
    loguru.logger.debug(f'Нашел {len(files)} наборов файлов')
    for dataset in files.values():
        processed_fileset = viirs.hlf_process_fileset(dataset, scale=args.scale, proj=proj)
        if processed_fileset is None:
            continue
        viirs.save_as_tiff(args.out_dir, processed_fileset)


if __name__ == '__main__':
    main()
