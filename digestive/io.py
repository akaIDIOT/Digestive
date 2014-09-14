from os import path


class Source:
    """
    Data source context manager and reader.
    """

    def __init__(self, source):
        self.source = source
        self.fd = None

    def __len__(self):
        return path.getsize(self.source)

    def __enter__(self):
        self.open()
        return self

    def open(self):
        # open named source in binary mode for reading
        self.fd = open(self.source, 'rb')

    def readinto(self, buffer):
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

    def update(self, data):
        """
        Updates this digest with a chunk of data.

        :param data: Chunk of data.
        """
        pass

    def digest(self):
        """
        Creates the result of this digest and returns it.

        :return: The result of this digest as a string.
        """
        pass