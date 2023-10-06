import concurrent.futures
import json
import logging
import os
import tempfile

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
    tmpdir = tempfile.TemporaryDirectory()
    collections_list = []
    for collection_url in really_get_all_collections(catalog_url, tmpdir.name):
        collections_list.append(("collection_title", collection_url))
    kwargs["item"] = collections_list
    upload_from_collection(**kwargs)
    logger.info(f"cleanup {tmpdir.name}")
    tmpdir.cleanup()


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
        for i in item:
            logger.info("item:")
            dataset_name, image_location = i
            dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
            if not dataset_name:
                logger.warning("No legal characters in dataset name. Named 'untitled' instead.")
                dataset_name = "untitled"
            logger.info(f"\tdataset name: {dataset_name}")
            logger.info(f"\timage location: {image_location}")
        if output_dir:
            logger.info(f"\toutput file: {os.path.join(output_dir, f'{dataset_name}.csv')}")
        else:
            logger.info("\tno output csv file")

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

    tmpdirs = []

    if dry_run:
        logger.info("---------------------dry run---------------------")
        logger.info(f"base_url: {base_url}")
        logger.info(f"token: {token}")
        logger.info(f"metadata: {metadata_json}")
        logger.info(f"private: {private}")
        logger.info(f"complete: {complete}")
        if exclude:
            logger.info(f"excluding keywords: {str(exclude)}")
        for i in item:
            dataset_name, image_location = i
            dataset_name = "".join(x for x in dataset_name.replace(" ", "_") if x in LEGAL_CHARS)
            remote_collection_json = image_location
            logger.info(f"retreiving collection.json from {remote_collection_json}")
            logger.info("item:")
            try:
                r = requests.get(image_location)
                r.raise_for_status()
                tmpdir = tempfile.TemporaryDirectory()
                tmpdirs.append(tmpdir)
                image_location = os.path.join(tmpdir.name, "collection.json")
                with open(image_location, 'wb') as fd:
                    fd.write(r.content)
            except Exception as exc:
                if r.status_code == 401:
                    logger.error(f"Authentication failed for downloading {image_location}. See readme for instruction.")
                else:
                    logger.error(f"{image_location} doesn't exist or is undownloadable: {str(exc)}")
                continue
            try:
                collection = pystac.Collection.from_file(image_location)
                if dataset_name == "collection_title":
                    logger.info("\tuse collection title as Geonadir dataset title.")
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
                            logger.warning(f"\tDataset {dataset_name} excluded for containing word {word}")
                            break
                    if excluded:
                        continue
            except Exception as exc:
                logger.error(f"\t{image_location} illegal: {str(exc)}")
            logger.info(f"\tdataset name: {dataset_name}")
            logger.info(f"\tcollection.json location: {image_location}")
        if output_dir:
            logger.info(f"\toutput file: {os.path.join(output_dir, f'{dataset_name}.csv')}")
        else:
            logger.info("\tno output csv file")

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
        try:
            r = requests.get(image_location)
            r.raise_for_status()
            tmpdir = tempfile.TemporaryDirectory()
            tmpdirs.append(tmpdir)
            image_location = os.path.join(tmpdir.name, "collection.json")
            with open(image_location, 'wb') as fd:
                fd.write(r.content)
        except Exception as exc:
            if r.status_code == 401:
                logger.error(f"Authentication failed for downloading {image_location}. See readme for instruction.")
            else:
                logger.error(f"{image_location} doesn't exist or is undownloadable: {str(exc)}")
            continue
        try:
            collection = pystac.Collection.from_file(image_location)
            if dataset_name == "collection_title":
                logger.info("Use collection title as Geonadir dataset title.")
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
                        logger.warning(f"\tDataset {dataset_name} excluded for containing word {word}")
                        break
                if excluded:
                    continue
        except Exception as exc:
            logger.error(f"{image_location} illegal: {str(exc)}")
            continue
        logger.info(f"Dataset name: {dataset_name}")
        logger.info(f"collection.json location: {image_location}")
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

