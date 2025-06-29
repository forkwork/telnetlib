"""Test the server's shell(reader, writer) callback."""
# std imports
import asyncio
import time

# local imports
import telnetlib
import telnetlib.stream_writer
from telnetlib.tests.accessories import unused_tcp_port, bind_host

# 3rd party
import pytest


async def test_telnet_server_default_timeout(bind_host, unused_tcp_port):
    """Test callback on_timeout() as coroutine of create_server()."""
    from telnetlib.telopt import IAC, WONT, TTYPE

    # given,
    _waiter = asyncio.Future()
    given_timeout = 19.29

    await telnetlib.create_server(
        _waiter_connected=_waiter,
        host=bind_host,
        port=unused_tcp_port,
        timeout=given_timeout,
    )

    reader, writer = await asyncio.open_connection(host=bind_host, port=unused_tcp_port)

    writer.write(IAC + WONT + TTYPE)

    server = await asyncio.wait_for(_waiter, 0.5)
    assert server.get_extra_info("timeout") == given_timeout

    # exercise, calling set_timeout remains the default given_value.
    server.set_timeout()
    assert server.get_extra_info("timeout") == given_timeout


async def test_telnet_server_set_timeout(bind_host, unused_tcp_port):
    """Test callback on_timeout() as coroutine of create_server()."""
    from telnetlib.telopt import IAC, WONT, TTYPE

    # given,
    _waiter = asyncio.Future()

    # exercise,
    await telnetlib.create_server(
        _waiter_connected=_waiter, host=bind_host, port=unused_tcp_port
    )

    reader, writer = await asyncio.open_connection(host=bind_host, port=unused_tcp_port)

    writer.write(IAC + WONT + TTYPE)

    server = await asyncio.wait_for(_waiter, 0.5)
    for value in (19.29, 0):
        server.set_timeout(value)
        assert server.get_extra_info("timeout") == value

    # calling with no arguments does nothing, only resets
    # the timer. value remains the last-most value from
    # previous loop
    server.set_timeout()
    assert server.get_extra_info("timeout") == 0


async def test_telnet_server_waitfor_timeout(bind_host, unused_tcp_port):
    """Test callback on_timeout() as coroutine of create_server()."""
    from telnetlib.telopt import IAC, DO, WONT, TTYPE

    # given,
    expected_output = IAC + DO + TTYPE + b"\r\nTimeout.\r\n"

    await telnetlib.create_server(host=bind_host, port=unused_tcp_port, timeout=0.050)

    reader, writer = await asyncio.open_connection(host=bind_host, port=unused_tcp_port)

    writer.write(IAC + WONT + TTYPE)

    stime = time.time()
    output = await asyncio.wait_for(reader.read(), 0.5)
    elapsed = time.time() - stime
    assert 0.050 <= round(elapsed, 3) <= 0.100
    assert output == expected_output
