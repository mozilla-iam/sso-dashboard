#!/usr/bin/python
"""Authentication class test."""


from dashboard import auth
from dashboard import config


def test_object_instantiation():
    """Test that we can new up the object."""
    configuration = config.Config()
    a = auth.OpenIDConnect(configuration)
    assert a is not None
