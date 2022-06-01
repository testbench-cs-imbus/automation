#######
# Attention: Using this impementation also requires using the input function from here instead of the built in.
# To do so, just import as follows:
# from utils.terminal_utils import ProgressIndicator, input
#######
import os
import re
import sys
from typing import List, TextIO

import colorama

if (sys.platform == "win32"):
    import ctypes
    # -*- coding: UTF-8 -*-
    #------------------------------------------------------------------------------
    from ctypes import (Structure, byref, c_short, c_ulong, c_ushort, windll, wintypes)

    from pyreadline import console

    #------------------------------------------------
    # Win32 API
    #------------------------------------------------
    SHORT = c_short
    WORD = c_ushort
    DWORD = c_ulong

    STD_OUTPUT_HANDLE = DWORD(-11)  # $CONOUT

    # These are already defined, so no need to redefine.
    COORD = wintypes._COORD
    SMALL_RECT = wintypes.SMALL_RECT
    CONSOLE_SCREEN_BUFFER_INFO = console.CONSOLE_SCREEN_BUFFER_INFO

    #------------------------------------------------
    # Main
    #------------------------------------------------
    wk32 = windll.kernel32

    hSo = wk32.GetStdHandle(STD_OUTPUT_HANDLE)
    GetCSBI = wk32.GetConsoleScreenBufferInfo

else:
    import termios

colorama.init()  # ensure escape sequence in windows terminal


class _CursorPosition(object):
    Row: int
    Col: int

    def __init__(self, Row: int, Col: int):
        self.Row = Row
        self.Col = Col


def cursorPos() -> _CursorPosition:
    result = _CursorPosition(Row=-1, Col=-1)
    if (sys.platform == "win32"):
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        GetCSBI(hSo, byref(csbi))
        xy = csbi.dwCursorPosition

        size = os.get_terminal_size()
        result.Row = xy.Y
        result.Col = xy.X
    else:
        OldStdinMode = termios.tcgetattr(sys.stdin)
        _ = termios.tcgetattr(sys.stdin)
        _[3] = _[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, _)
        try:
            _ = ""
            sys.stdout.write("\33[6n")
            sys.stdout.flush()
            while not (_ := _ + sys.stdin.read(1)).endswith('R'):
                True  # pyright: reportUnusedExpression=false
            res = re.match(r".*\[(?P<y>\d*);(?P<x>\d*)R", _)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, OldStdinMode)
        if (res):
            result.Row = int(res.group("y"))
            result.Col = int(res.group("x"))
    return result


def move_cursor(pos: _CursorPosition):
    if (sys.platform == "win32"):
        sys.stdout.write('\033[' + str(pos.Row + 1) + ';' + str(pos.Col + 1) +
                         'H')  # because win terminal starts with 1, unix 0
    else:
        sys.stdout.write('\033[' + str(pos.Row) + ';' + str(pos.Col) + 'H')
    sys.stdout.flush()


# because builtin input function fails while ovveriding stdout, override input function
def input_override(prompt):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return sys.stdin.readline().replace('\n', '')


global input
input = input_override


