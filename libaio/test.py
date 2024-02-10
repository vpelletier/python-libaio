#!/usr/bin/env python
# Copyright (C) 2017-2024  Vincent Pelletier <plr.vincent@gmail.com>
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
Testing libaio.
"""
from __future__ import absolute_import, print_function
import errno
from mmap import mmap
import os
import unittest
import select
import tempfile
import libaio

# BBB: <3.7
RWF_NOWAIT = getattr(os, 'RWF_NOWAIT', 8)

class LibAIOTests(unittest.TestCase):
    """
    Testing libaio.
    """
    def testReadWrite(self):
        """
        Most baic functions: without these, libaio will not be of much use.
        """
        with tempfile.TemporaryFile() as temp, libaio.AIOContext(1) as io_context:
            def readall():
                """
                Reread the whole tempfile.
                """
                temp.seek(0)
                return temp.read()
            temp.write(b'blah')
            temp.flush()
            completion_event_list = []
            onCompletion = lambda block, res, res2: (
                completion_event_list.append((block, res, res2))
            )

            read_buf_0 = bytearray(2)
            read_buf_1 = mmap(-1, 2)
            read_buffer_list = [
                read_buf_0,
                read_buf_1,
            ]
            read_block = libaio.AIOBlock(
                mode=libaio.AIOBLOCK_MODE_READ,
                target_file=temp,
                buffer_list=read_buffer_list,
                offset=0,
                onCompletion=onCompletion,
            )
            self.assertEqual(read_block.mode, libaio.AIOBLOCK_MODE_READ)
            self.assertEqual(
                len(read_block.buffer_list),
                len(read_buffer_list),
            )
            self.assertIs(read_block.buffer_list[0], read_buf_0)
            self.assertIs(read_block.buffer_list[1], read_buf_1)
            self.assertEqual(read_block.offset, 0)
            self.assertEqual(read_block.io_priority, None)
            read_block.io_priority = 1
            self.assertEqual(read_block.io_priority, 1)
            read_block.io_priority = None
            self.assertEqual(read_block.io_priority, None)
            self.assertEqual(read_block.rw_flags, 0)
            read_block.rw_flags = RWF_NOWAIT
            self.assertEqual(read_block.rw_flags, RWF_NOWAIT)
            read_block.rw_flags = 0
            self.assertEqual(read_block.rw_flags, 0)
            self.assertEqual(read_block.target_file, temp)
            # Submitting the same block multiple times fails
            self.assertRaises(
                ValueError,
                io_context.submit,
                [read_block, read_block],
            )
            # and the whole submition was undone, so it is possible to submit
            io_context.submit([read_block])
            # but submitting the same block again fails and (later) handling
            # completion of the successfuly submitted block must succeed.
            self.assertRaises(
                ValueError,
                io_context.submit,
                [read_block],
            )
            read_event_list_reference = [(read_block, 4, 0)]
            self.assertEqual(
                read_event_list_reference,
                io_context.getEvents(min_nr=None),
            )
            self.assertEqual(
                read_event_list_reference,
                completion_event_list,
            )
            self.assertEqual(read_buf_0, bytearray(b'bl'))
            self.assertEqual(list(read_buf_1), [b'a', b'h'])
            del completion_event_list[:]

            write_buffer_list = [
                bytearray(b'u'),
                bytearray(b'ez'),
            ]
            write_block = libaio.AIOBlock(
                mode=libaio.AIOBLOCK_MODE_WRITE,
                target_file=temp,
                buffer_list=write_buffer_list,
                offset=2,
                onCompletion=onCompletion,
            )
            self.assertEqual(write_block.mode, libaio.AIOBLOCK_MODE_WRITE)
            self.assertEqual(
                len(write_block.buffer_list),
                len(write_buffer_list),
            )
            self.assertIs(write_block.buffer_list[0], write_buffer_list[0])
            self.assertIs(write_block.buffer_list[1], write_buffer_list[1])
            self.assertEqual(write_block.offset, 2)
            io_context.submit([write_block])
            write_event_list_reference = [(write_block, 3, 0)]
            self.assertEqual(
                write_event_list_reference,
                io_context.getEvents(min_nr=None),
            )
            self.assertEqual(
                write_event_list_reference,
                completion_event_list,
            )
            self.assertEqual(readall(), b'bluez')

    def testFsync(self):
        """
        FSYNC was introduced in a later kernel version than READ/WRITE.
        (along with FDSYNC)
        """
        with tempfile.TemporaryFile() as temp, libaio.AIOContext(1) as io_context:
            completion_event_list = []
            onCompletion = lambda block, res, res2: (
                completion_event_list.append((block, res, res2))
            )
            fsync_block = libaio.AIOBlock(
                mode=libaio.AIOBLOCK_MODE_FSYNC,
                target_file=temp,
                onCompletion=onCompletion,
            )
            try:
                io_context.submit([fsync_block])
            except OSError as exc:
                if exc.errno != errno.EINVAL:
                    raise
                raise unittest.SkipTest('FSYNC kernel support missing')
            fsync_event_list_reference = [(fsync_block, 0, 0)]
            self.assertEqual(
                fsync_event_list_reference,
                io_context.getEvents(min_nr=None),
            )
            self.assertEqual(
                fsync_event_list_reference,
                completion_event_list,
            )

    def testFDsync(self):
        """
        FDSYNC was introduced in a later kernel version than READ/WRITE.
        (along with FSYNC)
        """
        with tempfile.TemporaryFile() as temp, libaio.AIOContext(1) as io_context:
            completion_event_list = []
            onCompletion = lambda block, res, res2: (
                completion_event_list.append((block, res, res2))
            )
            fdsync_block = libaio.AIOBlock(
                mode=libaio.AIOBLOCK_MODE_FDSYNC,
                target_file=temp,
                onCompletion=onCompletion,
            )
            try:
                io_context.submit([fdsync_block])
            except OSError as exc:
                if exc.errno != errno.EINVAL:
                    raise
                raise unittest.SkipTest('FDSYNC kernel support missing')
            fdsync_event_list_reference = [(fdsync_block, 0, 0)]
            self.assertEqual(
                fdsync_event_list_reference,
                io_context.getEvents(min_nr=None),
            )
            self.assertEqual(
                fdsync_event_list_reference,
                completion_event_list,
            )

    def testPoll(self):
        """
        POLL was introduced in a later kernel version than FSYNC/FDSYNC.
        """
        with libaio.AIOContext(1) as io_context:
            completion_event_list = []
            onCompletion = lambda block, res, res2: (
                completion_event_list.append((block, res, res2))
            )
            read_end, write_end = os.pipe()
            try:
                poll_block = libaio.AIOBlock(
                    mode=libaio.AIOBLOCK_MODE_POLL,
                    target_file=read_end,
                    onCompletion=onCompletion,
                    event_mask=select.EPOLLIN,
                )
                self.assertEqual(poll_block.event_mask, select.EPOLLIN)
                try:
                    io_context.submit([poll_block])
                except OSError as exc:
                    if exc.errno != errno.EINVAL:
                        raise
                    raise unittest.SkipTest('POLL kernel support missing')
                self.assertEqual([], io_context.getEvents(min_nr=0))
                self.assertEqual([], completion_event_list)
                os.write(write_end, b'foo')
                poll_event_list_reference = [(
                    poll_block,
                    select.EPOLLIN | select.EPOLLRDNORM,
                    0,
                )]
                self.assertEqual(
                    poll_event_list_reference,
                    io_context.getEvents(min_nr=None),
                )
                self.assertEqual(
                    poll_event_list_reference,
                    completion_event_list,
                )
            finally:
                os.close(write_end)
                os.close(read_end)


if __name__ == '__main__':
    unittest.main()
