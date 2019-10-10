# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler
import config


def get_logger(dirname, basename, level="INFO"):
    """日志"""
    _logger = logging.getLogger(basename)
    del _logger.handlers[:]
    filename = os.path.join(dirname, basename + ".log" if basename[-4:] != ".log" else basename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    formats = logging.Formatter("%(asctime)s %(levelname)-8s[%(filename)s:%(lineno)04d] %(message)s")
    handler = RotatingFileHandler(filename=filename, mode="a", maxBytes=1024 * 1024 * 10, backupCount=5)
    handler.setFormatter(formats)
    _logger.addHandler(handler)
    _level = level.upper()
    if _level == "DEBUG":
        _logger.setLevel(logging.DEBUG)
    elif _level == "INFO":
        _logger.setLevel(logging.INFO)
    elif _level == "WARNING":
        _logger.setLevel(logging.WARNING)
    elif _level == "ERROR":
        _logger.setLevel(logging.ERROR)
    elif _level == "CRITICAL":
        _logger.setLevel(logging.CRITICAL)
    else:
        _logger.setLevel(logging.ERROR)
    return _logger


log_path = config.fetch("logpath")
logger = get_logger(log_path, "sigmathird")