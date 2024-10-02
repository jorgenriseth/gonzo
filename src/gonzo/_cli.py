# ruff: disable=F401
from pathlib import Path

import click


@click.group()
def cli():
    pass


@cli.command()
@click.option("--SE", type=Path, required=True, help="Path to SpinEcho-image")
@click.option(
    "--IR", type=Path, required=True, help="Path to InversionRecovery real image"
)  # noqa: F401
@click.option(
    "--meta",
    type=Path,
    required=True,
    help="Path to mixed.json file with TR, TI and TE",
)
@click.option("--output", type=Path, required=True, help="Output path")
@click.option(
    "--postprocessed", type=Path, required=True, help="Path to postprocessed output"
)
def T1map_mixed(SE: Path, IR: Path, meta: Path, output: Path, postprocessed: Path):
    from gonzo.estimate_mixed_t1maps import main as mixed_t1map

    mixed_t1map(SE, IR, meta, output, postprocessed)


if __name__ == "__main__":
    cli()
