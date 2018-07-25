#!/usr/bin/env python
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
from __future__ import absolute_import, print_function
import tempfile
import libaio

def main():
    temp = tempfile.TemporaryFile()
    temp.write(b'blah')
    with libaio.AIOContext(1) as io_context:
        read_block = libaio.AIOBlock(
            libaio.AIOBLOCK_MODE_READ,
            temp,
            [
                bytearray(2),
                bytearray(2),
            ],
            0,
        )
        write_block = libaio.AIOBlock(
            libaio.AIOBLOCK_MODE_WRITE,
            temp,
            [
                bytearray(b"u"),
                bytearray(b"e"),
            ],
            2,
        )
        print(read_block, write_block)
        io_context.submit([read_block])
        for event in io_context.getEvents():
            print(event)
        temp.seek(0)
        print(temp.read())
        io_context.submit([write_block])
        for event in io_context.getEvents():
            print(event)
        temp.seek(0)
        print(temp.read())

if __name__ == '__main__':
    main()
