import credstash
import os

def get_secret(secret, context):
    """Fetch secret from credstash, environment, or return None."""
    try:
        res = credstash.getSecret(
            name=secret,
            context=context,
            region="us-east-1"
        )
    except:
        res = os.getenv(secret, None)

    return res