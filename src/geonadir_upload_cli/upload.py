"""main uploading function handling cli request
"""
import concurrent.futures
import json
import logging
import os
import re
import tempfile

from .dataset import dataset_info
from .parallel import process_thread
from .util import (deal_with_collection, download_to_dir,
                   generate_four_timestamps, really_get_all_collections)

logger = logging.getLogger(__name__)
env = os.environ.get("DEPLOYMENT_ENV", "prod")
LOG_LEVEL = logging.INFO
if env != "prod":
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL)


def upload_from_catalog(**kwargs):
    """recursively retrieve all collections and upload dataset from each
    """
    catalog_url = kwargs.get("item")
    with tempfile.TemporaryDirectory() as tmpdir:
        collections_list = []
        try:
            for collection_url in really_get_all_collections(catalog_url, tmpdir):
                collections_list.append(("=", collection_url))
        except Exception as exc:
            logger.error(f"Error when retrieving collections from remote catalog: \n{str(exc)}")
            return
        kwargs["item"] = collections_list
        upload_from_collection(**kwargs)
        logger.info(f"cleanup {tmpdir}")


def normal_upload(**kwargs):
    """upload local images
    """
    base_url = kwargs.get("base_url")
    token = kwargs.get("token")
    item = kwargs.get("item")
    private = kwargs.get("private")
    dry_run = kwargs.get("dry_run")
    metadata_json = kwargs.get("metadata")
    output_dir = kwargs.get("output_folder")
    complete = kwargs.get("complete")
    max_retry = kwargs.get("max_retry")
    retry_interval = kwargs.get("retry_interval")
    timeout = kwargs.get("timeout")
    dataset_id = kwargs.get("dataset_id")
    existing_dataset_name = ""
    if dataset_id:
        result = dataset_info(dataset_id, base_url)
        if result == "Metadata not found":
            raise Exception(f"Dataset id {dataset_id} invalid.")
        logger.info(f"Upload to existing dataset id: {dataset_id}")
        try:
            existing_dataset_name = result.get("project_id", {}).get("project_name", "")
            logger.info(f"Dataset name: {existing_dataset_name}")
        except Exception as exc:
            existing_dataset_name = f"<dataset id: {dataset_id}"

    if dry_run:
        logger.info("---------------------dry run---------------------")
        logger.info(f"base_url: {base_url}")
        logger.info(f"token: {token}")
        logger.info(f"metadata: {metadata_json}")
        logger.info(f"private: {private}")
        logger.info(f"complete: {complete}")
        logger.info(f"max_retry: {max_retry} times")
        logger.info(f"retry_interval: {retry_interval} sec")
        logger.info(f"timeout: {timeout} sec")
        for count, i in enumerate(item):
            logger.info(f"--item {count + 1}:")
            dataset_name, image_location = i
            if not dataset_id:
                dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", dataset_name.replace(" ", "_")).strip("_")
                if not dataset_name:
                    logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                    dataset_name = "untitled"
                logger.info(f"dataset name: {dataset_name}")
            logger.info(f"image location: {image_location}")
        if output_dir:
            logger.info(f"output file: {os.path.join(output_dir, f'{dataset_name}.csv')}")
        else:
            logger.info("no output csv file")
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
        meta = None
        if not dataset_id:
            dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", dataset_name.replace(" ", "_")).strip("_")
            if not dataset_name:
                logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                dataset_name = "untitled"
            logger.info(f"Dataset name: {dataset_name}")
            if metadata_json:
                meta = metadata.get(dataset_name, None)
                if meta:
                    logger.info(f"Metadata specified for dataset {dataset_name} in {metadata_json}")
        logger.info(f"Images location: {image_location}")

        if existing_dataset_name:
            dataset_name = existing_dataset_name
        dataset_details.append(
            (
                dataset_id,
                dataset_name,
                image_location,
                base_url,
                token,
                private,
                meta,
                complete,
                None,
                max_retry,
                retry_interval,
                timeout,
            )
        )
    if complete:
        logger.info("Orthomosaic will be triggered after uploading.")
    num_threads = len(dataset_details) if len(dataset_details) <= 5 else 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(process_thread, *params) for params in dataset_details]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        result_processing(results, output_dir)


