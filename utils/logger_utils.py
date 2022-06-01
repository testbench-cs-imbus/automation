import sys
from datetime import datetime
from logging import Formatter, Logger, StreamHandler, getLogger, root
from typing import List, Union
from colorama import init

init()


def get_logger(name: str, level: Union[str, int]) -> Logger:
    """
    Returns a named logger instance for stdout that uses colorized log levels.

    Parameters
    ----------
    name: str
        Logger name
    level: str | int
        The log level for the logger. Level must be an int or a str, e.g. logging.INFO

    Returns
    -------
    logging.Logger:
        A new logger instance or an already existing.

    Notes
    -----
    Logger name (for adapters) should be unique to avoid double output, when processing parallel Test Cases
    """
    for key in root.manager.loggerDict.keys():
        if key == name:
            return root.manager.loggerDict[key]  # type: ignore
    logger = getLogger(name)
    handler = StreamHandler(sys.stdout)
    formatter = __ColoredFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def remove_logger(name: str) -> None:
    """
    Removes a named logger instance.

    Parameters
    ----------
    name: str
        Logger name

    Returns
    -------
    None:
        None
    """
    logger_key = ''
    for key in root.manager.loggerDict.keys():
        if key == name:
            logger_key = name
            break
    if logger_key != '':
        __remove_logger_by_key(logger_key)


def remove_all_logger_with_prefix(prefix: str) -> None:
    """
    Removes all logger instances starting with the given prexi in the logger name.

    Parameters
    ----------
    name: prefix
        Logger name prefix

    Returns
    -------
    None:
        None
    """
    logger_keys: List[str] = []
    for key in root.manager.loggerDict.keys():
        if key.startswith(prefix): logger_keys.append(key)
    for matching in logger_keys:
        __remove_logger_by_key(matching)


def __remove_logger_by_key(key: str):
    logger = root.manager.loggerDict[key]
    logger.handlers.clear()  # type: ignore
    del root.manager.loggerDict[key]


##################################################
# Helper class for colored log output
##################################################
class __ColoredFormatter(Formatter):
    """
    A custom logging formatter that outputs colorized messages depending on the log level using ANSI escape sequences for terminal output.
    """

    class __AnsiColor:
        """
        Provides convertion to ANSI colored messages.
        """

        colors = {
            'black': 30,
            'red': 31,
            'green': 32,
            'yellow': 33,
            'blue': 34,
            'magenta': 35,
            'cyan': 36,
            'white': 37,
            'bgred': 41,
            'bggrey': 100
        }

        prefix = '\033['  # starts ANSI sequence
        suffix = '\033[0m'  # resets ANSI sequence

        def colorize(self, text: str, color: str = "") -> str:
            """
            Converts a string to an ANSI colorized string in the give color.

            Parameters
            ----------
            text: str
                The string to be converted.
            color: str
                The color the string shall be converted to.

            Returns
            -------
            str:
                The converted string.
            """
            if color not in self.colors:
                color = 'white'

            clr = self.colors[color]
            return f"{self.prefix}{clr}m{text}{self.suffix}"

    ansi_color = __AnsiColor()

    def format(self, record):

        message = record.getMessage()

        mapping = {
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bgred',
            'DEBUG': 'bggrey',
        }

        clr = mapping.get(record.levelname, 'white')

        # Time format: '2022-03-09 17:20:24,334' (only 3 digits for microsecods)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        formatted = self.ansi_color.colorize(f"{now} {record.levelname} ({record.name}): {message}", clr)

        return formatted
