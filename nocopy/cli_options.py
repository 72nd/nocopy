"""
Options for the click CLI.
"""

from pathlib import Path

import click


def config(func):
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


def format(func):
    func = click.option(
        "-f",
        "--format",
        "file_format",
        type=click.Choice(["CSV", "JSON", "YAML"], case_sensitive=False),
        help="specify in-/output format",
    )(func)
    return func


def fuzzy_query(func):
    func = click.option(
        "-q",
        "--query",
        "fuzzy_query",
        type=str,
        help="client side fuzzy query",
    )(func)
    return func


def input(func):
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


def output(func):
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


def where(func):
    func = click.option(
        "--where",
        type=str,
        required=False,
        help="complicated where conditions",
    )(func)
    return func


def query_params(func):
    func = where(func)
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


def table(func):
    func = click.option(
        "-t",
        "--table",
        type=str,
        required=True,
        help="select the table",
    )(func)
    return func
