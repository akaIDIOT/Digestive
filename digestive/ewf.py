import ctypes
from ctypes import byref, cdll
from ctypes.util import find_library
from glob import glob

from digestive.io import Source


_ewf = find_library('ewf')
_ewf = cdll.LoadLibrary(_ewf) if _ewf else None
if not _ewf:
    raise ImportError('libewf')


def _ewf_error(error):
    """
    Returns an error message associated with error as returned by libewf calls.

    :param error: A ctypes.c_int pointing to a libewf error.
    :return: A error message formatted by libewf.
    """
    if error.value == 0:
        return None

    message = bytearray(128)  # TODO: will 128 bytes always cover the message?
    message = (ctypes.c_char * len(message)).from_buffer(message)
    _ewf.libewf_error_sprint(error, message)

    return str(message, 'utf-8')


def _ewf_init_handle():
    """
    Initializes a libewf handle.

    :return: A value usable as the handle argument to libewf calls.
    """
    handle = ctypes.c_uint()
    error = ctypes.c_uint()
    _ewf.libewf_handle_initialize(byref(handle), byref(error))

    if error.value != 0:
        raise ValueError(_ewf_error(error))

    return handle


def _ewf_open(names):
    """
    Opens an EWF file or fileset.

    :param names: Either the basename of a set of EWF files (like file.E01) or a collection of names (like
                  [file.E01, file.E01, file.E03].
    :return: A value usable as the handle argument to libewf calls.
    """
    if isinstance(names, str) and not names.lower().endswith('e01'):  # TODO: libewf likely supports more than just E01
        raise ValueError('invalid basename for EWF file: {}'.format(names))

    if isinstance(names, str):
        # glob a basename like file.E01 into a list like [file.E01, file.E02, file.E03, ...]
        names = [bytes(name, 'utf-8') for name in glob(names[:-2] + '??')]

    names_arg = (ctypes.c_char_p * len(names))()
    names_arg[:] = names

    handle = _ewf_init_handle()
    error = ctypes.c_uint()
    _ewf.libewf_handle_open(handle,
                            byref(names_arg),
                            ctypes.c_int(len(names_arg)),
                            ctypes.c_int(0x01),  # access flag read
                            byref(error))
    if error.value != 0:
        raise ValueError(_ewf_error(error))

    return handle


def _ewf_size(handle):
    """
    Gets the size of the original source of the EWF fileset represented by handle.

    :param handle: The handle to pass to libewf.
    :return: The size of the data in fileset in bytes.
    """
    size = ctypes.c_uint64()
    error = ctypes.c_uint()
    _ewf.libewf_handle_get_media_size(handle, byref(size), byref(error))

    if error.value != 0:
        raise ValueError(_ewf_error(error))

    return size.value


def _ewf_readinto(handle, buffer):
    """
    Reads data from the current position of handle into the provided buffer.

    :param handle: The handle to pass to libewf.
    :param buffer: The buffer to read into.
    :return: The number of bytes read.
    """
    # create ctypes buffer pointing to data in buffer
    num_bytes = len(buffer)
    buffer = (ctypes.c_char * num_bytes).from_buffer(buffer)
    error = ctypes.c_uint()
    num_read = _ewf.libewf_handle_read_buffer(handle,
                                              byref(buffer),
                                              ctypes.c_size_t(num_bytes),
                                              byref(error))

    if error.value != 0:
        raise ValueError(_ewf_error(error))

    return num_read


def _ewf_close(handle):
    """
    Closes handle and frees it.

    :param handle: The handle to close.
    """
    # ignore errors at this point
    _ewf.libewf_handle_close(handle, byref(ctypes.c_uint()))
    _ewf.libewf_handle_free(byref(handle), byref(ctypes.c_uint()))


class EWFSource(Source):
    """
    Source implementation reading bytes from an EWF fileset, created from its primary file.
    """

    def __init__(self, source):
        super().__init__(source)

    def __len__(self):
        return _ewf_size(self.fd)

    def open(self):
        self.fd = _ewf_open(self.source)

    def readinto(self, buffer):
        return _ewf_readinto(self.fd, buffer)

    def close(self):
        _ewf_close(self.fd)
        self.fd = None
