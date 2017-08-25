import credstash
import os


def get_secret(secret_name, context):
    """Fetch secret from environment or credstash."""
    secret = os.getenv(secret_name, None)

    if secret is None:
        secret = credstash.getSecret(
            name=secret_name,
            context=context,
            region="us-east-1"
        )
    return secret
