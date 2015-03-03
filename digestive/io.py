from abc import abstractmethod
from os import path


class Source:
    """
    Data source context manager and reader.
    """

    def __init__(self, source):
        self.source = source
        self.fd = None

    def __str__(self):
        return self.source

    def __len__(self):
        return path.getsize(self.source)

    def __enter__(self):
        self.open()
        return self

    def open(self):
        # open named source in binary mode for reading
        self.fd = open(self.source, 'rb')

    def readinto(self, buffer):
        """
        Read data from this source in buffer.

        :param buffer: The buffer to read into.
        :return: The number of bytes read.
        """
        return self.fd.readinto(buffer)

    def blocks(self, block_size=1 << 20):
        """
        Generator for blocks of at most block_size read from this source.

        :param block_size: Maximum number of bytes to read at a time.
        :return: Data block generator.
        """
        current, swap = memoryview(bytearray(block_size)), memoryview(bytearray(block_size))
        num_read = self.readinto(current)
        while num_read:
            # yield the current block, excluding possible stale bytes not read
            yield current[:num_read]
            # swap buffers, allowing next block to be read into different buffer
            current, swap = swap, current
            num_read = self.readinto(current)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.fd.close()
        self.fd = None


class Sink:
    """
    Base class for digesting data in chunks.
    """

    def __init__(self, name=None):
        self.name = name

    @abstractmethod
    def process(self, data):
        """
        Processes a chunk of data.

        :param data: Chunk of data.
        """
        pass

    @abstractmethod
    def result(self):
        """
        Creates the result of this sink and returns it.

        :return: The result of this sink as a string.
        """
        pass
