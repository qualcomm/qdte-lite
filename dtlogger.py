# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# create a formatter
formatter = logging.Formatter(" %(asctime)s - %(levelname)s - %(message)s")
# create a console hanlder
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

def logger_init(log_file=None, log_level=logging.DEBUG, max_file_size_mb=1):
    """
    Initialize dt logger。

    Args:
        log_file (str): log file path。if it is None,only print to console。
        log_level (int): log level(logging.INFO、logging.DEBUG)。
        max_file_size_mb (int): Maxmin log file size(MB)。
    """

    logger.setLevel(log_level)

    # create a file handler
    if log_file:
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        file_handler = RotatingFileHandler(log_file, maxBytes=(1024*1024*max_file_size_mb), backupCount=1)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.NOTSET) 
        logger.addHandler(file_handler)

    logger.addHandler(console_handler)

def info(message):
    logger.info(message)

def warning(message):
    logger.warning(message)

def error(message):
    logger.error(message)

def debug(message):
    logger.debug(message)
