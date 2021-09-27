"""
Nocopy CLI application.
"""

import csv
from pathlib import Path
from typing import Dict, Optional

import click
from pydantic import BaseModel

from nocopy import Client
from nocopy.client import build_url


class Config(BaseModel):
    """Config file."""

    base_url: str
    """Base URL of the NocoDB API."""
    auth_token: str
    """JWT authentication token."""

    @classmethod
    def from_file(cls, path: Path):
        """Reads the `Config` as a JSON to a file."""
        with open(path, "r") as f:
            return cls.parse_raw(f.read())

    def to_file(self, path: Path):
        """writes the `Config` as a JSON to a file."""
        with open(path, "w") as f:
            f.write(self.json())


def config_option(func):
    func = click.option(
        "-c",
        "--config",
        "config_file",
        type=click.Path(
            exists=True,
            path_type=Path,
        ),
        required=False,
        help="path to config file",
    )(func)
    return func


def input_option(func):
    func = click.option(
        "-i",
        "--input",
        "input_file",
        type=click.Path(
            exists=True,
            path_type=Path,
        ),
        required=True,
        help="path to input file",
    )(func)
    return func


def output_option(func):
    func = click.option(
        "-o",
        "--output",
        "output_file",
        type=click.Path(
            path_type=Path,
        ),
        required=True,
        help="path to output file",
    )(func)
    return func


def url_option(func):
    func = click.option(
        "-u",
        "--url",
        type=str,
        required=False,
        help="base URL of the NocoDB API",
        envvar="NOCO_URL",
    )(func)
    return func


def table_option(func):
    func = click.option(
        "-t",
        "--table",
        type=str,
        required=True,
        help="select the table",
    )(func)
    return func

def token_option(func):
    func = click.option(
        "-k",
        "--token",
        type=str,
        required=False,
        help="JWT authentication token",
        envvar="NOCO_TOKEN",
    )(func)
    return func


def __check_get_config(
    config_file: Optional[Path],
    url: Optional[str],
    token: Optional[str],
) -> Config:
    got_config = config_file is not None
    got_url = url is not None or url == ""
    got_token = token is not None or token == ""

    if got_config and (got_url or got_token):
        raise click.BadOptionUsage(
            "use ether a config file _or_ the parameters for --url and --token"
        )
    if got_url ^ got_token:
        raise click.BadOptionUsage(
            "if defined by parameter _both_ --url and --token have to be set"
        )
    if got_url and got_token:
        return Config(url, token)
    if not got_config:
        raise click.BadOptionUsage(
            "connection information missing, use a config file or the "
            "parameters for --url and --token"
        )
    return Config.from_file(config_file)


@click.group()
def cli():
    """CLI tools for NocoDB."""


@click.command("import")
@config_option
@input_option
@url_option
@table_option
@token_option
def import_command(
    config_file: Path,
    input_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Upload the content of a CSV file to NocoDB."""
    config = __check_get_config(config_file, url, token)
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )
    print(client.count())


@click.command()
@config_option
@output_option
@url_option
@table_option
@token_option
def export(
    config_file: Path,
    output_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Download the content of a NocoDB instance."""
    config = __check_get_config(config_file, url, token)
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )
    data = client.list()
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=data[0].keys(),
            quotechar='"',
        )
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)


@click.command()
@config_option
@output_option
@url_option
@token_option
def template(
    config_file: Path,
    output_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Generate a empty CSV template for a table."""
    config = __check_get_config(config_file, url, token)
    print(build_url(config.base_url, table))
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )
    data = client.list()
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=data[0].keys(),
            quotechar='"',
        )
        writer.writeheader()


cli.add_command(import_command)
cli.add_command(export)
cli.add_command(template)


if __name__ == "__main__":
    cli()
