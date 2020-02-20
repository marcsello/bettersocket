#!/usr/bin/env python3
import socket
import select
from typing import Optional


class BetterSocketReader():
    """
    This socket reader is designed to read delimited chunks from the socket efficently
    """

    def __init__(self, sock: socket.socket, delimiter: bytes = b"\n"):

        if len(delimiter) != 1:
            raise ProgrammingError("Delimiter must be 1 byte long")

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
        This call clears the internal buffer of the BetterSocketReader instance.
        It does not alter the kernel buffer.
        """
        self._buffer = bytes()

    def readframe(self, chunksize: int = 1024) -> Optional[str]:  # timeouting and nonblocking sockets both expected as well as blocking, expected to be called in a loop
        """
        Returns one chunk of data between delimiters (without the delimiters)
        Returns None if nothing to read (no delimiter recieved)
        """

        data = self._pop_one_from_buffer()  # before recieve, check if there is a valid data in the buffer
        if data:
            return data

        # actual recieving won't start until there is no more valid message left in the buffer

        try:
            chunk = self._sock.recv(chunksize)  # recieve a chunk
        except socket.timeout:
            return None
        except socket.error as e:
            if e.errno == socket.errno.EWOULDBLOCK:  # nothing to read
                return None
            else:
                raise  # everything else should be raised

        if chunk:
            self._buffer += chunk  # append the recieved chunk to the buffer
            return self._pop_one_from_buffer()  # and check if a valid message recieved
        else:
            raise ConnectionResetError()  # chunk is only none when the connection is dropped (otherwise it would have returned)


class BetterSocketWriter():
    """
    This is a wrapper for sending with nonblocking sockets
    It kinda makes a nonblocking socket a little blocking in terms of sending, avoiding socket not ready errors
    """

    def __init__(self, sock: socket.socket, delimiter: bytes = b"\n"):

        if not isinstance(sock, socket.socket):
            raise TypeError("Socket must be an instance of socket.socket")

        self._sock = sock
        self._delimiter = delimiter

    def rawsendall(self, data: bytes):
        """
        This call is blocks until the socket is ready to send data. Then sends the data.
        """

        writable = select.select([], [self._sock], [])[1]

        if writable:
            self._sock.sendall(data)

    def sendframe(self, data: bytes):
        """
        This call sends a frame.
        Works the same as rawsendall
        """
        self.rawsendall(data + self._delimiter)


class BetterSocketIO:
    """
    This class combines BetterSocketReader and BetterSocketWriter together
    This is a simple wrapper that makes working with sockets just a little bit easier
    Also exposes the fileno (as well as some basic functionality) so this class can be used in select.select
    """

    def __init__(self, sock: socket.socket, delimiter: bytes = b"\n"):

        self._socket = sock
        self._reader = BetterSocketReader(sock, delimiter)
        self._writer = BetterSocketWriter(sock, delimiter)

    def readframe(self, chunksize: int = 1024) -> Optional[bytes]:
        return self._reader.readframe(chunksize)

    def rawsendall(self, data: bytes):
        self._writer.rawsendall(data)

    def sendframe(self, data: bytes):
        """
        Same as BetterSocketWriter.sendframe
        """
        self._writer.sendframe(data)

    def fileno(self) -> int:
        return self._socket.fileno()

    def close(self):
        """
        Closes the underlying socket as well as the reader and writer instance for the socket.
        After this call no further calls should be attempted.
        """
        self._socket.close()
        self._reader = None  # are those really necessary?
        self._writer = None

    def __str__(self):  # This is probably not very good for UINIX sockets
        try:
            host, port = self._socket.getpeername()
            return "Socket connected to {}:{}".format(host, port)

        except (OSError, BrokenPipeError):
            return "Unconnected socket"
