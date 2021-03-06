# -*- coding: utf-8 -*-
"""Tests for server initialization and loop logic."""
# Part of Atria MUD Server (https://github.com/whutch/atria)
# :copyright: (c) 2008 - 2016 Will Hutcheson
# :license: MIT (https://github.com/whutch/atria/blob/master/LICENSE.txt)

from multiprocessing import Queue

import pytest

from atria.core.server import CLIENTS, EVENTS, SERVER


def test_boot():

    """Test that we can initiate and boot the server."""

    array = []

    # noinspection PyUnusedLocal
    # This one should not fire, as init is not pre-hookable.
    @EVENTS.hook("server_init", pre=True)
    def _init_pre_hook():
        array.append(0)

    # noinspection PyUnusedLocal
    @EVENTS.hook("server_init")
    def _init_post_hook_1():
        array.append(1)

    # noinspection PyUnusedLocal
    @EVENTS.hook("server_boot")
    def _init_post_hook_2():
        array.append(2)

    SERVER.boot(Queue())
    assert array == [1, 2]
    assert CLIENTS.listening


def test_loop():

    """Test that we can loop through the server."""

    class _DummyException(Exception):
        pass

    # noinspection PyUnusedLocal
    @EVENTS.hook("server_loop")
    def _loop_hook():
        raise _DummyException()

    with pytest.raises(_DummyException):
        SERVER.loop()
