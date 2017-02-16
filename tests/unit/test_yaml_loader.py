from dotenv import load_dotenv, find_dotenv
from dashboard import app as sso_dashboard
from dashboard.op import file

def test_yaml_loader():
    app_loader = file.Application()
    print app_loader.apps
    assert app_loader.apps is not None
