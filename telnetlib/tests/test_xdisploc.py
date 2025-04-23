"""Test XDISPLOC, rfc-1096_."""
# std imports
import asyncio

# local imports
import telnetlib
import telnetlib.stream_writer
from telnetlib.tests.accessories import unused_tcp_port, bind_host

# 3rd party
import pytest


async def test_telnet_server_on_xdisploc(bind_host, unused_tcp_port):
    """Test Server's callback method on_xdisploc()."""
    # given
    from telnetlib.telopt import IAC, WILL, SB, SE, IS, XDISPLOC

    _waiter = asyncio.Future()
    given_xdisploc = "alpha:0"

    class ServerTestXdisploc(telnetlib.TelnetServer):
        def on_xdisploc(self, xdisploc):
            super().on_xdisploc(xdisploc)
            _waiter.set_result(self)

    await telnetlib.create_server(
        protocol_factory=ServerTestXdisploc, host=bind_host, port=unused_tcp_port
    )

    reader, writer = await asyncio.open_connection(host=bind_host, port=unused_tcp_port)

    # exercise,
    writer.write(IAC + WILL + XDISPLOC)
    writer.write(IAC + SB + XDISPLOC + IS + given_xdisploc.encode("ascii") + IAC + SE)

    # verify,
    srv_instance = await asyncio.wait_for(_waiter, 0.5)
    assert srv_instance.get_extra_info("xdisploc") == "alpha:0"


async def test_telnet_client_send_xdisploc(bind_host, unused_tcp_port):
    """Test Client's callback method send_xdisploc()."""
    # given
    _waiter = asyncio.Future()
    given_xdisploc = "alpha"

    class ServerTestXdisploc(telnetlib.TelnetServer):
        def on_xdisploc(self, xdisploc):
            super().on_xdisploc(xdisploc)
            _waiter.set_result(xdisploc)

        def begin_advanced_negotiation(self):
            from telnetlib.telopt import DO, XDISPLOC

            super().begin_advanced_negotiation()
            self.writer.iac(DO, XDISPLOC)

    await telnetlib.create_server(
        protocol_factory=ServerTestXdisploc, host=bind_host, port=unused_tcp_port
    )

    reader, writer = await telnetlib.open_connection(
        host=bind_host,
        port=unused_tcp_port,
        xdisploc=given_xdisploc,
        connect_minwait=0.05,
    )

    recv_xdisploc = await asyncio.wait_for(_waiter, 0.5)
    assert recv_xdisploc == given_xdisploc