def upload_from_collection(**kwargs):
    """upload from valid STAC collection object
    """
    base_url = kwargs.get("base_url")
    token = kwargs.get("token")
    item = kwargs.get("item")
    private = kwargs.get("private")
    dry_run = kwargs.get("dry_run")
    metadata_json = kwargs.get("metadata")
    output_dir = kwargs.get("output_folder")
    complete = kwargs.get("complete")
    exclude = kwargs.get("exclude", None)
    include = kwargs.get("include", None)
    max_retry = kwargs.get("max_retry")
    retry_interval = kwargs.get("retry_interval")
    timeout = kwargs.get("timeout")
    dataset_id = kwargs.get("dataset_id")
    existing_dataset_name = ""
    if dataset_id:
        result = dataset_info(dataset_id, base_url)
        if result == "Metadata not found":
            raise Exception(f"Dataset id {dataset_id} invalid.")
        logger.info(f"Upload to existing dataset id: {dataset_id}")
        try:
            existing_dataset_name = result.get("project_id", {}).get("project_name", "")
            logger.info(f"Dataset name: {existing_dataset_name}")
        except Exception as exc:
            existing_dataset_name = f"<dataset id: {dataset_id}"

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
        logger.info(f"max_retry: {max_retry} times")
        logger.info(f"retry_interval: {retry_interval} sec")
        logger.info(f"timeout: {timeout} sec")
        if exclude:
            logger.info(f"excluding keywords: {str(exclude)}")
        if include:
            logger.info(f"excluding keywords: {str(include)}")
        for count, i in enumerate(item):
            dataset_name, image_location = i
            remote_collection_json = image_location
            logger.info("")
            logger.info(f"--item {count + 1}:")
            logger.info(f"collection url: {image_location}")
            tmpdir = tempfile.TemporaryDirectory()
            tmpdirs.append(tmpdir)
            success = download_to_dir(image_location, tmpdir.name)
            if not success:
                continue
            title = deal_with_collection(image_location, exclude, include, cb, ca, ub, ua)
            if not title:
                continue
            if not dataset_id:
                dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", dataset_name.replace(" ", "_")).strip("_")
                if not dataset_name:
                    dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", title.replace(" ", "_")).strip("_")
                    if not dataset_name:
                        logger.warning(f"No legal character. Dataset named 'untitled_{count}'")
                        dataset_name = f"untitled_{count}"
                logger.info(f"dataset name: {dataset_name}")
                uploads.append(dataset_name)
            else:
                uploads.append(f"<dataset id: {dataset_id}>")
                logger.info(f"Upload to existing dataset id: {dataset_id}")
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
    if not dataset_id:
        if metadata_json:
            with open(metadata_json) as f:
                metadata = json.load(f)
            logger.info(f"metadata: {metadata_json}")
    dataset_details = []
    for count, i in enumerate(item):
        dataset_name, image_location = i
        meta = None
        remote_collection_json = image_location
        logger.info(f"retreiving collection.json from {remote_collection_json}")
        tmpdir = tempfile.TemporaryDirectory()
        tmpdirs.append(tmpdir)
        success = download_to_dir(image_location, tmpdir.name)
        if not success:
            continue
        title = deal_with_collection(image_location, exclude, include, cb, ca, ub, ua)
        if not title:
            continue
        if not dataset_id:
            dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", dataset_name.replace(" ", "_")).strip("_")
            if not dataset_name:
                dataset_name = re.sub(r"[^a-zA-Z0-9-_]+", "", title.replace(" ", "_")).strip("_")
                if not dataset_name:
                    logger.warning(f"No legal character. Dataset named 'untitled_{count}'")
                    dataset_name = f"untitled_{count}"
            logger.info(f"Dataset name: {dataset_name}")
            if metadata_json:
                meta = metadata.get(dataset_name, None)
                if meta:
                    logger.info(f"Metadata specified for dataset {dataset_name} in {metadata_json}")
        else:
            logger.info(f"Upload to existing dataset id: {dataset_id}")

        if existing_dataset_name:
            dataset_name = existing_dataset_name
        dataset_details.append(
            (
                dataset_id,
                dataset_name,
                image_location,
                base_url,
                token,
                private,
                meta,
                complete,
                remote_collection_json,
                max_retry,
                retry_interval,
                timeout,
            )
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
            result_processing(results, output_dir)

    logger.info(f"cleanup {', '.join([i.name for i in tmpdirs])}")
    for i in tmpdirs:
        i.cleanup()


def result_processing(results, output_dir):
    """save uploading result to csv; log warning and error

    Args:
        results (list): uploading results
        output_dir (str): directory of output csv files
    """
    for dataset_name, df, error in results:
        if error:
            logger.warning(f"{dataset_name} uploading failed when {error}")
        else:
            logger.info(f"{dataset_name} uploading success")
        if output_dir:
            if df is not None:
                df.to_csv(f"{os.path.join(output_dir, dataset_name)}.csv", index=False)
                if error:
                    logger.warning(f"(probably incomplete) output file: {os.path.join(output_dir, dataset_name)}.csv")
                else:
                    logger.info(f"output file: {os.path.join(output_dir, dataset_name)}.csv")
            else:
                logger.warning(f"output file for {dataset_name} not applicable")
        else:
            logger.info(f"no output csv file for {dataset_name}")
