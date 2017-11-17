#!/usr/bin/env python
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
