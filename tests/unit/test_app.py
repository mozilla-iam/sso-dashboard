#!/usr/bin/python
import os
import pytest
from dashboard import app as sso_dashboard

class TestDashboardRoutes(object):
    def __init__(self):
        self.app = self.create_app()

    def create_app(self):
        sso_dashboard.app.config['TESTING'] = True
        return sso_dashboard.app.test_client()

CLIENT = TestDashboardRoutes()

def test_index():
    result = CLIENT.app.get('/')
    assert b'HelloWorld' in result.data
