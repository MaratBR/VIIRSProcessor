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
    'PEEWEE_MODELS'
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
        return Path(self.input_directory).parts[-1]

    @property
    def swath_id(self):
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
        return self.ends_at.strftime('%d.%m') + ' - ' + self.ends_at.strftime('%d.%m.%Y')


class NDVICompositeComponents(BaseModel):
    composite = ForeignKeyField(NDVIComposite)
    component = ForeignKeyField(NDVITiff)


class NDVIDynamicsTiff(ProcessedFile):
    b1_composite: Union[int, NDVIComposite] = ForeignKeyField(NDVIComposite)
    b2_composite: Union[int, NDVIComposite] = ForeignKeyField(NDVIComposite)


PEEWEE_MODELS = [
    NDVITiff,
    NDVIComposite,
    NDVICompositeComponents,
    NDVIDynamicsTiff,
    ProcessedViirsL1,
    MetaData
]
