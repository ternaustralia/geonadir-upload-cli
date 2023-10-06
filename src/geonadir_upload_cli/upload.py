import concurrent.futures
import json
import logging
import os
import tempfile
from datetime import datetime

import pystac
import requests

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
    catalog_url = kwargs.get("item")
    with tempfile.TemporaryDirectory() as tmpdir:
        collections_list = []
        for collection_url in really_get_all_collections(catalog_url, tmpdir.name):
            collections_list.append(("collection_title", collection_url))
        kwargs["item"] = collections_list
        upload_from_collection(**kwargs)
        logger.info(f"cleanup {tmpdir.name}")


def normal_upload(**kwargs):
    base_url = kwargs.get("base_url")
    token = kwargs.get("token")
    item = kwargs.get("item")
    private = kwargs.get("private")
    dry_run = kwargs.get("dry_run")
    metadata_json = kwargs.get("metadata")
    output_dir = kwargs.get("output_folder")
    complete = kwargs.get("complete")

    if dry_run:
        logger.info("---------------------dry run---------------------")
        logger.info(f"base_url: {base_url}")
        logger.info(f"token: {token}")
        logger.info(f"metadata: {metadata_json}")
        logger.info(f"private: {private}")
        logger.info(f"complete: {complete}")
        for count, i in enumerate(item):
            logger.info(f"--item {count + 1}:")
            dataset_name, image_location = i
            dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
            if not dataset_name:
                logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                dataset_name = "untitled"
            logger.info(f"dataset name: {dataset_name}")
            logger.info(f"image location: {image_location}")
        if output_dir:
            logger.info(f"output file: {os.path.join(output_dir, f'{dataset_name}.csv')}")
        else:
            logger.info("no output csv file")

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
            (dataset_name, image_location, base_url, token, private, meta, complete, None)
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


def upload_from_collection(**kwargs):
    base_url = kwargs.get("base_url")
    token = kwargs.get("token")
    item = kwargs.get("item")
    private = kwargs.get("private")
    dry_run = kwargs.get("dry_run")
    metadata_json = kwargs.get("metadata")
    output_dir = kwargs.get("output_folder")
    complete = kwargs.get("complete")
    exclude = kwargs.get("exclude", None)

    cb, ca, ub, ua = generate_four_timestamps(**kwargs)

    tmpdirs = []
    uploads = []

    if dry_run:
        logger.info("---------------------dry run---------------------")
        logger.info(f"base_url: {base_url}")
        logger.info(f"token: {token}")
        logger.info(f"metadata: {metadata_json}")
        logger.info(f"private: {private}")
        logger.info(f"complete: {complete}")
        if exclude:
            logger.info(f"excluding keywords: {str(exclude)}")
        for count, i in enumerate(item):
            dataset_name, image_location = i
            dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
            remote_collection_json = image_location
            logger.info("")
            logger.info(f"--item {count + 1}:")
            logger.info(f"collection url: {image_location}")
            tmpdir = tempfile.TemporaryDirectory()
            tmpdirs.append(tmpdir)
            success = download_to_dir(image_location, tmpdir.name)
            if not success:
                continue
            title = deal_with_collection(image_location, exclude, cb, ca, ub, ua)
            if not title:
                continue
            if dataset_name == "collection_title":
                dataset_name = title
            uploads.append(dataset_name)
            logger.info(f"dataset name: {dataset_name}")
            if output_dir:
                logger.info(f"output file: {os.path.join(output_dir, f'{dataset_name}.csv')}")
            else:
                logger.info("no output csv file")

        logger.info("")
        logger.info("---------------Datasets to be uploaded---------------")
        for dataset in uploads:
            logger.info(dataset)
        logger.info("-----------------------------------------------------")
        logger.info("")

        logger.info(f"cleanup {', '.join([i.name for i in tmpdirs])}")
        for i in tmpdirs:
            i.cleanup()
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
        remote_collection_json = image_location
        logger.info(f"retreiving collection.json from {remote_collection_json}")
        tmpdir = tempfile.TemporaryDirectory()
        tmpdirs.append(tmpdir)
        success = download_to_dir(image_location, tmpdir.name)
        if not success:
            continue
        title = deal_with_collection(image_location, exclude, cb, ca, ub, ua)
        if not title:
            continue
        if dataset_name == "collection_title":
            dataset_name = title
        logger.info(f"Dataset name: {dataset_name}")
        meta = None
        if metadata_json:
            meta = metadata.get(dataset_name, None)
            if meta:
                logger.info(f"Metadata specified for dataset {dataset_name} in {metadata_json}")

        dataset_details.append(
            (dataset_name, image_location, base_url, token, private, meta, complete, remote_collection_json)
        )
    if complete:
        logger.info("Orthomosaic will be triggered after uploading.")
    num_threads = len(dataset_details) if len(dataset_details) <= 5 else 5
    if not num_threads:
        logger.error("No dataset to upload.")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(process_thread, *params) for params in dataset_details]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            for dataset_name, df, error in results:
                if error:
                    logger.warning(f"{dataset_name} uploading failed when {error}")
                else:
                    logger.info(f"{dataset_name} uploading success")
                if output_dir:
                    if df:
                        df.to_csv(f"{os.path.join(output_dir, dataset_name)}.csv", index=False)
                        if error:
                            logger.warning(f"(probably incomplete) output file: {os.path.join(output_dir, dataset_name)}.csv")
                        else:
                            logger.info(f"output file: {os.path.join(output_dir, dataset_name)}.csv")
                    else:
                        logger.warning(f"output file for {dataset_name} not applicable")
                else:
                    logger.info(f"no output csv file for {dataset_name}")

    logger.info(f"cleanup {', '.join([i.name for i in tmpdirs])}")
    for i in tmpdirs:
        i.cleanup()


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


def deal_with_collection(collection_location, exclude, cb, ca, ub, ua):
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
