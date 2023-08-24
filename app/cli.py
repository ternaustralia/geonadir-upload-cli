import logging
import os

import click

from .parallel import process_thread

# BASE_URL = "https://api.geonadir.com"
# TOKEN_STAG = "Token dhf892hfbn9472vg"
# dataset_details = [
#     ('Lan testing','/content/drive/MyDrive/image'),
#     ('Nishon Tandukar Test - DroneMapper-RedRocks-Oblique','/content/drive/Shareddrives/Naxa Photos Sharing (Internal)/Test Data/DroneMapper-RedRocks-Oblique')
# ]


logger = logging.getLogger(__name__)
env = os.environ.get("DEPLOYMENT_ENV", "prod")
log_level = logging.WARNING
if env != "prod":
    log_level = logging.INFO
logging.basicConfig(level=log_level)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--base-url", "-u",
    default="https://api.geonadir.com",
    type=str,
    required=False,
    help="Base url of geonadir api.",
)
@click.password_option(
    help="User token for authentication.",
)
@click.option(
    "--dataset-name", "-n",
    default=0,
    type=str,
    required=True,
    help="The name of the dataset.",
)
@click.option(
    "--image-location", "-l",
    default=0,
    type=str,
    required=True,
    help="The directory of images to be uploaded.",
)
@click.option(
    "--output-csv", "-o",
    default="output.csv",
    type=str,
    required=False,
    help="Output csv file.",
)
def upload_dataset(base_url, password, dataset_name, image_location, output_csv):
    logger.info(base_url)
    token = "Token " + password
    logger.info(f"Dataset name: {dataset_name}")
    logger.info(f"Images location: {image_location}")
    df = process_thread(dataset_name, image_location, base_url, token)
    df.to_csv(output_csv, index=False)
    # dataset_details = [(1,2)]
    # num_threads = len(dataset_details)
    # with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    #     futures = [executor.submit(process_thread, *params) for params in dataset_details]
    #     results = [future.result() for future in concurrent.futures.as_completed(futures)]


if __name__ == "__main__":
    cli()
