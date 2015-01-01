# -*- coding: utf-8 -*-
"""Network communication and client management."""
# Part of Atria MUD Server (https://github.com/whutch/atria)
# :copyright: (c) 2008 - 2015 Will Hutcheson
# :license: MIT (https://github.com/whutch/atria/blob/master/LICENSE.txt)

import socket
import sys
from types import MappingProxyType

from ..libs.miniboa import TelnetClient, TelnetServer
from .events import EVENTS
from .logs import get_logger


log = get_logger("net")


class ClientManager:

    """A manager for networking and client communication."""

    def __init__(self):
        """Create a new client manager."""
        self._server = None
        self._address = ""
        self._port = 0

    @property
    def listening(self):
        """Return whether this is listening for new connections or not."""
        return self._server is not None

    @property
    def clients(self):
        """Return a read-only mapping of this manager's clients."""
        return MappingProxyType(self._server.clients
                                if self._server else {})

    @property
    def address(self):
        """Return the address used to bind the listener socket."""
        return self._address

    @property
    def port(self):
        """Return the port used to listen for new connections."""
        return self._port

    def listen(self, address, port, on_connect, on_disconnect):
        """Start a new telnet server to listen for connections.

        This will discard any existing listener server, likely dropping any
        open connections.

        :param str address: The address to bind the listener socket to
        :param int port: The port to listen for new connections on
        :param callable on_connect: A callback for when a client connects
        :param callable on_disconnect: A callback for when a client disconnects
        :returns: None
        :raises TypeError: if on_connect or on_disconnect aren't callable

        """
        if not callable(on_connect):
            raise TypeError("on_connect callback must be callable")
        if not callable(on_disconnect):
            raise TypeError("on_disconnect callback must be callable")
        self._address = address
        self._port = port
        log.info("Binding listener to %s on port %s", address, port)
        self._server = TelnetServer(address=address,
                                    port=port,
                                    timeout=0,
                                    on_connect=on_connect,
                                    on_disconnect=on_disconnect)

    def close(self):
        """Stop the telnet server."""
        log.info("Closing listener from %s on port %s",
                 self.address, self.port)
        self._server.stop()
        self._server = None
        self._address = ""
        self._port = 0

    def poll(self):
        """Poll the telnet server to process any queued IO."""
        if self._server:
            self._server.poll()


# We create a global ClientManager here for convenience, and while the server
# will generally only need one to work with, they are NOT singletons and you
# can make more ClientManager instances if you like.
CLIENTS = ClientManager()


@EVENTS.hook("server_save_state", "clients", pre=True)
def _hook_server_save_state(state, pass_to_pid):
    sockets = {}
    if pass_to_pid is not None:
        for fileno, client in CLIENTS.clients.items():
            if sys.platform == "win32":
                socket_info = client.sock.share(pass_to_pid)
            else:
                socket_info = fileno
            sockets[fileno] = socket_info
    state["clients"] = sockets


# noinspection PyProtectedMember
@EVENTS.hook("server_load_state", "clients")
def _hook_server_load_state(state):
    sockets = state["clients"]
    new_clients = {}
    for fileno, socket_info in sockets.items():
        if sys.platform == "win32":
            new_socket = socket.fromshare(socket_info)
        else:
            new_socket = socket.fromfd(socket_info,
                                       socket.AF_INET,
                                       socket.SOCK_STREAM)
        client = TelnetClient(new_socket, new_socket.getsockname())
        CLIENTS._server.clients[client.fileno] = client
        new_clients[fileno] = client
    # Rewrite the sockets dict in the state so that other modules can
    #  reference the new clients by their old socket fileno.
    state["clients"] = new_clients
