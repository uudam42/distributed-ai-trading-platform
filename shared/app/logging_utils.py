import logging
import time
from typing import Any


def configure_logging(service_name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    return logging.getLogger(service_name)


def log_kv(logger: logging.Logger, service: str, action: str, **fields: Any) -> None:
    payload = ' '.join(f'{k}={v}' for k, v in fields.items())
    logger.info(f'[{service}] {action} | {payload}'.rstrip())


class RequestTimer:
    def __init__(self) -> None:
        self.started = time.perf_counter()

    @property
    def ms(self) -> float:
        return (time.perf_counter() - self.started) * 1000
