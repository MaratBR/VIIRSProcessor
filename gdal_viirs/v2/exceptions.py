class ViirsException(Exception):
    def __init__(self, message):
        self.message = message
        super(ViirsException, self).__init__(message)


class DatasetNotFoundException(ViirsException):
    def __init__(self, name):
        super(DatasetNotFoundException, self).__init__(f'Dataset or subdataset {name} not found')
        self.dataset = name


class SubDatasetNotFound(DatasetNotFoundException):
    pass


class InvalidFileType(ViirsException):
    pass


class InvalidData(ViirsException):
    pass


class GDALNonZeroReturnCode(ViirsException):
    return_code: int

    def __init__(self, code, message):
        super(GDALNonZeroReturnCode, self).__init__(message)
        self.return_code = code


class ProcessingException(ViirsException):
    pass


class ProjectionFailure(ProcessingException):
    pass
