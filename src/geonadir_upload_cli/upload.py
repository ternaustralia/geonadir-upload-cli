import concurrent.futures
import json
import logging
import os

from .parallel import process_thread

LEGAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"

logger = logging.getLogger(__name__)
env = os.environ.get("DEPLOYMENT_ENV", "prod")
log_level = logging.INFO
if env != "prod":
    log_level = logging.DEBUG
logging.basicConfig(level=log_level)


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
            (
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
        if output_dir:
            for dataset_name, df, _ in results:
                if df is not None:
                    df.to_csv(f"{os.path.join(output_dir, dataset_name)}.csv", index=False)
                    logger.info(f"output file: {os.path.join(output_dir, dataset_name)}.csv")
        else:
            logger.info("no output csv file")
