# std imports
import asyncio
import string

# 3rd party
import pytest

# local
import telnetlib
from telnetlib.tests.accessories import unused_tcp_port, bind_host


def test_reader_instantiation_safety():
    """On instantiation, one of server or client must be specified."""
    # given,
    def fn_encoding(incoming):
        return "def-ENC"

    reader = telnetlib.TelnetReader(limit=1999)

    # exercise,
    result = repr(reader)

    # verify.
    assert result == "<TelnetReader limit=1999 encoding=False>"


def test_reader_with_encoding_instantiation_safety():
    # given,
    def fn_encoding(incoming):
        return "def-ENC"

    expected_result = (
        "<TelnetReaderUnicode encoding='def-ENC' " "limit=1999 buflen=0 eof=False>"
    )

    reader = telnetlib.TelnetReaderUnicode(fn_encoding=fn_encoding, limit=1999)

    # exercise,
    result = repr(reader)

    # verify.
    assert result == expected_result


def test_reader_eof_safety():
    """Check side-effects of feed_eof."""
    # given,
    reader = telnetlib.TelnetReader(limit=1999)
    reader.feed_eof()

    # exercise,
    result = repr(reader)

    # verify.
    assert result == "<TelnetReader eof limit=1999 encoding=False>"


def test_reader_unicode_eof_safety():
    # given,
    def fn_encoding(incoming):
        return "def-ENC"

    expected_result = (
        "<TelnetReaderUnicode encoding='def-ENC' " "limit=65536 buflen=0 eof=True>"
    )

    reader = telnetlib.TelnetReaderUnicode(fn_encoding=fn_encoding)
    reader.feed_eof()

    # exercise,
    result = repr(reader)

    # verify.
    assert result == expected_result


async def test_telnet_reader_using_readline_unicode(bind_host, unused_tcp_port):
    """Ensure strict RFC interpretation of newlines in readline method."""
    # given
    _waiter = asyncio.Future()
    given_expected = {
        "alpha\r\x00": "alpha\r",
        "bravo\r\n": "bravo\r\n",
        "charlie\n": "charlie\n",
        "---\r": "---\r",
        "---\r\n": "---\r\n",
        "\r\x00": "\r",
        "\n": "\n",
        "\r\n": "\r\n",
        "xxxxxxxxxxx": "xxxxxxxxxxx",
    }

    def shell(reader, writer):
        for item in sorted(given_expected):
            writer.write(item)
        writer.close()

    await telnetlib.create_server(
        host=bind_host, port=unused_tcp_port, connect_maxwait=0.05, shell=shell
    )

    client_reader, client_writer = await telnetlib.open_connection(
        host=bind_host, port=unused_tcp_port, connect_minwait=0.05
    )

    # exercise,
    for given, expected in sorted(given_expected.items()):
        result = await asyncio.wait_for(client_reader.readline(), 0.5)

        # verify.
        assert result == expected

    # exercise,
    eof = await asyncio.wait_for(client_reader.read(), 0.5)

    # verify.
    assert eof == ""


async def test_telnet_reader_using_readline_bytes(bind_host, unused_tcp_port):
    """Ensure strict RFC interpretation of newlines in readline method."""
    # given
    _waiter = asyncio.Future()
    given_expected = {
        b"alpha\r\x00": b"alpha\r",
        b"bravo\r\n": b"bravo\r\n",
        b"charlie\n": b"charlie\n",
        b"---\r": b"---\r",
        b"---\r\n": b"---\r\n",
        b"\r\x00": b"\r",
        b"\n": b"\n",
        b"\r\n": b"\r\n",
        b"xxxxxxxxxxx": b"xxxxxxxxxxx",
    }

    def shell(reader, writer):
        for item in sorted(given_expected):
            writer.write(item)
        writer.close()

    await telnetlib.create_server(
        host=bind_host,
        port=unused_tcp_port,
        connect_maxwait=0.05,
        shell=shell,
        encoding=False,
    )

    client_reader, client_writer = await telnetlib.open_connection(
        host=bind_host, port=unused_tcp_port, connect_minwait=0.05, encoding=False
    )

    # exercise,
    for given, expected in sorted(given_expected.items()):
        result = await asyncio.wait_for(client_reader.readline(), 0.5)

        # verify.
        assert result == expected

    # exercise,
    eof = await asyncio.wait_for(client_reader.read(), 0.5)

    # verify.
    assert eof == b""


