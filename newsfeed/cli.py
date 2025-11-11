"""Command line interface for the newsfeed automation tool."""
from __future__ import annotations

from pathlib import Path
import logging

import typer

from .config import AppConfig, DeliveryContext, load_config
from .digest import render_digest
from .scheduler import run_scheduler
from .service import deliver, gather_articles, resolve_delivery

app = typer.Typer(help="Aggregate RSS feeds and email digests on a schedule.")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


def _load(path: Path) -> AppConfig:
    return load_config(path)


def _context_for(config: AppConfig, delivery_name: str) -> DeliveryContext:
    try:
        return resolve_delivery(config, delivery_name)
    except KeyError as exc:  # pragma: no cover - typer converts to exit
        raise typer.BadParameter(str(exc)) from exc


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(Path("config.yml"), "--config", help="Path to configuration file."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable debug logging."),
) -> None:
    """Store configuration on the context object for reuse by commands."""

    _configure_logging(verbose)
    ctx.obj = {"config_path": config}


def _get_config(ctx: typer.Context) -> AppConfig:
    config_path: Path = ctx.obj["config_path"]
    return _load(config_path)


@app.command()
def preview(ctx: typer.Context, delivery: str = typer.Argument(..., help="Delivery name to preview.")) -> None:
    """Render the digest for a delivery and print it to stdout."""

    config = _get_config(ctx)
    context = _context_for(config, delivery)
    articles = gather_articles(context)
    subject, _, text = render_digest(context, articles)
    typer.echo(f"Subject: {subject}\n")
    typer.echo(text)


@app.command()
def send(ctx: typer.Context, delivery: str = typer.Argument(..., help="Delivery name to send.")) -> None:
    """Send a digest immediately."""

    config = _get_config(ctx)
    context = _context_for(config, delivery)
    count, _ = deliver(context)
    typer.echo(
        f"Sent digest '{delivery}' with {count} articles to {', '.join(context.delivery.recipients)}"
    )


@app.command()
def run(ctx: typer.Context) -> None:
    """Start the scheduler and run until interrupted."""

    config = _get_config(ctx)
    run_scheduler(config)


if __name__ == "__main__":
    app()
