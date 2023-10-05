import logging
import os
import pystac
import requests
import urllib

logger = logging.getLogger(__name__)


def get_filelist_from_collection(collection_path:str, remote_collection_json:str):
    collection = pystac.Collection.from_file(collection_path)
    file_dict = {}
    for name, asset in collection.assets.items():
        # if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif')):
        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            file_dict[name] = urllib.parse.urljoin(remote_collection_json, asset.href)
    return file_dict


def really_get_all_collections(catalog_url:str, local_folder:str):
    # catalog_url = "https://data-test.tern.org.au/uas_raw/catalog.json"
    logger.info(f"getting child collection urls from {catalog_url}")
    r = requests.get(catalog_url)
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
