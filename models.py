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
    project = StringField(max_length=50, default='project')
    app = StringField(max_length=50, default='app')
    func = StringField(max_length=50, default='func')
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

    def write(self, log: str, level: str, user: Optional[int] = 0):
        func_name = [i.function for i in inspect.stack()][2]
        record = self.__class__(
            log=log, user=user, level=level, func=func_name,
            project=self.project, app=self.app)
        record.save()

    def debug(self, text: str, user: int = 0):
        self.write(log=text, level="DEBUG", user=user)

    def info(self, text: str, user: int = 0):
        self.write(log=text, level="INFO", user=user)

    def warning(self, text: str, user: int = 0):
        self.write(log=text, level="WARNING", user=user)

    def error(self, text: str, user: int = 0):
        self.write(log=text, level="ERROR", user=user)


class LogAccess(BaseLog):
    count = IntField(default=0)
    month = StringField(default=LogHelper.current_month)

    def increase(self):
        self.__class__.objects(
            project=self.project, app=self.app, func=self.func, month=self.month
        ).upsert_one(**{'inc__count': 1})
