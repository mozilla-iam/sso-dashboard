from dashboard.op import yaml_loader


class TestYamlLoader(object):
    def test_object_init(self):
        a = yaml_loader.Application()
        assert a is not None
