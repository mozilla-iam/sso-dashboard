"""Test to cover signed error message system."""
import os
from dashboard import auth


class ErrorTest(object):
    public_key_file = os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        'data/public-signing-key.pem'
    )

    public_key = open(public_key_file).read()

    sample_json_web_token = """eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJjb2RlIjoiZ2l0aHVicmVxdWlyZW1mYSIsInJlZGlyZWN0X3VyaSI6Imh0dHBzOi8vc3NvLm1vemlsbGEuY29tL3JlZGlyZWN0X3VyaSIsImNsaWVudCI6InNzby5tb3ppbGxhLmNvbSIsImNvbm5lY3Rpb24iOiJnaXRodWIiLCJwcmVmZXJyZWRfY29ubmVjdGlvbl9uYW1lIjoiIiwiaWF0IjoxNTIxMjIxMTY5LCJleHAiOjE1MjEyMjQ3OTl9.gXAxDWof0wkxhTfGoCZ6YsuJhwjGDLy9CSxjdm8peSPSEZtaSx3F9mLpjh0RMCzzBZjgR14CWWRrn-RbiX_FjRzKTHoGT9EgmyysOQpRB7_1Jwv_z_Ji771BNSS4bJMES78Hzyb4PPhoMjla1nu6ob8m2OE26jF7kDAD07k130uQwA-QtWTez5ktpjrbH3wkVp-v7Z06ZwdVhRO512XeExL9cd5wrDj7N7ae0nxEuRCWcF6NYdCIwcFcav1MB8hPnFuaM470Sa4wzFPeNRdBAOYLAgDTfYQhJOcUcmM2l-f1mUcl5feAVbF0IswpOLO7O9IVGhMJnLjHdMYxYddQJ07ZENPaHAJT9X-NcdDOlQh2Fi8XPaVmaSFjvZIGpATScW_9fdrId45bpcLVdkPYM1Rwf2qOkSSwcCRUmH-dzWMwBCHplruuA_O1LDeWxxVkYt2IXT5b8fz60vfEfGmYzo6g1oBpn6pjJCzjQjWWrWIH_RrUOl1lqjpviXmVPCIGyJzYfD7Nwl2d6BaBPMKaKNaBrwsbaxgeO8iyYNirDz74XAije_vk8NFW8Xy_MLGB3ZzPCeZhqBYiRjRlZVi2nonpswyQyV3KfYcPFeuywHf0Y4M9R3O6dXmkH3Fv83WLxphHDPvNMEJ7WwKD8S4tHYfnvxSEicCiGBKlUKbTgIs"""

    tv = auth.tokenVerification(
        public_key = public_key,
        jws = sample_json_web_token
    )

    assert tv is not None

    verification_result = tv.verify

    assert tv.verify is True
