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

This is considered a python 2.7 ctypes or memoryview bug, and not a python-libaio bug.

Also, memoryview refuses to use an mmap object:

.. code:: python

    >>> import mmap
    >>> a = mmap.mmap(-1, 16*1024)
    >>> b = memoryview(a)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: cannot make memory view because object does not have the buffer interface
    >>>

...but ctypes is happy with it:

.. code:: python

    >>> import ctypes
    >>> c = (ctypes.c_char * len(a)).from_buffer(a)
    >>>

...and memoryview accepts being constructed over ctype objects:

.. code:: python

    >>> d = memoryview(c)
    >>>

...and it really works !

.. code:: python

    >>> a[0]
    '\x00'
    >>> c[0]
    '\x00'
    >>> d[0]
    '\x00'
    >>> d[0] = '\x01'
    >>> c[0]
    '\x01'
    >>> a[0]
    '\x01'
    >>> a[0] = '\x02'
    >>> c[0]
    '\x02'
    >>> d[0]
    '\x02'

This is considered a python 2.7 memoryview or mmap bug.
