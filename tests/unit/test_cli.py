from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    yield CliRunner()


def test_run_server(cli_runner: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    import spannermc.cli

    run_server_subprocess = MagicMock()
    monkeypatch.setattr(spannermc.cli, "user_management_app", run_server_subprocess)
    result = cli_runner.invoke(spannermc.cli.user_management_app)
    assert result.exit_code == 0
