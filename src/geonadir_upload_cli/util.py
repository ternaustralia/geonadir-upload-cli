"""util functions for STAC objects
"""
import logging
import os
import re
import urllib
from datetime import datetime

import pystac
import requests

logger = logging.getLogger(__name__)


def get_filelist_from_collection(collection_path:str, remote_collection_json:str):
    """get list of all assets from STAC collection file

    Args:
        collection_path (str): local path of downloaded collection.json
        remote_collection_json (str): original url location of valid collection

    Returns:
        dict: asset names and urls
    """
    collection = pystac.Collection.from_file(collection_path)
    file_dict = {}
    for name, asset in collection.assets.items():
        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif')):
            file_dict[name] = urllib.parse.urljoin(remote_collection_json, asset.href)
    return file_dict


def really_get_all_collections(catalog_url:str, local_folder:str):
    """recursively get list of all sub-collections

    Args:
        catalog_url (str): original url location of valid catalog
        local_folder (str): local folder of downloaded catalog.json

    Yields:
        str: url of valid collection
    """
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
    """generate datetimes from input isoformat datetime strings

    Returns:
        datetime, datetime, datetime, datetime: created before/after/updated before/after
    """
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
    """download collection.json

    Args:
        url (str): url of collection
        directory (str): dest folder of downloaded collection.json

    Returns:
        bool: whether successfully downloaded
    """
    image_location = os.path.join(directory, "collection.json")
    r = requests.get(url, timeout=60)
    try:
        r.raise_for_status()
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
    """filter collections based on name and datetime

    Args:
        collection_location (str): local collection.json file
        exclude (str): exclude collection with name containing certain string
        include (str): include collection with name containing certain string
        cb (datetime): exclude collection not created before given datetime
        ca (datetime): exclude collection not created after given datetime
        ub (datetime): exclude collection not updated before given datetime
        ua (datetime): exclude collection not updated after given datetime

    Returns:
        str | bool: dataset name retrieved from collection.json. return False if collection is filtered out.
    """
    try:
        collection = pystac.Collection.from_file(collection_location)
        dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", collection.title.replace(" ", "_")).strip("_")
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


def original_filename(url:str):
    """
    Extract the original file name from Geonadir image url.
    for url = 'https://geonadir-prod.s3.amazonaws.com/privateuploads/images/ \
        3151-fce3304f-a253-4e91-acd9-3c2aaf876cd3/DJI_20220519122445_0024_766891.JPG \
        ?AWSAccessKeyId=<key_id>&Signature=<sig>&Expires=1692857952',
    the original file name is DJI_20220519122445_0024.JPG

    23/10/2023 update: filename in url changed due to uploading mechanism update.

    Args:
        url (str): image url

    Returns:
        name: the name of the original image
    """
    url_name = url.split("?")[0].split("/")[-1]  # DJI_20220519122445_0024_766891.JPG
    # basename, ext = os.path.splitext(url_name)
    # return "_".join(basename.split("_")[:-1]) + ext  # DJI_20220519122445_0024.JPG
    return url_name


def geonadir_filename_trans(filename:str):
    """get transformed filename in GN.

    Step 1: Replace %xx escapes by their single-character equivalent using urllib.parse.unquote
    Step 2: replace all characters with _, except for latin and digit
    Step 3: strip trailing underscores from both sides

    Args:
        filename (str): original filename

    Returns:
        str: transformed filename
    """
    name, ext = os.path.splitext(filename)
    trans_name = re.sub(r"[^a-zA-Z0-9_]+", "_", urllib.parse.unquote(name)).strip("_")
    return trans_name + ext


def first_value(iterable):
    """Extract the first non-None value

    Args:
        iterable (iterable): iterable object

    Returns:
        value: non-None value
    """
    return next((item for item in iterable if item is not None), None)


def clickable_link(text:str):
    """Find urls starting with ftp/http/https/www with at least 3 sections,
    and make them clickable in markdown.
    e.g. https://a.b will be substituted by <https://a.b>

    Args:
        text (str): text

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
