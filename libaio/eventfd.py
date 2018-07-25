# Copyright (C) 2017-2018  Vincent Pelletier <plr.vincent@gmail.com>
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
Minimal adaptation of sys/eventfd.h and bits/eventfs.h .
"""
from ctypes import CDLL, c_uint, c_int, get_errno

libc = CDLL("libc.so.6", use_errno=True)
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

EFD_CLOEXEC = 0o02000000
EFD_NONBLOCK = 0o00004000
EFD_SEMAPHORE = 0o00000001
