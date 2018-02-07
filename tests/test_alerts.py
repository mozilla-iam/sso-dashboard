from boto3 import Session
from moto import mock_dynamodb2

from dashboard.models import alert


class TestAlerts(object):
    def test_delegate_object_init(self):
        a = alert.Alert()
        assert a.alert_table_name == 'sso-dashboard-alert'
        assert a is not None

    def test_create_alert_id(self):
        a = alert.Alert()
        id = a._create_alert_id()
        assert id is id

    @mock_dynamodb2
    def test_create_alert(self):
        session = Session()
        # Get the service resource
        dynamodb = session.resource('dynamodb')
        dynamodb.create_table(
            TableName='sso-dashboard-alert1',
            KeySchema=[
                {
                    'AttributeName': 'alert_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'alert_id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        self.table = dynamodb.Table('sso-dashboard-alert1')
        self.table.meta.client.get_waiter('table_exists').wait(TableName='sso-dashboard-alert1')

        a = alert.Alert()
        a.dynamodb = self.table

        alert_dict = {
            'user_id': 'bob|ad|123456',
            'message': 'foo',
            'severity': 'HIGH'
        }
        #
        res = a.create(alert_dict=alert_dict)
        sample_alert_id = res['Attributes']['alert_id']

        assert res['ResponseMetadata']['HTTPStatusCode'] == 200

        res = a.find('bob|ad|123456')
        assert len(res) is 1

        updated_alert_dict = {
            'user_id': 'bob|ad|123456',
            'message': 'foo',
            'severity': 'MEDIUM'
        }

        res = a.update(alert_id=sample_alert_id, alert_dict=updated_alert_dict)
        assert res['ResponseMetadata']['HTTPStatusCode'] == 200

        res = a.destroy(alert_id=sample_alert_id, user_id='bob|ad|123456')
        assert res['ResponseMetadata']['HTTPStatusCode'] == 200


class TestRules(object):
    def test_object_init(self):
        a = alert.Rules(userinfo=None, request=None)

        assert a is not None


class TestFeedback(object):
    pass