from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
from logging.handlers import TimedRotatingFileHandler
FORMATTER = logging.Formatter("%(asctime)s - %(name)s - "
                              "%(levelname)s - %(message)s")
LOG_FILE = "/tmp/os_migrate.log"


def get_file_handler():
    """
    Get logger file handler.

    This method returns a file handler
    """
    file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name):
    """
    Get logger.

    This method will fetch an specific logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    # We can create other types of loggers like
    # a console logger if we need to.
    logger.addHandler(get_file_handler())
    logger.propagate = False
    return logger
