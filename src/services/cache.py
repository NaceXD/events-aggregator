"""Простой in-memmory TTL-кэш для мест"""

import time


class TtlCache:
    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> list | None:
        if key not in self.cache:
            return None
        saved_time, value = self.cache[key]
        if time.time() - saved_time > 30:
            del self.cache[key]
            return None
        return value

    def set(self, key: str, value: list):
        self.cache[key] = (time.time(), value)
