class EventNotFoundError(Exception):
    """Вызывается если события с таким ID не найдено"""


class EventNotPublishedError(Exception):
    """Вызывается если статус события не published"""
