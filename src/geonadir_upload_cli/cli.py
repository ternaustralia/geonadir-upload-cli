import json
import logging
import os
from importlib.metadata import version

import click

from .dataset import dataset_info, search_datasets
from .upload import normal_upload, upload_from_catalog, upload_from_collection

LEGAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"

logger = logging.getLogger(__name__)
env = os.environ.get("DEPLOYMENT_ENV", "prod")
log_level = logging.INFO
if env != "prod":
    log_level = logging.DEBUG
logging.basicConfig(level=log_level)


def print_version(ctx, param, value):
    # print(ctx.__dict__)
    # print(param.__dict__)
    # print(value)
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'Version: {version("geonadir-upload-cli")}')
    ctx.exit()


@click.group()
@click.option(
    '--version',
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Package version.",
)
def cli():
    pass


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    help="Dry-run.",
)
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.password_option(
    "--token", "-t",
    help="User token for authentication.",
)
@click.option(
    "--private/--public", "-p",
    default=False,
    show_default=True,
    type=bool,
    required=False,
    help="Whether dataset is private.",
)
@click.option(
    "--metadata", "-m",
    type=click.Path(exists=True),
    required=False,
    help="Metadata json file.",
)
@click.option(
    "--output-folder", "-o",
    is_flag=False,
    flag_value=os.getcwd(),
    type=click.Path(exists=True),
    required=False,
    help="Whether output csv is created. Generate output at the specified path. Default is false. If flagged without specifing output folder, default is the current path of your terminal.",
)
@click.option(
    "--item", "-i",
    type=(str, click.Path()),
    required=True,
    multiple=True,
    help="The name of the dataset and the directory of images to be uploaded.",
)
@click.option(
    "--complete", "-c",
    is_flag=True,
    default=False,
    show_default=True,
    type=bool,
    required=False,
    help="Whether post the uploading complete message to trigger the orthomosaic call.",
)
def local_upload(**kwargs):
    normal_upload(**kwargs)


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    help="Dry-run.",
)
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.password_option(
    "--token", "-t",
    help="User token for authentication.",
)
@click.option(
    "--private/--public", "-p",
    default=False,
    show_default=True,
    type=bool,
    required=False,
    help="Whether dataset is private.",
)
@click.option(
    "--metadata", "-m",
    type=click.Path(exists=True),
    required=False,
    help="Metadata json file.",
)
@click.option(
    "--output-folder", "-o",
    is_flag=False,
    flag_value=os.getcwd(),
    type=click.Path(exists=True),
    required=False,
    help="Whether output csv is created. Generate output at the specified path. Default is false. If flagged without specifing output folder, default is the current path of your terminal.",
)
@click.option(
    "--item", "-i",
    type=(str, str),
    required=True,
    multiple=True,
    help="The name of the dataset and the directory of stac collection. \
        Type 'collection_title' for dataset name when uploading from stac collection if you want to use title in collection.json as dataset title, \
        e.g. ... --item collection_title ./collection.json ...",
)
@click.option(
    "--complete", "-c",
    is_flag=True,
    default=False,
    show_default=True,
    type=bool,
    required=False,
    help="Whether post the uploading complete message to trigger the orthomosaic call.",
)
def collection_upload(**kwargs):
    upload_from_collection(**kwargs)


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    help="Dry-run.",
)
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.password_option(
    "--token", "-t",
    help="User token for authentication.",
)
@click.option(
    "--private/--public", "-p",
    default=False,
    show_default=True,
    type=bool,
    required=False,
    help="Whether dataset is private.",
)
@click.option(
    "--metadata", "-m",
    type=click.Path(exists=True),
    required=False,
    help="Metadata json file.",
)
@click.option(
    "--output-folder", "-o",
    is_flag=False,
    flag_value=os.getcwd(),
    type=click.Path(exists=True),
    required=False,
    help="Whether output csv is created. Generate output at the specified path. Default is false. If flagged without specifing output folder, default is the current path of your terminal.",
)
@click.option(
    "--item", "-i",
    type=str,
    required=True,
    help="The directory of catalog.json.",
)
@click.option(
    "--complete", "-c",
    is_flag=True,
    default=False,
    show_default=True,
    type=bool,
    required=False,
    help="Whether post the uploading complete message to trigger the orthomosaic call.",
)
def catalog_upload(**kwargs):
    upload_from_catalog(**kwargs)


@cli.command()
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.argument('search-str')
def search_dataset(**kwargs):
    base_url = kwargs.get("base_url")
    search = kwargs.get("search_str")
    print(json.dumps(search_datasets(search, base_url), indent=4))


@cli.command()
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.argument('project-id')
def get_dataset_info(**kwargs):
    base_url = kwargs.get("base_url")
    project_id = kwargs.get("project_id")
    print(json.dumps(dataset_info(project_id, base_url), indent=4))


if __name__ == "__main__":
    cli()
