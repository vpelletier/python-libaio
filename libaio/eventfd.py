# Copyright (C) 2017-2021  Vincent Pelletier <plr.vincent@gmail.com>
#
# This file is part of python-libaio.
# python-libaio is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-libaio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with python-libaio.  If not, see <http://www.gnu.org/licenses/>.
"""
Minimal adaptation of sys/eventfd.h and bits/eventfd.h .
"""
from ctypes import CDLL, c_uint, c_int, get_errno
from ctypes.util import find_library
import os

libc = CDLL(find_library("c"), use_errno=True)
# pylint: disable=unused-argument
def _raise_errno_on_neg_one(result, func, arguments):
    if result == -1:
        raise OSError(get_errno(), func.__name__)
    return result
# pylint: enable=unused-argument

eventfd = libc.eventfd
eventfd.restype = c_int
eventfd.argtypes = (c_int, c_uint)
eventfd.errcheck = _raise_errno_on_neg_one

EFD_SEMAPHORE = 0o00000001
# Note: the glibc hardcodes those EFD_ constants, duplicating their O_
# counterpart. The kernel equivalent of that header, and Android's libc
# headers, does instead refers to the latter when declaring the former.
# Follow the latter group, as it looks cleaner.
EFD_CLOEXEC = os.O_CLOEXEC
EFD_NONBLOCK = os.O_NONBLOCK
