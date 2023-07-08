import botocore
import botocore.session
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

__all__ = ["get_secret"]

client = botocore.session.get_session().create_client("secretsmanager")
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=client)


def get_secret(secret_id: str) -> str:
    """Load Secret from AWS Secret Manager.

    Args:
        secret_id (str): Name of the secret to load

    Returns:
        str: The secret
    """

    return cache.get_secret_string(secret_id)
