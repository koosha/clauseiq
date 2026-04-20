from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from app.cli import cli


FIXTURES = Path(__file__).parent / "fixtures"


@patch("app.cli.ingest_contract")
@patch("app.cli.make_client")
@patch("app.cli.make_session_factory")
def test_cli_ingest_single_file(mock_factory, mock_client, mock_ingest, tmp_path):
    """Test CLI ingest with a single file."""
    session = MagicMock()
    mock_factory.return_value = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=session),
            __exit__=MagicMock(return_value=False),
        )
    )
    mock_client.return_value = MagicMock()
    mock_ingest.return_value = "ctr_abc123"

    f = tmp_path / "x.pdf"
    f.write_bytes(b"%PDF-1.4")

    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", str(f)])
    assert result.exit_code == 0
    assert "ctr_abc123" in result.output
    mock_ingest.assert_called_once()


@patch("app.cli.ensure_clauses_index")
@patch("app.cli.make_client")
def test_cli_init_index(mock_client, mock_ensure):
    """Test CLI init-index command."""
    mock_client.return_value = MagicMock()
    runner = CliRunner()
    result = runner.invoke(cli, ["init-index"])
    assert result.exit_code == 0
    assert "ok" in result.output
    mock_ensure.assert_called_once()


@patch("app.cli.ingest_contract")
@patch("app.cli.make_client")
@patch("app.cli.make_session_factory")
def test_cli_ingest_skips_on_value_error(mock_factory, mock_client, mock_ingest, tmp_path):
    """Test CLI ingest skips files that raise ValueError."""
    session = MagicMock()
    mock_factory.return_value = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=session),
            __exit__=MagicMock(return_value=False),
        )
    )
    mock_client.return_value = MagicMock()
    mock_ingest.side_effect = ValueError("already ingested")

    f = tmp_path / "x.pdf"
    f.write_bytes(b"%PDF-1.4")

    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", str(f)])
    assert result.exit_code == 0
    assert "skip" in result.output.lower()
