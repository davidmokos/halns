from datetime import datetime

import pytz

OUR_DATE_FORMAT = '%Y-%m-%d'


class TimestampHelper:
    _current_timestamp: int = None

    @classmethod
    def set_current_timestamp(cls, timestamp: int):
        TimestampHelper._current_timestamp = timestamp

    @classmethod
    def current_datetime(cls) -> datetime:
        utc = pytz.timezone('UTC')
        now = utc.localize(datetime.utcnow())
        return now

    @classmethod
    def current_timestamp(cls) -> int:
        if TimestampHelper._current_timestamp:
            return TimestampHelper._current_timestamp
        return int(cls.current_datetime().timestamp())

    @classmethod
    def current_day_in_our_format(cls):
        return cls.current_datetime().strftime(OUR_DATE_FORMAT)
