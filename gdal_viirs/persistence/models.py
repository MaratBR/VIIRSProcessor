from datetime import datetime
from pathlib import Path
from typing import Union

from peewee import *

__all__ = (
    'db_proxy',
    'ProcessedViirsL1',
    'NDVITiff',
    'NDVIDynamicsTiff',
    'NDVIComposite',
    'NDVICompositeComponents',
    'MetaData',
    'PEEWEE_MODELS',
)

from peewee import ModelSelect

from gdal_viirs.hl import utility

db_proxy = Proxy()


class BaseModel(Model):
    id = IntegerField(primary_key=True)

    class Meta:
        database = db_proxy


class MetaData(BaseModel):
    key = CharField(primary_key=True)
    value = TextField()

    @classmethod
    def set_meta(cls, key: str, value: str):
        record: MetaData = cls.get_or_none(cls.key == key)
        if record is None:
            record = cls(key=key, value=value)
            record.save(True)
        else:
            record.value = value
            record.save()

    @classmethod
    def get_meta(cls, key: str, default: str):
        record = cls.get_or_none(cls.key == key)
        if record is None:
            return default
        return record.value


class ProcessedFile(BaseModel):
    def __init__(self, output_file: Union[str, Path] = None, **kwargs):
        if output_file:
            kwargs['output_file'] = str(output_file)
        super(ProcessedFile, self).__init__(**kwargs)

    output_file: str = CharField(unique=True)
    created_at: datetime = DateTimeField(default=datetime.now)


class DatasetRelatedFile(ProcessedFile):
    dataset_date = DateTimeField()

    def __init__(self, output_file: Union[str, Path] = None, dataset_date: datetime = None, **kwargs):
        super(DatasetRelatedFile, self).__init__(output_file, **kwargs)
        self.dataset_date = dataset_date


class ProcessedViirsL1(DatasetRelatedFile):
    input_directory: Union[CharField, str] = CharField()
    geoloc_filename: Union[CharField, str] = CharField()
    type: Union[CharField, str] = CharField()

    @property
    def directory_name(self):
        """
        Возвращает имя корневой папки, где находятся данные со снимка.
        Под корневой папкой тут подразумевается папка, содержащая подпапку viirs/level1
        :return:
        """
        return Path(self.input_directory).parts[-1]

    def is_of_type(self, typ: str):
        return self.type.strip().upper() == typ.upper()

    @property
    def swath_id(self):
        """
        Использует `utility.extract_swath_id` для получения ID витка и помещает его
        в поле модели.
        :return: ID витка (строка)
        """
        if not hasattr(self, '_swath_id'):
            setattr(self, '_swath_id', utility.extract_swath_id(self.directory_name))
        return self._swath_id

    @classmethod
    def select_gimgo_without_ndvi(cls) -> ModelSelect:
        sub = NDVITiff.select(SQL('1')).where(NDVITiff.based_on == cls.id)
        return cls.select().where((cls.type == 'GIMGO') & ~fn.EXISTS(sub))


class NDVITiff(ProcessedFile):
    based_on = ForeignKeyField(ProcessedViirsL1)


class NDVIComposite(ProcessedFile):
    starts_at: Union[DateField, datetime] = DateField()
    ends_at: Union[DateField, datetime] = DateField()

    @property
    def date_text(self):
        """
        Форматирует строку периода в виде ДД.ММ - ДД.ММ.ГГГГ
        :return: отформатированная строка периода (даты) композита
        """
        return self.ends_at.strftime('%d.%m') + ' - ' + self.starts_at.strftime('%d.%m.%Y')


class NDVICompositeComponents(BaseModel):
    composite = ForeignKeyField(NDVIComposite, related_name='components')
    component = ForeignKeyField(NDVITiff, related_name='composites')

    class Meta:
        primary_key = CompositeKey('composite', 'component')


class NDVIDynamicsTiff(ProcessedFile):
    b1_composite: Union[int, NDVIComposite] = ForeignKeyField(NDVIComposite)
    b2_composite: Union[int, NDVIComposite] = ForeignKeyField(NDVIComposite)

    @property
    def date_text(self):
        """
        Форматирует строку периода в виде ДД.ММ - ДД.ММ.ГГГГ
        :return: отформатированная строка периода (даты) динамики
        """
        return self.b1_composite.starts_at.strftime('%d.%m') + ' - ' + self.b2_composite.ends_at.strftime('%d.%m.%Y')


PEEWEE_MODELS = [
    NDVITiff,
    NDVIComposite,
    NDVICompositeComponents,
    NDVIDynamicsTiff,
    ProcessedViirsL1,
    MetaData
]
