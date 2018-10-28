# encdoing:utf-8
import logging
import logging.handlers


def get_log():
    logger = logging.getLogger('')
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(threadName)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.TimedRotatingFileHandler(
        'test.log', 'midnight', 1)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)

    return logger
