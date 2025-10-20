import logging
import sys

DATE_FORMAT = "%d/%m %H:%M:%S"
FORMAT = (
    "\n%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)s \n  - %(message)s"
)


def init_logger():
    formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.addHandler(console_handler)

    return logger
