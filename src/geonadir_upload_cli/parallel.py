"""parallel processing function
"""
import logging
import os
import time

import pystac

from .dataset import (create_dataset, paginate_dataset_images,
                      trigger_ortho_processing, upload_images,
                      upload_images_from_collection)
from .util import clickable_link, first_value, original_filename

logger = logging.getLogger(__name__)


def process_thread(
    dataset_id,
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

    # create new dataset if dataset_id not specified
    if not dataset_id:
        payload_data = {
            "dataset_name": dataset_name,
            "is_private": private,
            "is_published": True
        }

        # retrieve metadata from STAC collection if applicable
        if remote_collection_json:
            collection = pystac.Collection.from_file(img_dir)

            # get citation
            citation = collection.extra_fields.get('sci:citation')
            if citation:
                payload_data["data_credits"] = citation

            # get description
            description = ""
            if hasattr(collection, "description"):
                description += collection.description
            else:
                logger.warning(f"No description in {remote_collection_json}")

            # add license to description
            if hasattr(collection, "license"):
                description += "\n\nLicense: "
                description += collection.license
            else:
                logger.warning(f"No license in {remote_collection_json}")
            try:
                license_link = collection.get_single_link("license").get_href()
                if license_link:
                    description += "\n\nLicense href: "
                    description += license_link
            except Exception as exc:
                logger.warning(f"Can't find license href in {remote_collection_json}")
            if description:
                payload_data["description"] = description

        # update metadata if json file specified in command
        if metadata:
            payload_data.update(**metadata)

        # use <> to make url markdown-clickable
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

    logger.info(f"Dataset name: {dataset_name}, dataset ID: {dataset_id}")
    url = f"{base_url}/api/uploadfiles/?page=1&project_id={dataset_id}"

    try:
        if os.path.splitext(img_dir)[1] == ".json":  # upload from STAC collection
            result_df = upload_images_from_collection(
                dataset_name,
                dataset_id,
                img_dir,
                base_url,
                token,
                remote_collection_json,
                max_retry,
                retry_interval,
                timeout
            )
        else:  # upload local images in img_dir
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

    # get all images uploaded in GN dataset
    try:
        logger.info("sleep 15s")
        time.sleep(15)
        image_names = paginate_dataset_images(url, [])
        logger.debug(image_names)
        result_df["Is Image in API?"] = result_df["Image Name"].apply(
            lambda x: any(original_filename(name) in x for name in image_names)  # get original filename from GN image url
        )
        result_df["Image URL"] = result_df["Image Name"].apply(
            lambda x: first_value(name if original_filename(name) in x else None for name in image_names)
        )
    except Exception as exc:
        logger.error(f"Retrieving image status for {dataset_name} failed:\n{str(exc)}")
        return dataset_name, result_df, "paginate_dataset_image_images"

    # trigger orthomosaic processing in GN
    if complete:
        try:
            trigger_ortho_processing(dataset_id, base_url, token)
        except Exception as exc:
            logger.error(f"Triggering ortho processing for {dataset_name} failed:\n{str(exc)}")
            return dataset_name, result_df, "trigger_ortho_processing"

    return dataset_name, result_df, False
