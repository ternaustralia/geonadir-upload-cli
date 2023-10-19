import logging
import os
import urllib
from datetime import datetime

import pystac
import requests

logger = logging.getLogger(__name__)

LEGAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"


def get_filelist_from_collection(collection_path:str, remote_collection_json:str):
    collection = pystac.Collection.from_file(collection_path)
    file_dict = {}
    for name, asset in collection.assets.items():
        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif')):
            file_dict[name] = urllib.parse.urljoin(remote_collection_json, asset.href)
    return file_dict


def really_get_all_collections(catalog_url:str, local_folder:str):
    # catalog_url = "https://data-test.tern.org.au/uas_raw/catalog.json"
    logger.info(f"getting child collection urls from {catalog_url}")
    r = requests.get(catalog_url, timeout=60)
    r.raise_for_status()
    catalog_location = os.path.join(local_folder, "catalog.json")
    with open(catalog_location, 'wb') as fd:
        fd.write(r.content)
    catalog = pystac.Catalog.from_file(catalog_location)
    for child_link in catalog.get_child_links():
        href = child_link.href
        if href.endswith("collection.json"):
            yield urllib.parse.urljoin(catalog_url, href)
        if href.endswith("catalog.json"):
            subcat_href = urllib.parse.urljoin(catalog_url, href)
            local_subfolder = urllib.parse.urljoin(catalog_location, href).removesuffix("/catalog.json")
            os.makedirs(local_subfolder, exist_ok=True)
            yield from really_get_all_collections(subcat_href, local_subfolder)


def generate_four_timestamps(**kwargs):
    try:
        created_before = kwargs.get("created_before", "9999-12-31")
        cb = datetime.fromisoformat(created_before)
    except Exception as exc:
        logger.warning(f"create_before = {created_before} is not a legal iso format timestamp.")
        cb = datetime(9999, 12, 31, 0, 0)
    try:
        created_after = kwargs.get("created_after", "0001-01-01")
        ca = datetime.fromisoformat(created_after)
    except Exception as exc:
        logger.warning(f"created_after = {created_after} is not a legal iso format timestamp.")
        ca = datetime(1, 1, 1, 0, 0)
    try:
        updated_before = kwargs.get("updated_before", "9999-12-31")
        ub = datetime.fromisoformat(updated_before)
    except Exception as exc:
        logger.warning(f"create_before = {updated_before} is not a legal iso format timestamp.")
        ub = datetime(9999, 12, 31, 0, 0)
    try:
        updated_after = kwargs.get("updated_after", "0001-01-01")
        ua = datetime.fromisoformat(updated_after)
    except Exception as exc:
        logger.warning(f"created_after = {updated_after} is not a legal iso format timestamp.")
        ua = datetime(1, 1, 1, 0, 0)

    return cb, ca, ub, ua


def download_to_dir(url, directory):
    r = requests.get(url, timeout=60)
    try:
        r.raise_for_status()
        image_location = os.path.join(directory, "collection.json")
        with open(image_location, 'wb') as fd:
            fd.write(r.content)
    except Exception as exc:
        if r.status_code == 401:
            logger.error(f"Authentication failed for downloading {image_location}. See readme for instruction.")
        else:
            logger.error(f"{image_location} doesn't exist or is undownloadable: {str(exc)}")
        return False
    return True


def deal_with_collection(collection_location, exclude, include, cb, ca, ub, ua):
    try:
        collection = pystac.Collection.from_file(collection_location)
        dataset_name = collection.title
        dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
        if not dataset_name:
            logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
            dataset_name = "untitled"
        if exclude:
            excluded = False
            for word in exclude:
                if word.lower() in dataset_name.lower():
                    excluded = True
                    logger.warning(f"Dataset {dataset_name} excluded for containing word {word}")
                    break
            if excluded:
                return False
        if include:
            included = False
            for word in include:
                if word.lower() in dataset_name.lower():
                    included = True
                    break
            if not included:
                logger.warning(f"Dataset {dataset_name} excluded for not containing word(s) from {str(include)}")
                return False
        try:
            summary = collection.summaries
            other = summary.other
            created = datetime.fromisoformat(other.get("created"))
            updated = datetime.fromisoformat(other.get("updated"))
            if created > cb or created < ca:
                logger.warning(f"{dataset_name} created at {created}, not between {ca} and {cb}")
                return False
            if updated > ub or updated < ua:
                logger.warning(f"{dataset_name} updated at {updated}, not between {ua} and {ub}")
                return False
        except Exception as exc:
            logger.warning(f"Can't find legal created/updated timestamp for {dataset_name}:")
            logger.warning(f"\t{str(exc)}")
    except Exception as exc:
        logger.error(f"{collection_location} illegal: {str(exc)}")
        return False
    return dataset_name
