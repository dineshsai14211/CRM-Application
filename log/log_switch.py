from log.logging_logic import *

LOG_SWITCH = True


def log_info(message):
    """
    These function Logs an informational message based on LOG_SWITCH

    :param message: log message
    :return: None
    """
    if LOG_SWITCH:
        log.info(message)


def log_error(message):
    """
    These function logs an error message based on LOG_SWITCH

    :param message: log message
    :return: None
    """
    if LOG_SWITCH:
        log.error(message)


def log_debug(message):
    """
    These function logs an debug message based on LOG_SWITCH

    :param message: log message
    :return: None
    """
    if LOG_SWITCH:
        log.debug(message)


def log_warning(message):
    """
    These function logs an warning message based on LOG_SWITCH

    :param message: log measage
    :return: None
    """
    if LOG_SWITCH:
        log.warning(message)