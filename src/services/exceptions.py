"""Кастомные ошибки"""


class EventNotFoundError(Exception):
    """Вызывается, если события с таким ID не найдено"""


class EventNotPublishedError(Exception):
    """Вызывается, если статус события не published"""


class RegistrationDeadlinePassedError(Exception):
    """Вызывается, если дедлайн регистрации прошел"""


class TicketNotFoundError(Exception):
    """Вызывается, если Ticket не найден"""


class ProviderError(Exception):
    """Вызываеься, когда внешний Events Provider API возвращает ошибку"""
