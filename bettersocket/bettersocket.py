#!/usr/bin/env python3
import socket
import select
from typing import Optional


class BetterSocketReader(object):
    """
    This is a wrapper for low-level sockets, for reading delimited frames.

    Both blocking and non-blocking sockets work out of the box.
    """

    def __init__(self, sock: socket.socket, delimiter: bytes = b"\n"):

        if len(delimiter) != 1:
            raise ValueError("Delimiter must be 1 byte long")

        if not isinstance(sock, socket.socket):
            raise TypeError("Socket must be an instance of socket.socket")

        self._sock = sock
        self._buffer = bytes()
        self._delimiter = delimiter

    def _pop_one_from_buffer(self) -> Optional[bytes]:

        if self._delimiter in self._buffer:
            pos = self._buffer.find(self._delimiter)

            data = self._buffer[:pos]  # data from the beginning until the delimtiter
            self._buffer = self._buffer[pos + 1:]  # skip delimiter

            return data

        return None

    def reset(self):
        """
        This call clears the internal buffer of the instance.
        This does not clear the kernel buffer.
        """
        self._buffer = bytes()

    def readframe(self, chunksize: int = 1024) -> Optional[str]:
        """
        Returns one frame of data between delimiters (without the delimiters)
        Returns None if nothing to read (no delimiter received)
        """

        data = self._pop_one_from_buffer()  # before receive, check if there is a valid data in the buffer
        if data:
            return data

        # actual receiving won't start until there is no more valid message left in the buffer

        try:
            chunk = self._sock.recv(chunksize)  # receive a chunk
        except socket.timeout:
            return None
        except socket.error as e:
            if e.errno == socket.errno.EWOULDBLOCK:  # nothing to read
                return None
            else:
                raise  # everything else should be raised

        if chunk:
            self._buffer += chunk  # append the received chunk to the buffer
            return self._pop_one_from_buffer()  # and check if a valid message received
        else:
            raise ConnectionResetError()  # chunk is only none when the connection is dropped (otherwise it would have returned)


class BetterSocketWriter(object):
    """
    This is a wrapper for low-level sockets, for sending delimited frames.

    Both blocking and non-blocking sockets supported out of the box. Either way it waits for the socket to became ready.
    """

    def __init__(self, sock: socket.socket, delimiter: bytes = b"\n"):

        if not isinstance(sock, socket.socket):
            raise TypeError("Socket must be an instance of socket.socket")

        self._sock = sock
        self._delimiter = delimiter

    def rawsendall(self, data: bytes):
        """
        This call is blocks until the socket is ready. Then sends the data.
        Does not append the delimiter.
        """

        writable = select.select([], [self._sock], [])[1]

        if writable:
            self._sock.sendall(data)

    def sendframe(self, data: bytes):
        """
        This call automatically appends the delimiter to the end of the data.
        blocks until the socket is ready.
        """
        self.rawsendall(data + self._delimiter)


class BetterSocketIO(object):
    """
    This class combines BetterSocketReader and BetterSocketWriter together.
    Functions from both classes are exposed.
    This is the recommended wrapper to use.
    """

    def __init__(self, sock: socket.socket, delimiter: bytes = b"\n"):

        self._socket = sock
        self._reader = BetterSocketReader(sock, delimiter)
        self._writer = BetterSocketWriter(sock, delimiter)

    def readframe(self, chunksize: int = 1024) -> Optional[bytes]:
        """
        Same as BetterSocketReader.readframe
        """
        return self._reader.readframe(chunksize)

    def rawsendall(self, data: bytes):
        """
        Same as BetterSocketWriter.rawsendall
        """
        self._writer.rawsendall(data)

    def sendframe(self, data: bytes):
        """
        Same as BetterSocketWriter.sendframe
        """
        self._writer.sendframe(data)

    def reset(self):
        """
        Same as BetterSocketReader.reset
        """
        self._reader.reset()

    def close(self):
        """
        Closes the underlying socket as well as the reader and writer instance for the socket.
        After this call no further calls should be attempted.
        """
        self._socket.close()
        self._reader = None
        self._writer = None

    def __str__(self) -> str:
        try:

            if self._socket.family in [socket.AF_INET, socket.AF_INET6]:
                host, port = self._socket.getpeername()
                return f"Socket connected to {host}:{port}"

            else:  # including AF_UNIX
                return f"Socket connected to {self._socket.getpeername()}"

        except (OSError, BrokenPipeError):
            return "Unconnected socket"

    def __repr__(self) -> str:
        return f"<{str(self)}>"
