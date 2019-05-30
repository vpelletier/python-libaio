Linux AIO API wrapper

This is about in-kernel, file-descriptor-based asynchronous I/O.
It has nothing to do with the ``asyncio`` standard module.

Linux AIO primer
----------------

When sending or expecting data, the typical issue a developer faces is knowing
when the operation will complete, so the program can carry on.

- read/write/recv/send: blocks until stuff happened
- same, on a non-blocking file descriptor: errors out instead of blocking,
  developper has to implement retry somehow, and may end up wasting CPU time
  just resubmitting the same operation over and over.
- select/poll/epoll: kernel tells the program when (re)submitting an operation
  should not block (if developer is careful to not have competing IO sources)

AIO is the next level: the application expresses the intention that some IO
operation happens when the file descriptor accepts it *and* provides
corresponding buffer to the kernel.
Compared to select/poll/epoll, this avoids one round-trip to userland when the
operation becomes possible:

- kernel sends notification (ex: fd is readable)
- program initiates actual IO (ex: read from fd)

Instead, kernel only has to notify userland the operation is already completed,
and application may either process received data, or submit more data to send.

Edge cases
----------

Because of this high level of integration, low-level implementation
constraints which are abstracted by higher-overhead APIs may become apparent.

For example, when submitting AIO blocks to an USB gadget endpoint file, the
block should be aligned to page boundaries because some USB Device Controllers
do not have the ability to read/write partial pages.

In python, this means ``mmap`` should be used to allocate such buffer instead
of just any ``bytearray``.

Another place where implementation details appear is completion statuses,
``res`` and ``res2``. Their meaning depends on the module handling operations
on used file descriptor, so python-libaio transmits these values without
assuming their meaning (rather than, say, raise on negative values).

Yet another place is application-initiated closures: there is a fundamental
race-condition when cancelling an AIO block (maybe hardware-triggered
completion will happen first, or maybe software-initiated cancellation will).
In any case, a completion event will be produced and application may check
which origin won. A consequence of this is that AIO context closure may take
time: while requesting cancellation does not block, software should wait for
hardware to hand the buffers back.

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
