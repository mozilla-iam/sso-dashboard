#!/usr/bin/python
"""Authentication class test."""


from dashboard import s3


def test_object_init():
    af = s3.AppFetcher()
    assert af is not None


def test_last_updated():
    af = s3.AppFetcher()
    last = af.last_update()
    assert last is not None


def test_is_updated():
    af = s3.AppFetcher()
    update = af.is_updated()
    assert update is not None


def test_sync_config_and_images():
    af = s3.AppFetcher()
    af.sync_config_and_images()
    assert 0
