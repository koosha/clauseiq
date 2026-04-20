from pathlib import Path

import click

from app.db.session import make_session_factory
from app.search.client import make_client
from app.search.index_mapping import ensure_clauses_index
from app.ingest.orchestrator import ingest_contract


@click.group()
def cli() -> None:
    """ClauseIQ CLI."""


@cli.command("init-index")
def init_index_cmd() -> None:
    """Ensure the OpenSearch clauses index exists."""
    client = make_client()
    ensure_clauses_index(client)
    click.echo("ok")


@cli.command("ingest")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def ingest_cmd(path: Path) -> None:
    """Ingest a single contract file or every supported file in a directory."""
    factory = make_session_factory()
    os_client = make_client()

    if path.is_file():
        files = [path]
    else:
        files = sorted(list(path.glob("*.pdf")) + list(path.glob("*.docx")))

    with factory() as session:
        for f in files:
            try:
                cid = ingest_contract(session, os_client, f)
                click.echo(f"ingested {f.name} -> {cid}")
            except ValueError as e:
                click.echo(f"skip {f.name}: {e}", err=True)


if __name__ == "__main__":
    cli()
