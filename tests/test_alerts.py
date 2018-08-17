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
        assert len(res) is 4

        updated_alert_dict = {
            'user_id': 'bob|ad|123456',
            'message': 'foo',
            'severity': 'MEDIUM'
        }

        res = a.update(alert_id=sample_alert_id, alert_dict=updated_alert_dict)
        assert res['ResponseMetadata']['HTTPStatusCode'] == 200

        res = a.destroy(alert_id=sample_alert_id, user_id='bob|ad|123456')
        assert res['ResponseMetadata']['HTTPStatusCode'] == 200

    @mock_dynamodb2
    def test_alert_purge(self):
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

        client = session.client('dynamodb')
        response = client.update_table(
            TableName='sso-dashboard-alert1',
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': 'user_id-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                }
            ],
        )

        assert response is not None

        self.table = dynamodb.Table('sso-dashboard-alert1')
        self.table.meta.client.get_waiter('table_exists').wait(TableName='sso-dashboard-alert1')

        a = alert.Alert()
        a.dynamodb = self.table

        alert_dict = {
            "alert_code": "416c65727447656f6d6f64656c",
            "alert_id": "1c7c506eb221f6206becb8ef0d96f6",
            "alert_str_json": "foo",
            "date": "2018-08-05",
            "description": "This alert is created based on geo ip information about the last login of a user.",
            "duplicate": True,
            "risk": "high",
            "summary": "Did you recently login from Lewisham, United Kingdom (x.x.x.x)?",
            "url": "https://mana.mozilla.org/wiki/display/SECURITY/Alert%3A+Change+in+Country",
            "url_title": "Get Help",
            "user_id": "ad|Mozilla-LDAP|akrug"
        }

        res = a.create(alert_dict=alert_dict)
        assert res is not None
        assert res['ResponseMetadata']['HTTPStatusCode'] == 200

        res = a.find('ad|Mozilla-LDAP|akrug')

        for this_alert in res.get('visible_alerts'):
            if alert_dict.get('alert_id') == this_alert.get('alert_id'):
                assert 0
            else:
                pass


class TestRules(object):
    def test_object_init(self):
        a = alert.Rules(userinfo=None, request=None)

        assert a is not None


class TestFeedback(object):
    pass
