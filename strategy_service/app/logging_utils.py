import logging


def configure_logging(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    return logging.getLogger(name)


def log_kv(logger: logging.Logger, service: str, action: str, **fields):
    payload = ' '.join(f'{k}={v}' for k, v in fields.items())
    logger.info(f'[{service}] {action} | {payload}'.rstrip())