class ProgressIndicator():

    _indicator_list: List['ProgressIndicator'] = []

    def __init__(self, total: int, prefix: str = '', suffix: str = '', bar_width: int = 80):
        """
        Initializes the ProgressIndicator class.
        
        Progress bar format:

        [prefix] 100% [***************************] 5 of 5 [suffix] - [msg]

        Parameters
        ----------
        total: int
            Total count of items to be progressed
        prefix: str
            Optional: A string before the progress bar
        suffix: str
            Optional: A string after the progress bar
        bar_width: int
            Optional: Size of the progress bar (default: 80) affecting format part: [***************************]

        Returns
        -------
        ProgressIndicator
            A new instance of ProgressIndicator
        """
        self.__total = self.__total_initial = total
        self.__prefix = self.__prefix_initial = prefix
        self.__suffix = self.__suffix_initial = suffix
        self.__bar_width = self.__bar_width_initial = bar_width
        self.__count = self.__count_initial = 0
        self.__total_digits = self.__total_digits_initial = len(str(total))

        self.__first_run = True

        # line movements
        self.__cursor_row_start: int = 0
        self._cursor_row_current: int = 0

    def __del__(self):
        try:
            ProgressIndicator._indicator_list.index(self)  # raises ValueError if not found
            ProgressIndicator._indicator_list.remove(self)
        except ValueError:
            pass

    def reset_total(self, total: int):
        """
        Resets the total count of the bar. Usefully in loops which run multiple with different array sizes.

        Parameters
        ----------
        total: str
            The new total count
        """
        self.__total = self.__total_initial = total
        self.__prefix = self.__prefix_initial
        self.__suffix = self.__suffix_initial
        self.__bar_width = self.__bar_width_initial
        self.__count = self.__count_initial = 0
        self.__total_digits = self.__total_digits_initial = len(str(total))

    def update_progress(self, msg: str = ''):
        """
        Updates the progress by one count


        Parameters
        ----------
        msg: str
            Optional: A string displayed at the end of the progress line
        """
        self.__terminal_size = os.get_terminal_size()
        self._cursor_row_current = cursorPos().Row
        if self.__count == 0:
            if self.__first_run == True:
                self.__cursor_row_start = self._cursor_row_current
                self._indicator_list.append(self)

        # take respect to terminal size, row count
        self.__calculate_start_rows()

        if self._cursor_row_current != self.__cursor_row_start:
            move_cursor(_CursorPosition(Row=self.__cursor_row_start, Col=0))  # move to initial progress bar line

        self.__count += 1
        self.__count_format = f'{self.__total_digits}.0f'
        self.__progress = int(self.__count / int(self.__total) * self.__bar_width)
        self.__percent = self.__count * 100 / int(self.__total)

        # clear line if the one before was longer than the new one: '\r\033[0K'
        self._new_line = f'\r\033[0K{self.__prefix} {self.__percent:3.0f}% [{"*" * self.__progress}{"." * (self.__bar_width - self.__progress)}] {self.__count:{self.__count_format}} of {self.__total:{self.__count_format}} {self.__suffix}'
        if msg != '': self._new_line += f' - {msg}'
        # cut to max line length to prevent new lins from form feed (\f)
        self._new_line = self._new_line[:int(self.__terminal_size.columns)]

        self._new_line = self._new_line + '\n'

        sys.stdout.write(self._new_line)
        sys.stdout.flush()

        if self._cursor_row_current != self.__cursor_row_start:
            move_cursor(_CursorPosition(Row=self._cursor_row_current, Col=0))  # move back to latest line

        if self.__count == self.__total:
            # progress done -> reset to intial values
            self.__total = self.__total_initial
            self.__prefix = self.__prefix_initial
            self.__suffix = self.__suffix_initial
            self.__bar_width = self.__bar_width_initial
            self.__count = self.__count_initial
            self.__total_digits = self.__total_digits_initial
            self.__first_run = False

    @staticmethod
    def clear_indicators():
        """
        Clears all indicator instance used previously.
        This should be called after bars are not used anymore to ensure new lines are written on.
        If not called, the last lines of all previously progress bars are printed as last lines.
        """
        ProgressIndicator._indicator_list.clear()

    def __calculate_start_rows(self):
        if self.__count == 0 and self.__first_run: return  # first progress line

        if self.__terminal_size.lines <= self._cursor_row_current:
            if (sys.platform == "win32"):
                self.__cursor_row_start = self.__cursor_row_start - (self.__cursor_row_start -
                                                                     self.__terminal_size.lines) - 1
                self._cursor_row_current = self.__cursor_row_start
                self.__cursor_row_start -= len(
                    ProgressIndicator._indicator_list) - (ProgressIndicator._indicator_list.index(self))
            else:
                self.__cursor_row_start = self.__terminal_size.lines - 1
                self.__cursor_row_start -= len(
                    ProgressIndicator._indicator_list) - (ProgressIndicator._indicator_list.index(self) + 1)
        else:
            self.__cursor_row_start = self._cursor_row_current - (len(ProgressIndicator._indicator_list) -
                                                                  (ProgressIndicator._indicator_list.index(self)))


class _Capture_stdout(TextIO):

    org = sys.stdout

    def __init__(self):
        sys.stdout = self

    def __ignore_line(self, line: str) -> bool:
        # ignore special excapes e.g. from move_cursor()
        if line in ['\33[6n', '\x1b[6n', '\x1b[6n\n']:
            return True
        if re.match(r'^\x1b\[.+;.+H', line):
            return True
        return False

    def write(self, line: str):
        if self.__ignore_line(line):
            sys.stdout = self.org
            sys.stdout.write(line)
            sys.stdout = self
            return

        # check for progress indicators and place them as final lines
        # f'\r\033[0K
        if len(ProgressIndicator._indicator_list) > 0:
            for pi in ProgressIndicator._indicator_list:
                if line == pi._new_line:
                    sys.stdout = self.org
                    sys.stdout.write(line)
                    sys.stdout = self
                    return
            if line == '\n': return

            # none progress line, write and append progress lines
            curser_pos = cursorPos().Row
            pi_line = curser_pos - len(ProgressIndicator._indicator_list)
            if (sys.platform == "win32"):
                terminal_size = os.get_terminal_size()
                if terminal_size.lines <= curser_pos:
                    real_cursor = terminal_size.lines - 1
                    pi_line = real_cursor - len(ProgressIndicator._indicator_list)

            move_cursor(_CursorPosition(pi_line, 0))
            sys.stdout = self.org
            sys.stdout.write(f'\r\033[0K{line}')
            if not line.endswith('\n'):
                move_cursor(_CursorPosition(pi_line + 1, 0))

            for pi in ProgressIndicator._indicator_list:
                sys.stdout.write(pi._new_line)

            sys.stdout = self
        else:
            sys.stdout = self.org
            sys.stdout.write(line)
            sys.stdout = self

    def flush(self):
        sys.stdout = self.org
        sys.stdout.flush()
        sys.stdout = self


_Capture_stdout()
