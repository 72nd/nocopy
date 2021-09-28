"""
Nocopy CLI application.
"""

import csv
import io
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

import click
from pydantic import BaseModel
import yaml

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


def format_option(func):
    func = click.option(
        "-f",
        "--format",
        "file_format",
        type=click.Choice(["CSV", "JSON", "YAML"], case_sensitive=False),
        help="specify in-/output format",
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
        help="path to output file",
    )(func)
    return func


def query_params_option(func):
    func = click.option(
        "--where",
        type=str,
        required=False,
        help="complicated where conditions",
    )(func)
    func = click.option(
        "--limit",
        type=int,
        required=False,
        help="number of rows to get(SQL limit value)",
    )(func)
    func = click.option(
        "--offset",
        type=int,
        required=False,
        help="offset for pagination(SQL offset value)",
    )(func)
    func = click.option(
        "--sort",
        type=str,
        required=False,
        help="sort by column name, use `-` as prefix for desc. sort",
    )(func)
    func = click.option(
        "--fields",
        type=str,
        required=False,
        help="required column names in result",
    )(func)
    func = click.option(
        "--fields1",
        type=str,
        required=False,
        help="required column names in child result",
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


def __determine_file_type(
    file: Optional[Path],
    format_option: Optional[str]
) -> str:
    if format_option is not None:
        return format_option
    if file is not None:
        if file.suffix.lower() == ".json":
            return "JSON"
        elif file.suffix.lower() == ".csv":
            return "CSV"
        elif file.suffix.lower() == ".yaml" or file.suffix.lower() == ".yml":
            return "YAML"
        else:
            print(f"{file.suffix} is a unknown file type, default to YAML")
    return "YAML"


def __load_csv(input_file: Path) -> Dict[str, Any]:
    with open(input_file) as f:
        data = csv.DictReader(f)
        rsl = []
        for entry in data:
            for field in entry:
                if entry[field] == "":
                    entry[field] = None
            rsl.append(entry)
    return rsl


def __get_csv(data: Dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=data[0].keys(),
        quotechar='"',
    )
    writer.writeheader()
    for entry in data:
        writer.writerow(entry)
    return buffer.getvalue()


def __write_output(
    output_file: Optional[Path],
    format_option: Optional[str],
    data: Dict[str, Any],
):
    format_option = __determine_file_type(output_file, format_option)
    print(format_option)
    if format_option == "YAML":
        rsl = yaml.dump(data)
    elif format_option == "JSON":
        rsl = json.dumps(data)
    elif format_option == "CSV":
        rsl = __get_csv(data)

    if output_file is not None:
        with open(output_file, "w") as f:
            f.write(rsl)
    else:
        print(rsl)


@click.group()
def cli():
    """CLI tools for NocoDB."""


@click.command()
@config_option
@format_option
@input_option
@url_option
@table_option
@token_option
def push(
    config_file: Path,
    input_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Upload the content of a JSON/CSV file to NocoDB."""
    config = __check_get_config(config_file, url, token)
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )
    data = __load_csv(input_file)
    client.add(data)


@click.command()
@output_option
def init(output_file: Path):
    """Generate an empty configuration file."""
    cfg = Config(
        base_url="https:///noco.example.com/nc/project/api/v1/",
        auth_token="A-SECRET-TOKEN-FNORD",
    )
    cfg.to_file(output_file)


@click.command()
@config_option
@format_option
@output_option
@query_params_option
@url_option
@table_option
@token_option
def pull(
    config_file: Path,
    file_format: str,
    output_file: Path,
    where: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
    sort: Optional[str],
    fields: Optional[str],
    fields1: Optional[str],
    url: str,
    table: str,
    token: str,
):
    """Pull the records from a NocoDB instance."""
    config = __check_get_config(config_file, url, token)
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )
    data = client.list(
        where=where,
        limit=limit,
        offset=offset,
        sort=sort,
        fields=fields,
        fields1=fields1,
        as_dict=True,
    )
    __write_output(output_file, file_format, data)


@click.command()
@config_option
@url_option
@table_option
@token_option
def purge(
    config_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Delete the all content of a table."""
    config = __check_get_config(config_file, url, token)
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )

    print(
        f"This will PERMANENTLY delete ALL data in table {table} on {config.base_url}")
    user = input("Is this ok (Y/n): ")
    if user != "Y":
        sys.exit(0)
    # Being extra annoying because it's me...
    user = input(
        "Sure? Think again and then type the name of the table to proceed: "
    )
    if user != table:
        sys.exit(0)
    records = client.list()
    with click.progressbar(
        records,
        label="Purge records...",
        show_pos=True
    ) as bar:
        for record in bar:
            client.delete(record["id"])


@click.command()
@config_option
@output_option
@url_option
@table_option
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


@click.command()
@config_option
@input_option
@url_option
@table_option
@token_option
def update(
    config_file: Path,
    input_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Update records."""
    config = __check_get_config(config_file, url, token)
    client = Client(
        build_url(config.base_url, table),
        config.auth_token,
    )
    data = __load_csv(input_file)
    client.bulk_update(data)


cli.add_command(push)
cli.add_command(init)
cli.add_command(pull)
cli.add_command(purge)
cli.add_command(template)
cli.add_command(update)


if __name__ == "__main__":
    cli()
