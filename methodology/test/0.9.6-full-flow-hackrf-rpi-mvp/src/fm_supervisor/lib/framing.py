"""Length-prefixed JSON framing for Unix stream sockets (SYS-IPC-001).

4-byte big-endian uint32 length prefix, then UTF-8 JSON body.
Maximum message size: 16 MB.
"""
import json
import socket
import struct
from typing import Any

_MAX_MSG = 16 * 1024 * 1024
_HDR = struct.Struct(">I")


def send_msg(sock: socket.socket, obj: Any) -> None:
    """Send a JSON-serialisable object with a 4-byte length prefix."""
    body = json.dumps(obj, separators=(",", ":")).encode()
    if len(body) > _MAX_MSG:
        raise ValueError(f"message too large: {len(body)}")
    sock.sendall(_HDR.pack(len(body)) + body)


def recv_msg(sock: socket.socket) -> Any:
    """Receive one framed message; raises EOFError when the peer closes."""
    hdr = _recv_exactly(sock, 4)
    (length,) = _HDR.unpack(hdr)
    if length > _MAX_MSG:
        raise ValueError(f"message too large: {length}")
    return json.loads(_recv_exactly(sock, length).decode())


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("connection closed")
        buf.extend(chunk)
    return bytes(buf)
