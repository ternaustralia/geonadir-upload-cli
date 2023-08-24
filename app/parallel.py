import logging
import os
import time
from datetime import datetime

from .dataset import (create_dataset, paginate_dataset_image_images,
                      upload_images)

logger = logging.getLogger(__name__)


def process_thread(dataset_name, img_dir, base_url, token):
    """
    Process a thread for uploading images to a dataset.

    Args:
        dataset_name (str): Name of the dataset.
        img_dir (str): Directory path where the images are located.

    Returns:
        pd.DataFrame: DataFrame containing upload results for each image.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Get current timestamp
    dataset_name_with_timestamp = f"{dataset_name} - {timestamp}"  # Add timestamp to dataset name

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
        "dataset_name": dataset_name_with_timestamp,
        "is_private": 0,
        "is_published": True
    }

    dataset_id = create_dataset(payload_data, base_url, token)
    # print(f"Uploading https://staging.geonadir.com/image-collection-details/{dataset_id}")
    # print()
    url = f"https://api.geonadir.com/api/uploadfiles/?page=1&project_id={dataset_id}"

    result_df = upload_images(dataset_id, img_dir, base_url, token)
    try:
        logger.info("sleep 15s")
        print("sleep 15s")
        time.sleep(15)
        image_names = paginate_dataset_image_images(url, [])
        print(image_names)
        result_df["Is Image in API?"] = result_df["Image Name"].apply(lambda x: any(extract_original_filename_from_url(name) in x for name in image_names))
        # result_df["Image URL"] = result_df.apply(lambda row: image_urls[row["Image Name"]] if row["Is Image in API?"] else None, axis=1)  # TODO: what is image_urls?
    except Exception as e:
        print(e)
    return result_df


def extract_original_filename_from_url(url):
    # url = 'https://geonadir-prod.s3.amazonaws.com/privateuploads/images/
    # 3151-fce3304f-a253-4e91-acd9-3c2aaf876cd3/DJI_20220519122445_0024_766891.JPG
    # ?AWSAccessKeyId=<key_id>&Signature=<sig>&Expires=1692857952'
    url_name = url.split("?")[0].split("/")[-1]  # DJI_20220519122445_0024_766891.JPG
    basename, ext = os.path.splitext(url_name)
    return "_".join(basename.split("_")[:-1]) + ext  # DJI_20220519122445_0024.JPG
