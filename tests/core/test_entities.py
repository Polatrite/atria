# -*- coding: utf-8 -*-
"""Tests for entities."""
# Part of Atria MUD Server (https://github.com/whutch/atria)
# :copyright: (c) 2008 - 2016 Will Hutcheson
# :license: MIT (https://github.com/whutch/atria/blob/master/LICENSE.txt)

import pytest

from atria.core.entities import Entity
from atria.core.pickle import PickleStore


class SomeEntity(Entity):

    """A test subclass of entity."""

    _store = PickleStore("some_entities")
    _uid_code = "S"


@pytest.fixture(scope="module")
def entity():
    """Create an entity for all tests to share."""
    return SomeEntity()


class TestEntities:

    """A collection of tests for entities."""

    def test_entity_create(self, entity):
        """Test that we can create an entity."""
        assert entity

    def test_entity_load_data_integrity(self):
        """Test loading two copies of an entity from a store transaction."""
        another_entity = SomeEntity()
        uid, key = another_entity.uid, another_entity.key
        assert uid and key
        assert uid in SomeEntity._instances
        assert another_entity in SomeEntity._instances.values()
        another_entity.save()
        assert key in SomeEntity._store._transaction
        del another_entity
        # Entity should have been dereferenced and fallen out of instances,
        # an attempt to load it now should fall back to the store transaction.
        assert uid not in SomeEntity._instances.values()
        assert key in SomeEntity._store._transaction
        another_entity = SomeEntity.load(key, default=None)
        assert another_entity and another_entity.uid
        assert another_entity.uid == uid
        del another_entity
        assert uid not in SomeEntity._instances.values()
        another_copy = SomeEntity.load(key, default=None)
        assert another_copy and another_copy.uid
        assert another_copy.uid == uid
