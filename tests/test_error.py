"""Test to cover signed error message system."""
from dashboard import auth

import os


class ErrorTest(object):
    public_key_file = os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        'data/public-signing-key.pem'
    )

    public_key = open(public_key_file).read()

    sample_jwt_file = os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        'data/public-signing-key.pem'
    )

    sample_json_web_token = open(sample_jwt_file).read()

    tv = auth.tokenVerification(
        public_key=public_key,
        jws=sample_json_web_token
    )

    assert tv is not None
    verification_result = tv.verify
    assert tv.verify is True
