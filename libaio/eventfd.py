from ctypes import CDLL, c_uint, c_int, get_errno

libc = CDLL("libc.so.6", use_errno=True)
def _raise_errno_on_neg_one(result, func, arguments):
    if result == -1:
        raise IOError(get_errno())
    return result

eventfd = libc.eventfd
eventfd.restype = c_int
eventfd.argtypes = (c_int, c_uint)
eventfd.errcheck = _raise_errno_on_neg_one

EFD_CLOEXEC = 0o02000000
EFD_NONBLOCK = 0o00004000
EFD_SEMAPHORE = 0o00000001
