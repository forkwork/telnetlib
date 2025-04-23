#!/usr/bin/env python3
"""
A very simple linemode server shell.
"""
# std
import asyncio
import sys
import pkg_resources

# local
import telnetlib


async def shell(reader, writer):
    from telnetlib import WONT, ECHO

    writer.iac(WONT, ECHO)

    while True:
        writer.write("> ")

        recv = await reader.readline()

        # eof
        if not recv:
            return

        writer.write("\r\n")

        if recv.rstrip() == "bye":
            writer.write("goodbye.\r\n")
            await writer.drain()
            writer.close()

        writer.write("".join(reversed(recv)) + "\r\n")


if __name__ == "__main__":
    kwargs = telnetlib.parse_server_args()
    kwargs["shell"] = shell
    telnetlib.run_server(**kwargs)
    # sys.argv.append('--shell={
    sys.exit(
        pkg_resources.load_entry_point(
            "telnetlib", "console_scripts", "telnetlib-server"
        )()
    )
