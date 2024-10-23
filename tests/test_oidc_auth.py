from pathlib import Path
from dashboard import oidc_auth


class TestOidcAuth:
    def setup_method(self):
        data = Path(__file__).parent / "data"
        self.public_key = (data / "public-signing-key.pem").read_text()
        self.sample_json_web_token = (data / "mfa-required-jwt").read_text()

    def test_token_verification(self):
        tv = oidc_auth.TokenVerification(
            jws=self.sample_json_web_token.encode(),
            public_key=self.public_key.encode(),
        )
        assert tv.verify, "Could not verify JWS"
