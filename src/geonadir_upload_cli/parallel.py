import logging
import os
import pystac
import time

from .dataset import (create_dataset, paginate_dataset_image_images,
                      trigger_ortho_processing, upload_images,
                      upload_images_from_collection)

logger = logging.getLogger(__name__)


def process_thread(dataset_name, img_dir, base_url, token, private, metadata, complete, root_catalog_url):
    """
    Process a thread for uploading images to a dataset.

    Args:
        dataset_name (str): Name of the dataset to upload images to.
        dataset_id (str): ID of the dataset to upload images to.
        img_dir (str): Directory path where the images are located, or path of collection.json file.
        base_url (str): Base url of Geonadir api.
        token (str): User token.
        complete (str): Whether to trigger orthomosaic processing after finishing uploading.
        metadata (str): Metadata json file directory.

    Returns:
        pd.DataFrame: DataFrame containing upload results for each image.
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
    if os.path.splitext(img_dir)[1] == ".json":
        collection = pystac.Collection.from_file(img_dir)
        citation = collection.extra_fields.get('sci:citation')
        if citation:
            payload_data["description"] = citation

    if metadata:
        payload_data.update(**metadata)

    print(payload_data)

    try:
        dataset_id = create_dataset(payload_data, base_url, token)
    except Exception as exc:
        logger.error(f"Create dataset {dataset_name} failed: {str(exc)}")
    # print(f"Uploading https://staging.geonadir.com/image-collection-details/{dataset_id}")
    # print()
    logger.info(f"Dataset name: {dataset_name}, dataset ID: {dataset_id}")
    url = f"{base_url}/api/uploadfiles/?page=1&project_id={dataset_id}"

    if os.path.splitext(img_dir)[1] == ".json":
        result_df = upload_images_from_collection(dataset_name, dataset_id, img_dir, base_url, token, root_catalog_url)
    else:
        result_df = upload_images(dataset_name, dataset_id, img_dir, base_url, token)

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
        logger.error(f"Retrieving image status for {dataset_name} failed: {str(exc)}")
    if complete:
        try:
            trigger_ortho_processing(dataset_id, base_url, token)
        except Exception as exc:
            logger.error(f"Triggering ortho processing for {dataset_name} failed: {str(exc)}")

    return dataset_name, result_df


def original_filename(url):
    """Extract the original file name from Geonadir image url.
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
