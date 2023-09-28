import concurrent.futures
import json
import logging
import os
import pystac

from .parallel import process_thread
from .stac import really_get_all_collections

LEGAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"

logger = logging.getLogger(__name__)
env = os.environ.get("DEPLOYMENT_ENV", "prod")
log_level = logging.INFO
if env != "prod":
    log_level = logging.DEBUG
logging.basicConfig(level=log_level)


def upload_from_catalog(**kwargs):
    catalog_file = kwargs.get("item")
    catalog = pystac.Catalog.from_file(catalog_file)
    collections_list = []
    for collection in really_get_all_collections(catalog):
        collections_list.append(("collection_title", collection.self_href))
    kwargs["item"] = collections_list
    normal_upload(**kwargs)


def normal_upload(**kwargs):
    base_url = kwargs.get("base_url")
    token = kwargs.get("token")
    item = kwargs.get("item")
    private = kwargs.get("private")
    dry_run = kwargs.get("dry_run")
    metadata_json = kwargs.get("metadata")
    output_dir = kwargs.get("output_folder")
    complete = kwargs.get("complete")
    root_catalog_url = kwargs.get("root_catalog_url")

    if dry_run:
        logger.info("---------------------dry run---------------------")
        logger.info(f"base_url: {base_url}")
        logger.info(f"token: {token}")
        logger.info(f"metadata: {metadata_json}")
        logger.info(f"private: {private}")
        logger.info(f"complete: {complete}")
        for i in item:
            logger.info("item:")
            dataset_name, image_location = i
            dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
            if os.path.splitext(image_location)[1] == ".json":
                try:
                    collection = pystac.Collection.from_file(image_location)
                    if dataset_name == "collection_title":
                        logger.info("\tuse collection title as Geonadir dataset title.")
                        dataset_name = collection.title
                    if not dataset_name:
                        logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                        dataset_name = "untitled"
                except Exception as exc:
                    logger.error(f"\t{image_location} illegal: {str(exc)}")
                logger.info(f"\troot catalog url: {root_catalog_url}")
                logger.info(f"\tdataset name: {dataset_name}")
                logger.info(f"\tcollection.json location: {image_location}")
            else:
                if not dataset_name:
                    logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                    dataset_name = "untitled"
                logger.info(f"\tdataset name: {dataset_name}")
                logger.info(f"\timage location: {image_location}")
        if output_dir:
            logger.info(f"\toutput file: {os.path.join(output_dir, f'{dataset_name}.csv')}")
        else:
            logger.info("\tno output csv file")
        return

    logger.info(base_url)
    token = "Token " + token
    if metadata_json:
        with open(metadata_json) as f:
            metadata = json.load(f)
        logger.info(f"metadata: {metadata_json}")
    dataset_details = []
    for i in item:
        dataset_name, image_location = i
        dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
        if os.path.splitext(image_location)[1] == ".json":
            try:
                collection = pystac.Collection.from_file(image_location)
                if dataset_name == "collection_title":
                    logger.info("Use collection title as Geonadir dataset title.")
                    dataset_name = collection.title
                if not dataset_name:
                    logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                    dataset_name = "untitled"
            except Exception as exc:
                logger.error(f"{image_location} illegal: {str(exc)}")
            logger.info(f"Root catalog url: {root_catalog_url}")
            logger.info(f"Dataset name: {dataset_name}")
            logger.info(f"collection.json location: {image_location}")
        else:
            if not dataset_name:
                logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                dataset_name = "untitled"
            logger.info(f"Dataset name: {dataset_name}")
            logger.info(f"Images location: {image_location}")
        meta = None
        if metadata_json:
            meta = metadata.get(dataset_name, None)
            if meta:
                logger.info(f"Metadata specified for dataset {dataset_name} in {metadata_json}")

        dataset_details.append(
            (dataset_name, image_location, base_url, token, private, meta, complete, root_catalog_url)
        )
    if complete:
        logger.info("Orthomosaic will be triggered after uploading.")
    num_threads = len(dataset_details) if len(dataset_details) <= 5 else 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(process_thread, *params) for params in dataset_details]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        if output_dir:
            for dataset_name, df in results:
                df.to_csv(f"{os.path.join(output_dir, dataset_name)}.csv", index=False)
                logger.info(f"output file: {os.path.join(output_dir, dataset_name)}.csv")
        else:
            logger.info("no output csv file")
