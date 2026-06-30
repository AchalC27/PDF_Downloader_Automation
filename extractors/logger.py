import logging
from pathlib import Path


LOG_FOLDER = Path("logs")

LOG_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


FORMAT = "%(asctime)s %(levelname)-8s %(message)s"


def get_logger(name):

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(FORMAT)

    logfile = LOG_FOLDER / f"{name.lower()}.log"

    file_handler = logging.FileHandler(
        logfile,
        encoding="utf-8"
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


master_logger = get_logger("master")