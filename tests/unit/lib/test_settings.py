from spannermc.lib import settings


def test_app_slug() -> None:
    """Test app name conversion to slug."""
    settings.spannermc.NAME = "My Application!"
    assert settings.spannermc.slug == "my-application"
