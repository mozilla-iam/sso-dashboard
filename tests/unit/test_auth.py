#!/usr/bin/python
"""Authentication class test."""


from dashboard import app as sso_dashboard
from dashboard import auth


def test_object_instantiation():
    """Test that we can new up the object."""
    a = auth.OpenIDConnect()
    assert a is not None
