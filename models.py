"""Contains app models"""
from peewee import *

db = SqliteDatabase("alarm_clocks")


class AlarmClock(Model):
    """
    Alarm clock model
    """
    alarm_time = DateTimeField()
    description = TextField()

    class Meta:
        database = db


db.create_tables([AlarmClock])
