import json
import logging
import os
import time

import pandas as pd
import requests
import tqdm as tq
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)


def create_dataset(payload_data, base_url, token):
    """
    Create a new dataset on the Geonadir API.

    Args:
        payload_data (dict): Payload data for creating the dataset.

    Returns:
        str: Dataset ID.

    Raises:
        requests.exceptions.HTTPError: If there's an error creating the dataset.
    """

    reqUrl = f"{base_url}/api/dataset/"

    headers = {
        "Accept": "*/*",
        "Authorization": token,
        "Content-Type": "multipart/form-data; boundary=kljmyvW1ndjXaOEAg4vPm6RBUqO6MC5A"
    }

    payload = ""
    for key, value in payload_data.items():
        payload += f"--kljmyvW1ndjXaOEAg4vPm6RBUqO6MC5A\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n"
    payload += "--kljmyvW1ndjXaOEAg4vPm6RBUqO6MC5A--\r\n"

    response = requests.post(reqUrl, data=payload, headers=headers, timeout=120)
    response.raise_for_status()

    dataset_id = response.json()["id"]
    return dataset_id


def upload_images(dataset_name, dataset_id, img_dir, base_url, token, max_retry, retry_interval, timeout):
    """
    Upload images from a directory to a dataset.

    Args:
        dataset_name (str): Name of the dataset to upload images to.
        dataset_id (str): ID of the dataset to upload images to.
        img_dir (str): Directory path where the images are located.
        base_url (str): Base url of Geonadir api.
        token (str): User token.
        max_retry (int): Max retry for uploading single image.
        retry_interval (float): Interval between retries.
        retry_interval (float): Timeout limit for uploading single images.

    Returns:
        pd.DataFrame: DataFrame containing upload results for each image.
    """
    file_list = os.listdir(img_dir)
    file_list = [file for file in file_list if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif'))]

    count = 0
    df_list = []

    with tq.tqdm(total=len(file_list), position=0) as pbar:
        for file_path in file_list:

            file_size = os.path.getsize(os.path.join(img_dir, file_path))

            start_time = time.time()

            # with open(os.path.join(img_dir, file_path), "rb") as file:
            param = {
                "base_url":base_url,
                "token":token,
                "dataset_id":dataset_id,
                "file_path":os.path.join(img_dir, file_path),
            }
            try:
                response_code = upload_single_image(param, max_retry, retry_interval, timeout)
            except Exception as exc:
                logger.error(f"Error when uploading {file_path}")
                raise exc

            end_time = time.time()
            upload_time = end_time - start_time
            df = pd.DataFrame(
                {
                    "Project ID": dataset_id,
                    "Dataset Name": dataset_name,
                    "Image Name": file_path,
                    "Response Code": response_code,
                    "Upload Time": upload_time,
                    "Image Size": file_size
                },
                index=[0]
            )
            df_list.append(df)

            count += 1
            pbar.update(1)

    result_df = pd.concat(df_list, ignore_index=True)
    return result_df


def trigger_ortho_processing(dataset_id, base_url, token):
    """trigger orthomosaic processing in GN after uploading completed

    Args:
        dataset_id (str | int): GN dataset id.
        base_url (_type_): Base url of Geonadir api.
        token (str): User token.
    """    
    headers = {
        "authorization": token
    }

    payload = {
        'dataset_id': (None, str(dataset_id)),
        'flag': (None, 'upload_completed'),
    }

    response = requests.post(
        f"{base_url}/api/utility/dataset-actions/",
        headers=headers,
        files=payload,
        timeout=180,
    )
    response.raise_for_status()


def paginate_dataset_image_images(url, image_names):
    """
    Paginate through the dataset images API response to retrieve all image names.

    Args:
        url (str): URL of the API endpoint.
        image_names (list): List to store the image names.

    Returns:
        list: List of image names.
    """
    response = requests.get(url, timeout=60)
    data = response.json()
    results = data["results"]
    for result in results:
        image_name = result["upload_files"]
        # image_name = re.search(r'([^/]+?)(?:_\d+)?\.JPG', image_url).group(1) + ".JPG"
        image_names.append(image_name)
    next_page = data["next"]
    if next_page:
        paginate_dataset_image_images(next_page, image_names)
    return image_names


def search_datasets(search_str, base_url):
    """search GN dataset by name
    sample output:
    [
        {
            "id": 3256,
            "dataset_name": "SASMDD0006"
        },
        {
            "id": 3198,
            "dataset_name": "SASMDD0002"
        }
    ]

    Args:
        search_str (str): keyword searched for in GN dataset name.
        base_url (_type_): Base url of Geonadir api.

    Returns:
        list: list of dataset ids and names.
    """    
    payload = {
        "search": search_str
    }

    response = requests.get(
        f"{base_url}/api/search_datasets",
        params=payload,
        timeout=180,
    )
    return response.json()


def dataset_info(project_id, base_url):
    """show dataset info of given id
    sample output:
    {
        "id": 2863,
        "project_id": {
            "id": 3198,
            "user": "TERN Australia",
            "user_id": 4865,
            "user_image": null,
            "project_institution_name": "",
            "project_name": "SASMDD0002",
            "tags": "",
            "category": [
                "Shrubland"
            ],
            "description": "TERN Landscapes, TERN Surveillance Monitoring, Stenson, M., Sparrow, B. & Lucieer, A. (2022): Drone RGB and Multispectral Imagery from TERN plots across Australia. Version 1. Terrestrial Ecosystem Research Network. (Dataset). https://portal.tern.org.au/metadata/TERN/39de90f5-49e3-4567-917c-cf3e3bc93086 Creative Commons Attribution 4.0 International Licence http://creativecommons.org/licenses/by/4.0",
            "data_captured_by": "",
            "latitude": -34.0123308611111,
            "longitude": 140.591931111111,
            "created_at": "2023-08-28T03:30:41.907924Z",
            "captured_date": "2022-05-19T12:24:21Z",
            "location": "Renmark West, Australia",
            "image_count": 693,
            "data_credits": "",
            "is_private": false,
            "has_ortho": true,
            "has_dsm": true,
            "has_dtm": true,
            "ic_bbox": [
                -34.01593698,
                140.58760077,
                -34.00872474,
                140.59626145
            ],
            "ortho_size": 5071.88,
            "raw_images_size": 15171.659
        },
        "uuid": "b257c851-6ecb-428e-882e-f685b663f9a9",
        "metadata":{
            ...
        }
    }

    Args:
        project_id (str): GN dataset id.
        base_url (str): Base url of Geonadir api.

    Returns:
        dict: dataset metadata.
    """    
    payload = {
        "project_id": project_id
    }

    response = requests.get(
        f"{base_url}/api/metadata/",
        params=payload,
        timeout=180,
    )
    return response.json()


def search_datasets_coord(coord, base_url):
    """find GN datasets in given area
    sample output:
    [
        {
            "id": 2359,
            "latitude": -33.47661578,
            "longitude": 25.34186233
        },
        {
            "id": 2520,
            "latitude": -33.49132739,
            "longitude": 26.81348708
        }
    ]

    Args:
        coord (tuple): bbox in latlon.
        base_url (str): Base url of Geonadir api.

    Returns:
        list: list of dataset ids and latlons.
    """    
    l, r = max(min(coord[0], coord[2]), -180), min(max(coord[0], coord[2]), 180)
    b, t = max(min(coord[1], coord[3]), -90), min(max(coord[1], coord[3]), 90)
    logger.info(f"Querying dataset within ({l}, {b}, {r}, {t})")
    payload = {
        "bbox": f"{coord[0]},{coord[1]},{coord[2]},{coord[3]}"
    }

    response = requests.get(
        f"{base_url}/api/dataset_coords",
        params=payload,
        timeout=180,
    )
    return response.json()


def upload_single_image(param, max_retry=5, retry_interval=10, timeout=60):
    """upload single image to GN in 3 steps:
    1. generate presigned url for GN Amazon S3 storage.
    2. upload image to url generated before.
    3. create image uploaded to storage.

    Args:
        param (dict): all params required for uploading, including base_url, token, dataset id and local file path.
        max_retry (int, optional): max retry. Defaults to 5.
        retry_interval (int, optional): retry interval in second. Defaults to 10.
        timeout (int, optional): timeout for single http request in second. Defaults to 60.

    Raises:
        exc: Exception

    Returns:
        int: http response code for creating image in GN.
    """    
    base_url = param["base_url"]
    token = param["token"]
    dataset_id = param["dataset_id"]
    file_path = param["file_path"]

    try:
        response_code, response_json = generate_presigned_url(dataset_id, base_url, token, file_path, max_retry, retry_interval, timeout)
        response_code = upload_to_amazon(response_json, file_path, max_retry, retry_interval, timeout)
        response_code = create_post_image(response_json, dataset_id, base_url, token, max_retry, retry_interval, timeout)
        return response_code
    except Exception as exc:
        raise exc


def generate_presigned_url(dataset_id, base_url, token, file_path, max_retry=5, retry_interval=10, timeout=60):
    """Step 1: generate presigned url for GN Amazon S3 storage.
    sample return:
    {
        "fields": [
            {
                "key": "privateuploads/images/2717-3173fe88-844a-46bd-9348-f7caceb012f7/100.jpeg",
                "policy": "<omitted>",
                "signature": "<omitted>"
            }
        ],
        "url": "https://geonadir-dev.s3.amazonaws.com/",
        "AWSAccessKeyId": "<omitted>"
    }

    Args:
        dataset_id (str): dataset_id
        base_url (str): base_url
        token (str): token
        file_path (str): file_path

    Returns:
        (int, dict): (status_code, response.json())
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': token,
    }

    json_data = {
        'dataset_id': str(dataset_id),
        'images': [
            os.path.basename(file_path),
        ],
    }
    s = requests.Session()
    retries = Retry(
        total=max_retry,
        backoff_factor=retry_interval,
        raise_on_status=False,
        status_forcelist=list(range(400, 600))
    )
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        r = s.post(
            f'{base_url}/api/generate_presigned_url/',
            headers=headers,
            json=json_data,
            timeout=timeout,
        )
        r.raise_for_status()
        return r.status_code, r.json()
    except Exception as exc:
        if "r" not in locals():
            raise Exception(f"generate_presigned_url invalid: {json.dumps(json_data, indent=4)}.")
        raise Exception(str(exc))


def upload_to_amazon(presigned_info, file_path, max_retry=5, retry_interval=10, timeout=60):
    """Step 2: upload image to url generated before.

    Args:
        presigned_info (dict): key, policy, signature and AWSAccessKeyId for uploading to Amazon.
        file_path (str): local file path.
        max_retry (int, optional): max retry. Defaults to 5.
        retry_interval (int, optional): retry interval. Defaults to 10.
        timeout (int, optional): timeout. Defaults to 60.

    Returns:
        int: http request status code.
    """    
    key = presigned_info["fields"][0]["key"]
    policy = presigned_info["fields"][0]["policy"]
    signature = presigned_info["fields"][0]["signature"]
    AWSAccessKeyId = presigned_info["AWSAccessKeyId"]
    
    with open(file_path, 'rb') as file:
        files = {
            'key': (None, key),
            'AWSAccessKeyId': (None, AWSAccessKeyId),
            'policy': (None, policy),
            'signature': (None, signature),
            'file': file,
        }

        s = requests.Session()
        retries = Retry(
            total=max_retry,
            backoff_factor=retry_interval,
            raise_on_status=False,
            status_forcelist=list(range(400, 600))
        )
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            r = s.post(
                'https://geonadir-prod.s3.amazonaws.com/',
                files=files,
                timeout=timeout,
            )
            r.raise_for_status()
            return r.status_code
        except Exception as exc:
            if "r" not in locals():
                raise Exception(f"https://geonadir-dev.s3.amazonaws.com/ posting invalid: {key}.")
            raise Exception(str(exc))


def create_post_image(presigned_info, dataset_id, base_url, token, max_retry=5, retry_interval=10, timeout=60):
    """Step 3: create image uploaded to storage.

    Args:
        presigned_info (dict): key, policy, signature and AWSAccessKeyId for uploading to Amazon.
        dataset_id (int | str): GN dataset_id.
        base_url (str): GN api base_url.
        token (str): GN user token.
        max_retry (int, optional): max_retry. Defaults to 5.
        retry_interval (int, optional): retry_interval. Defaults to 10.
        timeout (int, optional): timeout. Defaults to 60.

    Returns:
        int: http request status code.
    """    
    key = presigned_info["fields"][0]["key"].removeprefix("privateuploads/")

    headers = {
        'Authorization': token,
    }

    files = {
        'dataset_id': (None, str(dataset_id)),
        'image': (None, key),
    }

    s = requests.Session()
    retries = Retry(
        total=max_retry,
        backoff_factor=retry_interval,
        raise_on_status=False,
        status_forcelist=list(range(400, 600))
    )
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        r = s.post(
            f'{base_url}/api/create_post_image/',
            headers=headers,
            files=files,
            timeout=timeout,
        )
        r.raise_for_status()
        return r.status_code
    except Exception as exc:
        if "r" not in locals():
            raise Exception(f"Url {f'{base_url}/api/create_post_image/'} invalid.")
        raise Exception(str(exc))
