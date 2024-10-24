from pathlib import Path
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
from josepy.jwk import JWK
from josepy.jws import JWS
from josepy.jwa import ES256
import pytest
from dashboard import oidc_auth


class TestValidOidcAuth:
    def setup_method(self):
        data = Path(__file__).parent / "data"
        self.public_key = (data / "public-signing-key.pem").read_text()
        self.sample_json_web_token = (data / "mfa-required-jwt").read_text()

    def test_token_verification(self):
        tv = oidc_auth.TokenVerification(
            jws=self.sample_json_web_token.encode(),
            public_key=self.public_key.encode(),
        )
        assert tv.signed(), "Could not verify JWS"


class TestInvalidOidcAuth:
    def setup_method(self):
        keypair = ec.generate_private_key(ec.SECP256R1())
        self.private_key = JWK.load(
            keypair.private_bytes(
                Encoding.PEM,
                PrivateFormat.PKCS8,
                NoEncryption(),
            )
        )
        self.public_key = keypair.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    def test_invalid_json_payload(self):
        jws = JWS.sign(
            protect={"alg"},
            payload=b"this isn't valid json",
            key=self.private_key,
            alg=ES256,
        )
        with pytest.raises(oidc_auth.TokenError):
            oidc_auth.TokenVerification(jws.to_compact(), self.public_key)

    def test_empty_json_body(self):
        jws = JWS.sign(
            alg=ES256,
            key=self.private_key,
            payload=json.dumps({}).encode("utf-8"),
            protect={"alg"},
        ).to_compact()
        tv = oidc_auth.TokenVerification(jws, self.public_key)
        assert tv.signed(), "should have been signed"
        # These don't super matter a whole lot, just checking that we don't
        # accidentally throw assertions.
        assert tv.error_code is None
        assert tv.error_message() is None

    def test_known_error_code(self):
        for error_code in oidc_auth.KNOWN_ERROR_CODES:
            jws = JWS.sign(
                alg=ES256,
                key=self.private_key,
                payload=json.dumps(
                    {
                        "code": error_code,
                    }
                ).encode("utf-8"),
                protect={"alg"},
            ).to_compact()
            tv = oidc_auth.TokenVerification(jws, self.public_key)
            assert tv.error_message() is not None, f"couldn't generate message for {error_code}"
