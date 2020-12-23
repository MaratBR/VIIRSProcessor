class ViirsException(Exception):
    """
    Базовый класс исключений
    """

    def __init__(self, message):
        self.message = message
        super(ViirsException, self).__init__(message)


class DatasetNotFoundException(ViirsException):
    """
    Исключение, выбрасываемае, когда не удается открыть датасет
    """

    def __init__(self, name):
        super(DatasetNotFoundException, self).__init__(f'Датасет {name} не найден')
        self.dataset = name


class SubDatasetNotFound(DatasetNotFoundException):
    """
    Исключение, выбрасываемое, когда субдатасет не удается открыть или найти,
    например при получении широты и долготы из файла
    """
    pass


class InvalidFileType(ViirsException):
    """
    Исключение выбрасываемое при попытке провести какую-то
    операцию над файлом, тип которого не поддерживает эту операцию.
    Например, получить тип канала (M/I) для файла с координатами (напр. GIMGO)
    """
    pass


class GDALNonZeroReturnCode(ViirsException):
    """
    Выбрасывается, если операция GDAL'а вернула код, отличный от 0
    Например при вызове gdal.FillNodata
    """
    return_code: int

    def __init__(self, code, message):
        super(GDALNonZeroReturnCode, self).__init__(message)
        self.return_code = code


class InvalidData(ViirsException):
    """
    Данное исключение выбрасываемое в случае, если входные данные были неверны,
    например если на вход функции был подан набор файлов без файлов (пустой)
    """
    pass


class InvalidFilename(ViirsException):
    """
    Выбрасывается, если имя VIIRS файла не соответсвует шаблону
    """

    def __init__(self, filename):
        super(InvalidFilename, self).__init__(
            f'Имя файла не соответсвует шаблону. Имя файла: {filename}, ожидалось: ТИП_спутник_dГГГГММДД_tЧЧММССС_eЧЧММССС_bНомерОрбиты_cГГГММДДччммсссссссс_ИсточникФайла.h5')


class DriverNotFound(ViirsException):
    def __init__(self, driver):
        super(DriverNotFound, self).__init__(f'Драйвер {driver} необходим, но не найден')
