# Copyright (C) 2017-2019  Vincent Pelletier <plr.vincent@gmail.com>
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
pythonic wrapper for libaio

With minimal eventfd support to make possible to integrate with usual polling
mechanisms already available in select module.
"""
from __future__ import absolute_import
from ctypes import addressof, byref, cast, c_char, c_void_p, pointer
import errno
from mmap import mmap
import os
from struct import pack, unpack
import sys
from . import libaio
from .eventfd import eventfd, EFD_CLOEXEC, EFD_NONBLOCK, EFD_SEMAPHORE
from . import linux_fs
from . import ioprio
# pylint: disable=wildcard-import
from .linux_fs import *
from .ioprio import *
# pylint: enable=wildcard-import
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

if sys.version_info[0] == 2:
    # pylint: disable=redefined-builtin
    range = xrange
    # pylint: enable=redefined-builtin

__all__ = (
    'EFD_CLOEXEC', 'EFD_NONBLOCK', 'EFD_SEMAPHORE',
    'EventFD', 'AIOBlock', 'AIOContext',
    'AIOBLOCK_MODE_READ', 'AIOBLOCK_MODE_WRITE',
    'AIOBLOCK_MODE_FSYNC', 'AIOBLOCK_MODE_FDSYNC',
    'AIOBLOCK_MODE_POLL',
) + linux_fs.__all__ + ioprio.__all__

class EventFD(object):
    """
    Minimal file-like object for eventfd.
    """
    def __init__(self, initval=0, flags=0):
        """
        initval (int 0..2**64 - 1)
            Internal counter value.
        flags (int)
            Bit mask of EFD_* constants.
        """
        self._file = os.fdopen(eventfd(initval, flags), 'r+b')

    def __enter__(self):
        """
        Returns self.
        """
        return self

    def __exit__(self, exc_type, ex_val, exc_tb):
        """
        Calls self.close().
        """
        self.close()

    def close(self):
        """
        Close file.
        """
        self._file.close()

    def read(self):
        """
        Read current counter value.

        See manpage for flags effect on this.
        """
        return unpack('Q', self._file.read(8))[0]

    def write(self, value):
        """
        Add given value to counter.
        """
        self._file.write(pack('Q', value))

    def fileno(self):
        """
        Return eventfd's file descriptor.
        """
        return self._file.fileno()

AIOBLOCK_MODE_READ = object()
AIOBLOCK_MODE_WRITE = object()
AIOBLOCK_MODE_FSYNC = object()
AIOBLOCK_MODE_FDSYNC = object()
AIOBLOCK_MODE_POLL = object()

class AIOBlock(object):
    """
    Asynchronous I/O block.

    Defines a (list of) buffer(s) to read into or write from, and what should
    happen on completion.
    """
    _AIOBLOCK_MODE_DICT = {
        AIOBLOCK_MODE_READ: libaio.IO_CMD_PREADV,
        AIOBLOCK_MODE_WRITE: libaio.IO_CMD_PWRITEV,
        AIOBLOCK_MODE_FSYNC: libaio.IO_CMD_FSYNC,
        AIOBLOCK_MODE_FDSYNC: libaio.IO_CMD_FDSYNC,
        AIOBLOCK_MODE_POLL: libaio.IO_CMD_POLL,
    }
    _REVERSE_AIOBLOCK_MODE_DICT = {
        y: x for x, y in _AIOBLOCK_MODE_DICT.items()
    }
    assert len(_AIOBLOCK_MODE_DICT) == len(_REVERSE_AIOBLOCK_MODE_DICT)
    _buffer_list = None
    _eventfd = None
    _file = None
    _iovec = None
    _onCompletion = None

    def __init__(
        self,
        mode,
        target_file=None,
        buffer_list=(),
        offset=0,
        # pylint: disable=redefined-outer-name
        eventfd=None,
        # pylint: enable=redefined-outer-name
        onCompletion=lambda block, res, res2: None,
        rw_flags=0,
        io_priority=None,
        event_mask=0,
    ):
        """
        mode (AIOBLOCK_MODE_*)
            The action this block represents.
        target_file (file-ish)
            The file to read from/write to.
        buffer_list (list of mutable buffer instances: mmap, bytearray, ...)
            Buffers to use.
            Must be empty in AIOBLOCK_MODE_POLL.
        offset (int)
            Where to start reading from/writing to.
            Must be zero in AIOBLOCK_MODE_POLL.
        eventfd (EventFD)
            An eventfd file, so AIO completion can be waited upon by
            select/poll/epoll.
        onCompletion (callable)
            Receives as arguments:
            - the AIOBlock instance which completed
            - res (int)
            - res2 (int)
            For forward compatibility, should return None.
        rw_flags (int)
            OR-ed RWF_* constants, see aio_rw_flags in io_submit(2) manpage.
            Must be zero in AIOBLOCK_MODE_POLL.
        io_priority (int)
            Request io priority & class, as returned by IOPRIO_PRIO_VALUE.
            "class" may be one of:
                IOPRIO_CLASS_RT: real-time
                IOPRIO_CLASS_BE: best-effort
                IOPRIO_CLASS_IDLE: idle
            "data" meaning depends on class, see ioprio_set(2) manpage.
        event_mask (int)
            OR-ed select.EPOLL* constants. EPOLLERR and EPOLLHUP are always
            enabled.
        """
        self._iocb = iocb = libaio.iocb()
        libaio.zero(iocb)
        self.mode = mode
        self.target_file = target_file
        self.io_priority = io_priority
        if mode is AIOBLOCK_MODE_POLL:
            self.event_mask = event_mask
        else:
            self.buffer_list = buffer_list
            self.offset = offset
            self.rw_flags = rw_flags
        self.eventfd = eventfd
        self.onCompletion = onCompletion

    @property
    def mode(self):
        """
        This instance's mode.

        Clears buffer_list, offset, event_mask and rw_flags when changed
        between AIOBLOCK_MODE_POLL and any other mode.
        """
        return self._REVERSE_AIOBLOCK_MODE_DICT[self._iocb.aio_lio_opcode]

    @mode.setter
    def mode(self, value):
        old_opcode = self._iocb.aio_lio_opcode
        new_opcode = self._AIOBLOCK_MODE_DICT[value]
        if old_opcode != new_opcode:
            if new_opcode == libaio.IO_CMD_POLL:
                self.buffer_list = ()
                self.offset = 0
                self.rw_flags = 0
            elif old_opcode == libaio.IO_CMD_POLL:
                self.event_mask = 0
        self._iocb.aio_lio_opcode = new_opcode

    @property
    def target_file(self):
        """
        The file object this instance operates on.
        """
        return self._file

    @target_file.setter
    def target_file(self, value):
        self._file = value
        if value is None:
            self._iocb.aio_fildes = 0
        else:
            self._iocb.aio_fildes = getattr(value, 'fileno', lambda: value)()

    @property
    def buffer_list(self):
        """
        The buffer list this instance operates on.

        Only available in mode != AIOBLOCK_MODE_POLL.

        Changes on a submitted transfer are not fully applied until its
        next submission: kernel will still be using original buffer list.
        """
        if self._iocb.aio_lio_opcode == libaio.IO_CMD_POLL:
            raise AttributeError
        return self._buffer_list

    @buffer_list.setter
    def buffer_list(self, value):
        if self._iocb.aio_lio_opcode == libaio.IO_CMD_POLL:
            raise AttributeError
        # Keep a reference to original buffers, in case caller does not, so
        # they do not get garbage-collected. Make it a tuple to avoid caller
        # mutating "value".
        buffer_list = tuple(value)
        iocb = self._iocb
        iocb.u.c.nbytes = buffer_count = len(buffer_list)
        if buffer_count:
            self._iovec = iovec = (libaio.iovec * buffer_count)(*[
                libaio.iovec(
                    c_void_p(addressof(c_char.from_buffer(x))),
                    # Mimic file.write, with workaround for python2.7 bug:
                    # mmap objects are rejected by memoryview.
                    len(x if isinstance(x, mmap) else memoryview(x)),
                )
                for x in buffer_list
            ])
            iocb.u.c.buf = c_void_p(addressof(iovec))
        else:
            iocb.u.c.buf = None
            self._iovec = None
        self._buffer_list = buffer_list

    @property
    def event_mask(self):
        """
        The events this block will wait for.

        Only available in mode == AIOBLOCK_MODE_POLL.
        """
        if self._iocb.aio_lio_opcode != libaio.IO_CMD_POLL:
            raise AttributeError
        return self._iocb.u.c.buf.value

    @event_mask.setter
    def event_mask(self, value):
        if self._iocb.aio_lio_opcode != libaio.IO_CMD_POLL:
            raise AttributeError
        self._iocb.u.c.buf = c_void_p(value)

    @property
    def offset(self):
        """
        The file offset this instance writes to/reads from.

        Only available in mode != AIOBLOCK_MODE_POLL.
        """
        return self._iocb.u.c.offset.value

    @offset.setter
    def offset(self, value):
        self._iocb.u.c.offset = value

    @property
    def onCompletion(self):
        """
        Called by AIOContext upon block completion.

        res (int)
        res2 (int)
            target_file-dependent values describing completion conditions.
            Like the number of bytes read/written, error codes, ...
        """
        return self._onCompletion

    @onCompletion.setter
    def onCompletion(self, value):
        self._onCompletion = value

    @property
    def io_priority(self):
        """
        IO priority for this instance.
        """
        return (
            self._iocb.aio_reqprio
            if self._iocb.u.c.flags & libaio.IOCB_FLAG_IOPRIO else
            None
        )

    @io_priority.setter
    def io_priority(self, value):
        iocb = self._iocb
        if value is None:
            iocb.u.c.flags &= ~libaio.IOCB_FLAG_IOPRIO
            iocb.aio_reqprio = 0
        else:
            iocb.u.c.flags |= libaio.IOCB_FLAG_IOPRIO
            iocb.aio_reqprio = value

    @property
    def rw_flags(self):
        """
        RWF_* bitmask.

        Only available in mode != AIOBLOCK_MODE_POLL.
        """
        if self._iocb.aio_lio_opcode == libaio.IO_CMD_POLL:
            raise AttributeError
        return self._iocb.aio_rw_flags

    @rw_flags.setter
    def rw_flags(self, value):
        if self._iocb.aio_lio_opcode == libaio.IO_CMD_POLL:
            raise AttributeError
        self._iocb.aio_rw_flags = value

    @property
    def eventfd(self):
        """
        eventfd file to use for event notifications.
        """
        return self._eventfd

    @eventfd.setter
    def eventfd(self, value):
        iocb = self._iocb
        if value is None:
            iocb.u.c.flags &= ~libaio.IOCB_FLAG_RESFD
            iocb.u.c.resfd = 0
        else:
            iocb.u.c.flags |= libaio.IOCB_FLAG_RESFD
            iocb.u.c.resfd = getattr(value, 'fileno', lambda: value)()
        self._eventfd = eventfd

    def _getSubmissionState(self):
        """
        For internal use only.
        """
        # Returns all values which must not be garbage collected until completion.
        return (self._buffer_list, self._iovec)

class AIOContext(object):
    """
    Linux Ashynchronous IO context.
    """
    _ctx = None

    def __init__(self, maxevents):
        """
        maxevents (int)
            Maximum number of events this context will have to handle.
        """
        self._maxevents = maxevents
        self._submitted = {}
        # Avoid garbage collection issues on interpreter shutdown.
        self._io_queue_release = libaio.io_queue_release
        ctx = libaio.io_context_t()
        # Note: almost same as io_setup
        libaio.io_queue_init(self._maxevents, byref(ctx))
        self._ctx = ctx

    def close(self):
        """
        Cancels all pending IO blocks.
        Waits until all non-cancellable IO blocks finish.
        De-initialises AIO context.
        """
        if self._ctx is not None:
            # Note: same as io_destroy
            self._io_queue_release(self._ctx)
            del self._ctx

    def __enter__(self):
        """
        Returns self.
        """
        return self

    def __exit__(self, exc_type, ex_val, exc_tb):
        """
        Calls close.
        """
        self.close()

    def __del__(self):
        """
        Calls close, in case instance was not properly closed by the time it
        gets garbage-collected.
        """
        self.close()

    def submit(self, block_list):
        """
        Submits transfers.

        block_list (list of AIOBlock)
            The IO blocks to hand off to kernel.

        Returns the number of successfully submitted blocks.
        """
        # A non-set file will cause an AIO block on stdin, which is likely not
        # expected. Do this extra check when assertions are enabled.
        assert not any(x.target_file is None for x in block_list)
        # io_submit ioctl will only return an error for issues with the first
        # transfer block. If there are issues with a later block, it will stop
        # submission and return the number of submitted blocks. So it is safe
        # to only update self._submitted once io_submit returned.
        submitted_count = libaio.io_submit(
            self._ctx,
            len(block_list),
            (libaio.iocb_p * len(block_list))(*[
                # pylint: disable=protected-access
                pointer(x._iocb)
                # pylint: enable=protected-access
                for x in block_list
            ]),
        )
        submitted = self._submitted
        for block in block_list[:submitted_count]:
            # pylint: disable=protected-access
            submitted[addressof(block._iocb)] = (block, block._getSubmissionState())
            # pylint: enable=protected-access
        return submitted_count

    def _eventToPython(self, event):
        aio_block, _ = self._submitted.pop(addressof(event.obj.contents))
        aio_block.onCompletion(aio_block, event.res, event.res2)
        return (
            aio_block,
            event.res,
            event.res2,
        )

    def cancel(self, block):
        """
        Cancel an IO block.

        block (AIOBlock)
            The IO block to cancel.

        Returns cancelled block's event data (see getEvents), or None if the
        kernel returned EINPROGRESS. In the latter case, event completion will
        happen on a later getEvents call.
        """
        event = libaio.io_event()
        try:
            # pylint: disable=protected-access
            libaio.io_cancel(self._ctx, byref(block._iocb), byref(event))
            # pylint: enable=protected-access
        except OSError as exc:
            if exc.errno == errno.EINPROGRESS:
                return None
            raise
        return self._eventToPython(event)

    def cancelAll(self):
        """
        Cancel all submitted IO blocks.

        Blocks until all submitted transfers have been finalised.
        Submitting more transfers or processing completion events while this
        method is running produces undefined behaviour.
        Returns the list of values returned by individual cancellations.
        See "cancel" documentation.
        """
        cancel = self.cancel
        result = []
        for block, _ in self._submitted.values():
            try:
                result.append(cancel(block))
            except OSError as exc:
                # EINVAL should mean we requested to cancel a not-in-flight
                # transfer - maybe it was just completed and we just did
                # not process its completion event yet.
                if exc.errno != errno.EINVAL:
                    raise
        return result

    def getEvents(self, min_nr=1, nr=None, timeout=None):
        """
        Returns a list of event data from submitted IO blocks.

        min_nr (int, None)
            When timeout is None, minimum number of events to collect before
            returning.
            If None, waits for all submitted events.
        nr (int, None)
            Maximum number of events to return.
            If None, set to maxevents given at construction or to the number of
            currently submitted events, whichever is larger.
        timeout (float, None):
            Time to wait for events.
            If None, become blocking.

        Returns a list of 3-tuples, containing:
        - completed AIOBlock instance
        - res, file-object-type-dependent value
        - res2, another file-object-type-dependent value
        """
        if min_nr is None:
            min_nr = len(self._submitted)
        if nr is None:
            nr = max(len(self._submitted), self._maxevents)
        if timeout is None:
            timeoutp = None
        else:
            sec = int(timeout)
            timeout = libaio.timespec(sec, int((timeout - sec) * 1e9))
            timeoutp = byref(timeout)
        event_buffer = (libaio.io_event * nr)()
        actual_nr = libaio.io_getevents(
            self._ctx,
            min_nr,
            nr,
            event_buffer,
            timeoutp,
        )
        return [
            self._eventToPython(event_buffer[x])
            for x in range(actual_nr)
        ]
