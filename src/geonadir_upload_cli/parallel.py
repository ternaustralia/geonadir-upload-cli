import logging
import os
import re
import time

from .dataset import (create_dataset, paginate_dataset_image_images,
                      trigger_ortho_processing, upload_images)

logger = logging.getLogger(__name__)


def process_thread(
        dataset_name,
        img_dir,
        base_url,
        token,
        private,
        metadata,
        complete,
        remote_collection_json,
        max_retry,
        retry_interval,
        timeout
):
    """
    Process a thread for uploading images to a dataset.

    Args:
        dataset_name (str): Name of the dataset to upload images to.
        img_dir (str): Local directory of images or collection.json.
        base_url (str): Base url of Geonadir api.
        token (str): User token.
        private (bool): Whether the dataset is private.
        metadata (str): Metadata json file directory.
        complete (str): Whether to trigger orthomosaic processing after finishing uploading.
        remote_collection_json (str): Remote url of collection.json. Applicable when uploading from collection.
        max_retry (int): Max retry for uploading single image.
        retry_interval (float): Interval between retries.
        timeout (float): Timeout for uploading single image.
    Returns:
        dataset_name (str): Geonadir dataset name.
        result_df (pd.DataFrame): DataFrame containing upload results for each image, or False if error raised before DF generated.
        error (str): At which step the error happened, or False if not applicable.
    """
    # payload_data below can be modified to accomodate metadata information
    # {
    #     "id": 2838,
    #     "user_id": 3514,
    #     "dataset_name": "DroneMapper-RedRocks-Oblique",
    #     "location_name": None,
    #     "category": [],
    #     "tags": "tag1",
    #     "description": "test descriptuon",
    #     "data_captured_by": "nishon1",
    #     "data_credits": "I took this data from a project at my company",
    #     "institution_name": "Naxa Pvt Ltd",
    #     "is_published": True,
    #     "is_private": False
    # }

    payload_data = {
        "dataset_name": dataset_name,
        "is_private": private,
        "is_published": True
    }

    if metadata:
        payload_data.update(**metadata)

    if payload_data.get("description", None):
        payload_data["description"] = clickable_link(payload_data["description"])
    if payload_data.get("data_credits", None):
        payload_data["data_credits"] = clickable_link(payload_data["data_credits"])

    logger.info("\n")
    logger.info(f"Metadata for dataset {dataset_name}:")
    logger.info(str(payload_data))

    try:
        dataset_id = create_dataset(payload_data, base_url, token)
    except Exception as exc:
        logger.error(f"Create dataset {dataset_name} failed:\n{str(exc)}")
        return dataset_name, False, "create_dataset"
    # print(f"Uploading https://staging.geonadir.com/image-collection-details/{dataset_id}")
    # print()
    logger.info(f"Dataset name: {dataset_name}, dataset ID: {dataset_id}")
    url = f"{base_url}/api/uploadfiles/?page=1&project_id={dataset_id}"

    try:
        result_df = upload_images(
            dataset_name,
            dataset_id,
            img_dir,
            base_url,
            token,
            max_retry,
            retry_interval,
            timeout
        )
    except Exception as exc:
        logger.error(f"Uploading images failed:\n{str(exc)}")
        return dataset_name, None, "upload_images"

    try:
        logger.info("sleep 15s")
        time.sleep(15)
        image_names = paginate_dataset_image_images(url, [])
        logger.debug(image_names)
        result_df["Is Image in API?"] = result_df["Image Name"].apply(
            lambda x: any(original_filename(name) in x for name in image_names)
        )
        result_df["Image URL"] = result_df["Image Name"].apply(
            lambda x: first_value(name if original_filename(name) in x else None for name in image_names)
        )
    except Exception as exc:
        logger.error(f"Retrieving image status for {dataset_name} failed:\n{str(exc)}")
        return dataset_name, result_df, "paginate_dataset_image_images"

    if complete:
        try:
            trigger_ortho_processing(dataset_id, base_url, token)
        except Exception as exc:
            logger.error(f"Triggering ortho processing for {dataset_name} failed:\n{str(exc)}")
            return dataset_name, result_df, "trigger_ortho_processing"

    return dataset_name, result_df, False


def original_filename(url):
    """
    Extract the original file name from Geonadir image url.
    for url = 'https://geonadir-prod.s3.amazonaws.com/privateuploads/images/ \
        3151-fce3304f-a253-4e91-acd9-3c2aaf876cd3/DJI_20220519122445_0024_766891.JPG \
        ?AWSAccessKeyId=<key_id>&Signature=<sig>&Expires=1692857952',
    the original file name is DJI_20220519122445_0024.JPG

    Args:
        url (str): image url

    Returns:
        name: the name of the original image
    """
    url_name = url.split("?")[0].split("/")[-1]  # DJI_20220519122445_0024_766891.JPG
    basename, ext = os.path.splitext(url_name)
    return "_".join(basename.split("_")[:-1]) + ext  # DJI_20220519122445_0024.JPG


def first_value(iterable):
    """Extract the first non-None value

    Args:
        iterable (iterable): iterable object

    Returns:
        value: non-None value
    """
    return next((item for item in iterable if item is not None), None)


def clickable_link(text:str):
    """make web urls markdown-clickable in text.

    Args:
        text (str): description/acknowledgement text.

    Returns:
        str: processed text
    """    
    regexp = r'((?:(?:(?:https?|ftp):\/\/)|www)[\w/\-?=%.]+\.[\w/\-&?=%.]+)([^\w/\-&?=%.]|$)'

    def repl(matchobj:re.Match):
        rs = matchobj.group(1).rstrip(".")
        if rs:
            num = len(matchobj.group(1)) - len(rs)
            res = f"<{rs}>{matchobj.group(2)}"
            for _ in range(num):
                res += "."
            return res
        return matchobj.string

    text = re.sub(regexp, repl, text)
    return text