async def test_telnet_reader_read_exactly_unicode(bind_host, unused_tcp_port):
    """Ensure TelnetReader.readexactly, especially IncompleteReadError."""
    # given
    _waiter = asyncio.Future()
    given = "☭---------"
    given_partial = "💉-"

    def shell(reader, writer):
        writer.write(given)
        writer.write(given_partial)
        writer.close()

    await telnetlib.create_server(
        host=bind_host, port=unused_tcp_port, connect_maxwait=0.05, shell=shell
    )

    client_reader, client_writer = await telnetlib.open_connection(
        host=bind_host, port=unused_tcp_port, connect_minwait=0.05
    )

    # exercise, readexactly # bytes of given
    result = await asyncio.wait_for(client_reader.readexactly(len(given)), 0.5)

    # verify,
    assert result == given

    # exercise, read 1 byte beyond given_partial
    given_readsize = len(given_partial) + 1
    with pytest.raises(asyncio.IncompleteReadError) as exc_info:
        result = await asyncio.wait_for(client_reader.readexactly(given_readsize), 0.5)

    assert exc_info.value.partial == given_partial
    assert exc_info.value.expected == given_readsize


async def test_telnet_reader_read_exactly_bytes(bind_host, unused_tcp_port):
    """Ensure TelnetReader.readexactly, especially IncompleteReadError."""
    # given
    _waiter = asyncio.Future()
    given = string.ascii_letters.encode("ascii")
    given_partial = b"zzz"

    def shell(reader, writer):
        writer.write(given + given_partial)
        writer.close()

    await telnetlib.create_server(
        host=bind_host,
        port=unused_tcp_port,
        connect_maxwait=0.05,
        shell=shell,
        encoding=False,
    )

    client_reader, client_writer = await telnetlib.open_connection(
        host=bind_host, port=unused_tcp_port, connect_minwait=0.05, encoding=False
    )

    # exercise, readexactly # bytes of given
    result = await asyncio.wait_for(client_reader.readexactly(len(given)), 0.5)

    # verify,
    assert result == given

    # exercise, read 1 byte beyond given_partial
    given_readsize = len(given_partial) + 1
    with pytest.raises(asyncio.IncompleteReadError) as exc_info:
        result = await asyncio.wait_for(client_reader.readexactly(given_readsize), 0.5)

    assert exc_info.value.partial == given_partial
    assert exc_info.value.expected == given_readsize


async def test_telnet_reader_read_0(bind_host, unused_tcp_port):
    """Ensure TelnetReader.read(0) returns nothing."""
    # given
    def fn_encoding(incoming):
        return "def-ENC"

    reader = telnetlib.TelnetReaderUnicode(fn_encoding=fn_encoding)

    # exercise
    value = await reader.read(0)

    # verify
    assert value == ""


async def test_telnet_reader_read_beyond_limit_unicode(bind_host, unused_tcp_port):
    """Ensure ability to read(-1) beyond segment sizes of reader._limit."""
    # given
    _waiter = asyncio.Future()

    limit = 10

    def shell(reader, writer):
        assert reader._limit == limit
        given = "x" * (limit + 1)
        writer.write(given)
        writer.close()

    await telnetlib.create_server(
        host=bind_host,
        port=unused_tcp_port,
        connect_maxwait=0.05,
        shell=shell,
        limit=limit,
    )

    client_reader, client_writer = await telnetlib.open_connection(
        host=bind_host, port=unused_tcp_port, connect_minwait=0.05, limit=limit
    )

    assert client_reader._limit == limit
    value = await asyncio.wait_for(client_reader.read(), 0.5)
    assert value == "x" * (limit + 1)


async def test_telnet_reader_read_beyond_limit_bytes(bind_host, unused_tcp_port):
    """Ensure ability to read(-1) beyond segment sizes of reader._limit."""
    # given
    _waiter = asyncio.Future()

    limit = 10

    def shell(reader, writer):
        assert reader._limit == limit
        given = b"x" * (limit + 1)
        writer.write(given)
        writer.close()

    await telnetlib.create_server(
        host=bind_host,
        port=unused_tcp_port,
        connect_maxwait=0.05,
        shell=shell,
        encoding=False,
        limit=limit,
    )

    client_reader, client_writer = await telnetlib.open_connection(
        host=bind_host,
        port=unused_tcp_port,
        connect_minwait=0.05,
        encoding=False,
        limit=limit,
    )

    assert client_reader._limit == limit
    value = await asyncio.wait_for(client_reader.read(), 0.5)
    assert value == b"x" * (limit + 1)
