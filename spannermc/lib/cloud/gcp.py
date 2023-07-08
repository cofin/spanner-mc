from google.cloud import secretmanager as sm

__all__ = ["get_secret"]


def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """Load Secret from GCP Secret Manager.

    Args:
        project_id (str): _description_
        secret_id (str): _description_
        version_id (str, optional): _description_. Defaults to "latest".

    Returns:
        str: _description_
    """
    client = sm.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
