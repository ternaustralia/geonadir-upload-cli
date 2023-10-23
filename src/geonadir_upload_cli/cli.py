import json
import logging
import os
from importlib.metadata import version

import click

from .dataset import dataset_info, search_datasets, search_datasets_coord
from .upload import normal_upload

LEGAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"

logger = logging.getLogger(__name__)
env = os.environ.get("DEPLOYMENT_ENV", "prod")
log_level = logging.INFO
if env != "prod":
    log_level = logging.DEBUG
logging.basicConfig(level=log_level)


def print_version(ctx, param, value):
    """callback for printing cli tool version
    """    
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
    """main cli call
    """    
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
    type=(str, click.Path(exists=True)),
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
@click.option(
    "--max-retry", "-mr",
    default=5,
    show_default=True,
    type=click.IntRange(0, 20, clamp=True),
    required=False,
    help="Max retry for uploading single image.",
)
@click.option(
    "--timeout", "-to",
    default=60,
    show_default=True,
    type=click.FloatRange(0, 3600, clamp=True),
    required=False,
    help="Timeout second for uploading single image.",
)
@click.option(
    "--retry-interval", "-ri",
    default=10,
    show_default=True,
    type=click.FloatRange(0, 3600, clamp=True),
    required=False,
    help="Retry interval second for uploading single image.",
)
def local_upload(**kwargs):
    """upload local images
    """    
    normal_upload(**kwargs)


@cli.command()
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.option(
    "--output-folder", "-o",
    is_flag=False,
    flag_value=os.getcwd(),
    type=click.Path(exists=True),
    required=False,
    help="Whether output csv is created. Generate output at the specified path. Default is false. If flagged without specifing output folder, default is the current path of your terminal.",
)
@click.argument('search-str')
def search_dataset(**kwargs):
    """search dataset by keyword
    """    
    base_url = kwargs.get("base_url")
    search = kwargs.get("search_str")
    output = kwargs.get("output_folder", None)
    result = search_datasets(search, base_url)
    print(json.dumps(result, indent=4))
    print(len(result), "results.")
    if output:
        path = os.path.join(output, "data.json")
        logger.info(f"result saved as {path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)


@cli.command()
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.argument(
    'coords',
    nargs=4,
    type=float,
)
@click.option(
    "--output-folder", "-o",
    is_flag=False,
    flag_value=os.getcwd(),
    type=click.Path(exists=True),
    required=False,
    help="Whether output csv is created. Generate output at the specified path. Default is false. If flagged without specifing output folder, default is the current path of your terminal.",
)
def range_dataset(**kwargs):
    """search dataset by latlon area
    """    
    base_url = kwargs.get("base_url")
    search = kwargs.get("coords")
    output = kwargs.get("output_folder", None)
    result = search_datasets_coord(search, base_url)
    print(json.dumps(result, indent=4))
    print(len(result), "results.")
    if output:
        path = os.path.join(output, "data.json")
        logger.info(f"result saved as {path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)


@cli.command()
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    show_default=True,
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.option(
    "--output-folder", "-o",
    is_flag=False,
    flag_value=os.getcwd(),
    type=click.Path(exists=True),
    required=False,
    help="Whether output csv is created. Generate output at the specified path. Default is false. If flagged without specifing output folder, default is the current path of your terminal.",
)
@click.argument('project-id')
def get_dataset_info(**kwargs):
    """get metadata of dataset given dataset id
    """    
    base_url = kwargs.get("base_url")
    project_id = kwargs.get("project_id")
    output = kwargs.get("output_folder", None)
    result = dataset_info(project_id, base_url)
    print(json.dumps(result, indent=4))
    if output:
        path = os.path.join(output, "data.json")
        logger.info(f"result saved as {path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    cli()
