Linux AIO API wrapper

This is about in-kernel, file-descriptor-based asynchronous I/O.
It has nothing to do with the `asyncio` standard module.

python 2 Notes
--------------

In python 2.7, a memoryview of a bytearray, despite being writable, is rejected
by ctypes:

.. code:: python

    >>> from ctypes import c_char
    >>> a = bytearray(b'foo')
    >>> c_char.from_buffer(a)
    c_char('f')
    >>> b = memoryview(a)
    >>> b.readonly
    False
    >>> c_char.from_buffer(b)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: expected a writeable buffer object

This means that it is not possible to only read or write a few bytes at the
beginning of a large buffer without having to copy memory.

The same code works fine with python 3.x .

This is considered as python 2.7 ctypes bug, and not a python-libaio bug.
