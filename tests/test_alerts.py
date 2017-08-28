from dashboard.models import alert

class TestAlerts(object):
    def setup(self):
        pass

    def test_delegate_object_init(self):
        a = alert.AlertDelegate()
        assert a.alert_table_name == 'sso-dashboard-alerts'
        assert a is not None

    def test_create_alert_id(self):
        a = alert.AlertDelegate()
        id = a._create_alert_id()
        assert id is str(id)