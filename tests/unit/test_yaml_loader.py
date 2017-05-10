from dashboard.op import yaml_loader


def test_yaml_loader():
    app_loader = yaml_loader.Application()
    assert app_loader.apps is not None
