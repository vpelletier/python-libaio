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
Adaptation of libaio.h .
"""
from ctypes import (
    CDLL, CFUNCTYPE, POINTER, Union, Structure, memset, sizeof, byref, c_long,
    c_size_t, c_int64, c_short, c_int, c_uint, c_ulong, c_void_p, c_longlong,
    cast,
)
import sys
# pylint: disable=missing-docstring

class timespec(Structure):
    _fields_ = [
        # XXX: is this the correct definition ?
        ('tv_sec', c_int64),
        ('tv_nsec', c_long),
    ]

class sockaddr(Structure):
    # XXX: not implemented !
    pass

class iovec(Structure):
    _fields_ = [
        ('iov_base', c_void_p),
        ('iov_len', c_size_t),
    ]

class io_context(Structure):
    pass
io_context_t = POINTER(io_context)
io_context_t_p = POINTER(io_context_t)

# io_iocb_cmd
IO_CMD_PREAD = 0
IO_CMD_PWRITE = 1
IO_CMD_FSYNC = 2
IO_CMD_FDSYNC = 3
IO_CMD_POLL = 5
IO_CMD_NOOP = 6
IO_CMD_PREADV = 7
IO_CMD_PWRITEV = 8

PADDED, PADDEDptr, PADDEDul, PADDEDl = {
    (4, 'little'): (
        lambda w, x, y: [(x, w), (y, c_uint)],
        lambda w, x, y: [(x, w), (y, c_uint)],
        lambda    x, y: [(x, c_ulong), (y, c_uint)],
        lambda    x, y: [(x, c_long), (y, c_uint)],
    ),
    (8, 'little'): (
        lambda w, x, y: [(x, w), (y, w)],
        lambda w, x, _: [(x, w)],
        lambda    x, _: [(x, c_ulong)],
        lambda    x, _: [(x, c_long)],
    ),
    (8, 'big'): (
        lambda w, x, y: [(y, c_uint), (x, w)],
        lambda w, x, _: [(x, w)],
        lambda    x, _: [(x, c_ulong)],
        lambda    x, _: [(x, c_long)],
    ),
    (4, 'big'): (
        lambda w, x, y: [(y, c_uint), (x, w)],
        lambda w, x, y: [(y, c_uint), (x, w)],
        lambda    x, y: [(y, c_uint), (x, c_ulong)],
        lambda    x, y: [(y, c_uint), (x, c_long)],
    ),
}[(sizeof(c_ulong), sys.byteorder)]

class io_iocb_poll(Structure):
    _fields_ = PADDED(c_int, 'events', '__pad1')

class io_iocb_sockaddr(Structure):
    _fields_ = [
        ('addr', POINTER(sockaddr)),
        ('len', c_int),
    ]

class io_iocb_common(Structure):
    _fields_ = (
        PADDEDptr(c_void_p, 'buf', '__pad1') +
        PADDEDul('nbytes', '__pad2') +
        [
            ('offset', c_longlong),
            ('__pad3', c_longlong),
            ('flags', c_uint),
            ('resfd', c_uint),
        ]
    )

class io_iocb_vector(Structure):
    _fields_ = [
        ('vec', POINTER(iovec)),
        ('nr', c_int),
        ('offset', c_longlong),
    ]

class _iocb_u(Union):
    _fields_ = [
        ('c', io_iocb_common),
        ('v', io_iocb_vector),
        ('poll', io_iocb_poll),
        ('saddr', io_iocb_sockaddr),
    ]

class iocb(Structure):
    _fields_ = (
        PADDEDptr(c_void_p, 'data', '__pad1') +
        PADDED(c_uint, 'key', 'aio_rw_flags') +
        [
            ('aio_lio_opcode', c_short),
            ('aio_reqprio', c_short),
            ('aio_fildes', c_int),
            ('u', _iocb_u),
        ]
    )

del _iocb_u

iocb_p = POINTER(iocb)
iocb_pp = POINTER(iocb_p)

class io_event(Structure):
    _fields_ = (
        PADDEDptr(c_void_p, 'data', '__pad1') +
        PADDEDptr(iocb_p, 'obj', '__pad2') +
        # libaio declares these unsigned, which contradicts kernel ABI.
        PADDEDl('res', '__pad3') +
        PADDEDl('res2', '__pad4')
    )
io_event_p = POINTER(io_event)

del PADDED, PADDEDptr, PADDEDul, PADDEDl

io_callback_t = CFUNCTYPE(None, io_context_t, iocb, c_long, c_long)

libaio = CDLL('libaio.so.1')
# pylint: disable=unused-argument
def _raise_on_negative(result, func, arguments):
    if result < 0:
        raise OSError(-result, func.__name__)
    return result
# pylint: enable=unused-argument

def _func(name, *args):
    result = getattr(libaio, name)
    result.restype = c_int
    result.argtypes = args
    result.errcheck = _raise_on_negative
    return result

io_queue_init = _func('io_queue_init', c_int, io_context_t_p)
io_queue_release = _func('io_queue_release', io_context_t)
io_queue_run = _func('io_queue_run', io_context_t)
io_setup = _func('io_setup', c_int, io_context_t_p)
io_destroy = _func('io_destroy', io_context_t)
io_submit = _func('io_submit', io_context_t, c_long, iocb_pp)
io_cancel = _func('io_cancel', io_context_t, iocb_p, io_event_p)
io_getevents = _func(
    'io_getevents',
    io_context_t,
    c_long,
    c_long,
    io_event_p,
    POINTER(timespec),
)

# pylint: disable=redefined-outer-name, too-many-arguments
def io_set_callback(iocb, cb):
    iocb.data = cast(cb, c_void_p)

def zero(struct):
    memset(byref(struct), 0, sizeof(struct))

def _io_prep_prw(opcode, iocb, fd, buf, count, offset, flags=0):
    zero(iocb)
    iocb.aio_fildes = fd
    iocb.aio_lio_opcode = opcode
    iocb.aio_reqprio = 0
    iocb.aio_rw_flags = flags
    iocb.u.c.buf = buf
    iocb.u.c.nbytes = count
    iocb.u.c.offset = offset

def io_prep_pread(iocb, fd, buf, count, offset):
    _io_prep_prw(IO_CMD_PREAD, iocb, fd, buf, count, offset)

def io_prep_pwrite(iocb, fd, buf, count, offset):
    _io_prep_prw(IO_CMD_PWRITE, iocb, fd, buf, count, offset)

def io_prep_preadv(iocb, fd, iov, iovcnt, offset):
    _io_prep_prw(IO_CMD_PREADV, iocb, fd, cast(iov, c_void_p), iovcnt, offset)

def io_prep_pwritev(iocb, fd, iov, iovcnt, offset):
    _io_prep_prw(IO_CMD_PWRITEV, iocb, fd, cast(iov, c_void_p), iovcnt, offset)

def io_prep_preadv2(iocb, fd, iov, iovcnt, offset, flags):
    _io_prep_prw(IO_CMD_PREADV, iocb, fd, cast(iov, c_void_p), iovcnt, offset, flags)

def io_prep_pwritev2(iocb, fd, iov, iovcnt, offset, flags):
    _io_prep_prw(IO_CMD_PWRITEV, iocb, fd, cast(iov, c_void_p), iovcnt, offset, flags)

# io_prep_poll
# io_poll

def io_prep_fsync(iocb, fd):
    zero(iocb)
    iocb.aio_fildes = fd
    iocb.aio_lio_opcode = IO_CMD_FSYNC
    iocb.aio_reqprio = 0

def io_fsync(ctx, iocb, cb, fd):
    io_prep_fsync(iocb, fd)
    io_set_callback(iocb, cb)
    return io_submit(ctx, 1, iocb_pp(byref(iocb)))

def io_prep_fdsync(iocb, fd):
    zero(iocb)
    iocb.aio_fildes = fd
    iocb.aio_lio_opcode = IO_CMD_FDSYNC
    iocb.aio_reqprio = 0

def io_fdsync(ctx, iocb, cb, fd):
    io_prep_fdsync(iocb, fd)
    io_set_callback(iocb, cb)
    return io_submit(ctx, 1, iocb_pp(byref(iocb)))

IOCB_FLAG_RESFD = 1 << 0
IOCB_FLAG_IOPRIO = 1 << 1

def io_set_eventfd(iocb, eventfd):
    iocb.u.c.flags |= IOCB_FLAG_RESFD
    iocb.u.c.resfd = eventfd
# pylint: enable=redefined-outer-name, too-many-arguments, missing-docstring
