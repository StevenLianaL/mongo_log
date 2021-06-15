import inspect
from datetime import datetime
from enum import Enum
from typing import Optional

from mongoengine import Document, StringField, EnumField, DateTimeField, IntField


class LogLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class LogHelper:
    @classmethod
    def current_month(cls):
        return f"{datetime.utcnow():%Y-%M}"


class BaseLog(Document):
    project = StringField(max_length=50, default='itembank')
    app = StringField(max_length=50, default='global')
    func = StringField(max_length=50)
    meta = {
        'abstract': True,
        'indexes': ['project', 'app', 'func']
    }


class LogRecord(BaseLog):
    log = StringField()
    level = EnumField(LogLevel, default=LogLevel.INFO)
    created = DateTimeField(default=datetime.utcnow)
    user = IntField()

    meta = {
        'indexes': [
            {
                'fields': ['created'],
                'expireAfterSeconds': 30 * 24 * 60 * 60
            }
        ]
    }

    @classmethod
    def write(cls, text: str, level: str, user: Optional[int] = 0, app: Optional[str] = ''):
        func_name = [i.function for i in inspect.stack()][2]
        record = cls(log=text, level=level, user=user, app=app, func=func_name)
        record.save()

    @classmethod
    def info(cls, text: str, user: int = 0, app: str = ''):
        cls.write(text=text, user=user, app=app, level="INFO")

    @classmethod
    def debug(cls, text: str, user: int = 0, app: str = ''):
        cls.write(text=text, user=user, app=app, level="DEBUG")

    @classmethod
    def warning(cls, text: str, user: int = 0, app: str = ''):
        cls.write(text=text, user=user, app=app, level="WARNING")

    @classmethod
    def error(cls, text: str, user: int = 0, app: str = ''):
        cls.write(text=text, user=user, app=app, level="ERROR")


class LogAccess(BaseLog):
    count = IntField(default=0)
    month = StringField(default=LogHelper.current_month)

    def increase(self):
        self.__class__.objects(
            project=self.project, app=self.app, func=self.func, month=self.month
        ).upsert_one(**{'inc__count': 1})
