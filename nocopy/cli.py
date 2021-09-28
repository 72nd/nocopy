"""
Nocopy CLI application.
"""

import csv
import io
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import click
from pydantic import BaseModel
from thefuzz import process as fuzz_process
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
    func = click.option(
        "-u",
        "--url",
        type=str,
        required=False,
        help="base URL of the NocoDB API",
        envvar="NOCO_URL",
    )(func)
    func = click.option(
        "-k",
        "--token",
        type=str,
        required=False,
        help="JWT authentication token",
        envvar="NOCO_TOKEN",
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


def fuzzy_query_option(func):
    func = click.option(
        "-q",
        "--query",
        "fuzzy_query",
        type=str,
        help="client side fuzzy query",
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


def where_option(func):
    func = click.option(
        "--where",
        type=str,
        required=False,
        help="complicated where conditions",
    )(func)
    return func


def query_params_option(func):
    func = where_option(func)
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


def table_option(func):
    func = click.option(
        "-t",
        "--table",
        type=str,
        required=True,
        help="select the table",
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


def __load_input(
    input_file: Optional[Path],
    format_option: Optional[str],
) -> Dict[str, Any]:
    format_option = __determine_file_type(input_file, format_option)
    if format_option == "YAML":
        return yaml.load(open(input_file))
    elif format_option == "JSON":
        return json.load(open(input_file))
    elif format_option == "CSV":
        return __load_csv(input_file)


def __get_client(
    config_file: Path,
    url: str,
    table: str,
    token: str,
) -> Client:
    config = __check_get_config(config_file, url, token)
    return Client(
        build_url(config.base_url, table),
        config.auth_token,
    )


def __get_csv(data: Dict[str, Any], only_header: bool = False) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=data[0].keys(),
        quotechar='"',
    )
    writer.writeheader()
    if not only_header:
        for entry in data:
            writer.writerow(entry)
    return buffer.getvalue()


def __write_output(
    output_file: Optional[Path],
    format_option: Optional[str],
    data: List[Dict[str, Any]],
    only_header: bool = False,
):
    format_option = __determine_file_type(output_file, format_option)
    if format_option == "YAML":
        rsl = yaml.dump(data)
    elif format_option == "JSON":
        rsl = json.dumps(data)
    elif format_option == "CSV":
        rsl = __get_csv(data, only_header=only_header)

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
@where_option
@table_option
def count(
    config_file: Path,
    where: Optional[str],
    url: str,
    table: str,
    token: str,
):
    """Count the records in a table."""
    client = __get_client(config_file, url, table, token)
    print(client.count(where=where))


@click.command()
@config_option
@format_option
@input_option
@table_option
def push(
    config_file: Path,
    file_format: Optional[str],
    input_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Upload the content of a JSON/CSV file to NocoDB."""
    client = __get_client(config_file, url, table, token)
    data = __load_input(input_file, file_format)

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
@fuzzy_query_option
@output_option
@query_params_option
@table_option
def pull(
    config_file: Path,
    file_format: Optional[str],
    output_file: Path,
    where: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
    sort: Optional[str],
    fields: Optional[str],
    fields1: Optional[str],
    fuzzy_query: Optional[str],
    url: str,
    table: str,
    token: str,
):
    """Pull the records from a NocoDB instance."""
    client = __get_client(config_file, url, table, token)
    data = client.list(
        where=where,
        limit=limit,
        offset=offset,
        sort=sort,
        fields=fields,
        fields1=fields1,
        as_dict=True,
    )
    if fuzzy_query is not None:
        fuzz = fuzz_process.extractBests(fuzzy_query, data, score_cutoff=50)
        data = []
        for rsl in fuzz:
            data.append(rsl[0])
    __write_output(output_file, file_format, data)


@click.command()
@config_option
@table_option
def purge(
    config_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Delete the all content of a table."""
    client = __get_client(config_file, url, table, token)

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
@format_option
@output_option
@table_option
def template(
    config_file: Path,
    file_format: Optional[str],
    output_file: Optional[Path],
    url: str,
    table: str,
    token: str,
):
    """Generate a empty template for a specified table."""
    client = __get_client(config_file, url, table, token)
    data = client.list()[0]
    for key in data:
        data[key] = None
    __write_output(output_file, file_format, [data], only_header=True)


@click.command()
@config_option
@input_option
@table_option
def update(
    config_file: Path,
    input_file: Path,
    url: str,
    table: str,
    token: str,
):
    """Update records."""
    client = __get_client(config_file, url, table, token)
    data = __load_csv(input_file)
    client.bulk_update(data)


cli.add_command(count)
cli.add_command(push)
cli.add_command(init)
cli.add_command(pull)
cli.add_command(purge)
cli.add_command(template)
cli.add_command(update)


if __name__ == "__main__":
    cli()
