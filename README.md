# geonadir_upload_cli

## About

This package is for uploading datasets to Geonadir. You can use it to upload multiple datasets at one time with metadata specified for any or all of them. This cli tool has other functions e.g. searching for dataset or getting dataset information.

## Setup

After cloning this repo, run the commands below to install this package.

```bash
# create a virtual env before installing if you prefer
(virtualenv env)
(source env/bin/activate)
cd your/repo/directory/geonadir-upload-cli
pip install -e .
```

Another option is to install from PyPi. Visit <https://pypi.org/project/geonadir-upload-cli/> for detail:

```bash
# create a virtual env before installing if you prefer
(virtualenv env)
(source env/bin/activate)
pip install geonadir-upload-cli
```

You can run this cli tool from any location. Add option `--help` for command detail, e.g.

```bash
geonadir-cli --help
geonadir-cli local-upload --help
```

Call below command for showing current version of the package.

```bash
geonadir-cli --version
```

## command details

### upload dataset from local image directory

Usage: `geonadir-cli local-upload [OPTIONS]`

Options:

- `--dry-run`: Show all information of this run without actual running.

- `-u, --base-url`: The base url of geonadir api.

  - Default is <https://api.geonadir.com>.

  - Usually leave default.

- `-t, --token`: The user token for authentication.

  - When not specified in command, there will be a password prompt for it. (recommended for security’s sake)

- `-p, --private / --public`: Whether datasets are private.

  - Default is public.

  - This option is applied to all datasets in a single run. Use metadata if some of the datasets need to be set differently.

- `-m, --metadata`: The path of metadata json file.

  - This option is not required. Only use it when some metadata fields need to be specified manually on the run.

  - The path must exist, otherwise error raised.

- `-o, --output-folder`: Whether output csv is created. Generate output at the specified path.

  - Default is false.

  - If flagged without specifying output folder, default is the current path of your terminal.

  - The path must exist, otherwise error raised.

- `-c, --complete`: Whether to trigger the orthomosaic processing once uploading is finished.

  - Default is false.

  - This option is applied to all datasets in a single run.

- `-i, --item`: The name of the dataset and the directory of images to be uploaded.

  - This is a multiple option. user can upload multiple datasets by e.g.  
`... -i dataset1 path1 -i dataset2 path2 ...`

  - All path(s) must exist, otherwise error raised.

  - Dataset name is processed as follows:

    1. Space in dataset name replaced by "_".

    2. Characters in dataset name removed except for Latins, digits, "-" and "_".

    3. Trailing "_"s removed from both sides

- `-mr, --max-retry`: Max retry attempt for uploading single image.

  - Must be non-negative integer.

  - Default is 5.

- `-ri, --retry-interval`: Interval seconds between retries for uploading single image.

  - Must be non-negative float.

  - Actual interval is `{retry-interval} * (2 ** ({number of total retries} - 1))`

  - Default is 10.

- `-to, --timeout`: Timeout seconds for uploading single image.

  - Must be non-negative float.

  - Default is 60.

- `-d, --dataset-id`: Optional for uploading to existing GN dataset.
Unless you know what you are doing, don't enable this when you are uploading multiple datasets in parallel.

  - Must be non-negative integer.

  - Leave it default or set 0 to upload to new dataset.

  - Error raised if dataset-id is illegal.

  - If id specified, several option will be disabled, e.g., dataset name, metadata, etc.

### upload dataset from single remote STAC collection.json file

This is for uploading all image assets as a GN dataset from single collection. STAC items are not yet supported.

Usage: `geonadir-upload collection-upload [OPTIONS]`

Options:

- `--dry-run`: Show all information of this run without actual running.

- `-u, --base-url`: The base url of geonadir api.

  - Default is <https://api.geonadir.com>.

  - Usually leave default.

- `-t, --token`: The user token for authentication.

  - When not specified in command, there will be a password prompt for it. (recommended for security’s sake)

- `-p, --private / --public`: Whether datasets are private.

  - Default is public.

  - This option is applied to all datasets in a single run. Use metadata if some of the datasets need to be set differently.

- `-m, --metadata`: The path of metadata json file.

  - This option is not required. Only use it when some metadata fields need to be specified manually on the run.

  - The path must exist, otherwise error raised.

- `-o, --output-folder`: Whether output csv is created. Generate output at the specified path.

  - Default is false.

  - If flagged without specifying output folder, default is the current path of your terminal.

  - The path must exist, otherwise error raised.

- `-c, --complete`: Whether to trigger the orthomosaic processing once uploading is finished.

  - Default is false.

  - This option is applied to all datasets in a single run.

- `-i, --item`: The name of the dataset and the url of stac collection.

  - This is a multiple option. User can upload multiple datasets by e.g.  
`... -i dataset1 url1 -i dataset2 url2 ...`

  - Type '=' for dataset name when uploading from stac collection if you want to use title in collection.json as dataset title, e.g.
`... --item = https://url/to/collection.json ...`

  - All path(s) must exist, otherwise error raised.

  - Dataset name is processed as follows:

    1. Space in dataset name replaced by "_".

    2. Characters in dataset name removed except for Latins, digits, "-" and "_".

    3. Trailing "_"s removed from both sides

- `-cb, --created-before`: Only upload collections created before this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

- `-ca, --created-after`: Only upload collections created after this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

- `-ub, --updated-before`: Only upload collections updated before this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

- `-ua, --updated-after`: Only upload collections updated after this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

- `-mr, --max-retry`: Max retry attempt for uploading single image.

  - Must be non-negative integer.

  - Default is 10.

- `-ri, --retry-interval`: Interval seconds between retries for uploading single image.

  - Must be non-negative integer.

  - Actual interval is `{retry-interval} * (2 ** ({number of total retries} - 1))`

  - Default is 30.

- `-to, --timeout`: Timeout seconds for uploading single image.

  - Must be non-negative float.

  - Default is 120.

- `-d, --dataset-id`: Optional for uploading to existing GN dataset.
Unless you know what you are doing, don't enable this when you are uploading multiple datasets in parallel.

  - Must be non-negative integer.

  - Leave it default or set 0 to upload to new dataset.

  - Error raised if dataset-id is illegal.

  - If id specified, several option will be disabled, e.g., dataset name, metadata, etc.

### upload datasets from all collections of STAC catalog

Usage: `geonadir-upload catalog-upload [OPTIONS]`

This command uploads all collections in the specified STAC catalog (not necessarily the root catalog) and all its sub-catalogs if any. Each collection will be uploaded as a Geonadir dataset with dataset name being collection title. One catalog each time. Other options are same as single-datasets uploading.

Options:

- `--dry-run`: Show all information of this run without actual running.

- `-u, --base-url`: The base url of geonadir api.

  - Default is <https://api.geonadir.com>.

  - Usually leave default.

- `-t, --token`: The user token for authentication.

  - When not specified in command, there will be a password prompt for it. (recommended for security’s sake)

- `-p, --private / --public`: Whether datasets are private.

  - Default is public.

  - This option is applied to all datasets in a single run. Use metadata if some of the datasets need to be set differently.

- `-m, --metadata`: The path of metadata json file.

  - This option is not required. Only use it when some metadata fields need to be specified manually on the run.

  - The path must exist, otherwise error raised.

- `-o, --output-folder`: Whether output csv is created. Generate output at the specified path.

  - Default is false.

  - If flagged without specifying output folder, default is the current path of your terminal.

  - The path must exist, otherwise error raised.

- `-c, --complete`: Whether to trigger the orthomosaic processing once uploading is finished.

  - Default is false.

  - This option is applied to all datasets in a single run.

- `-i, --item`: The remote url of the STAC catalog json file.

- `-x, --exclude`: Exclude collections with keyword in title.

  - This is a multiple option. User can specify multiple keywords by e.g.  
`... -x keyword1 -x keyword2 ...`

  - Ignore case.

- `-cb, --created-before`: Only upload collections created before this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

  - If timezone not specified, e.g. `-cb 2023-09-23`, it will automatically adapt to local timezone.

- `-ca, --created-after`: Only upload collections created after this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

  - If timezone not specified, e.g. `-ca 2023-09-23`, it will automatically adapt to local timezone.

- `-ub, --updated-before`: Only upload collections updated before this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

  - If timezone not specified, e.g. `-ub 2023-09-23`, it will automatically adapt to local timezone.

- `-ua, --updated-after`: Only upload collections updated after this timestamp.

  - Must be of [ISO format](https://en.wikipedia.org/wiki/ISO_8601).

  - If timezone not specified, e.g. `-ua 2023-09-23`, it will automatically adapt to local timezone.

- `-mr, --max-retry`: Max retry attempt for uploading single image.

  - Must be non-negative integer.

  - Default is 10.

- `-ri, --retry-interval`: Interval seconds between retries for uploading single image.

  - Must be non-negative integer.

  - Actual interval is `{retry-interval} * (2 ** ({number of total retries} - 1))`

  - Default is 30.

- `-to, --timeout`: Timeout seconds for uploading single image.

  - Must be non-negative float.

  - Default is 120.

## Running

An example of privately uploading `./testimage` as dataset **test1** and `C:\tmp\testimage` as **test2** with metadata file in `./sample_metadata.json` (see next section), generating the output csv files in the current folder, and trigger the orthomosaic process when uploading is finished:

```bash
geonadir-cli local-upload -i test1 testimage -i test2 C:\tmp\testimage -p -m sample_metadata.json -o
```

The metadata specified in the json file will override the global settings, e.g. `is_private`.  

### sample metadata json

Below is an example for specifying some metadata values on the run. In this example, the metadata record will be mapped to uploaded dataset with name being "test1"/"test2", if any.

For uploading from STAC objects (collection or catalog), the key in metadata.json should be equal to the (processed) collection title if dataset name is not manually specified.

Note: The value in designated `metadata.json` will be of highest priority. However, the metadata values from elsewhere (e.g. `collection.json`) won't be overwritten if the relative fields are not specified in `metadata.json`. Therefore, it's ok to only specify some of the fields especially when uploading from collection.

```json
{
    "test1": {
        "tags": ["tag1", "tag2"],
        "description": "test descriptuon",
        "data_captured_by": "lan",
        "data_credits": "credit1",
        "institution_name": "Naxa Pvt Ltd",
        "is_published": true,
        "is_private": true
    },
    "test2": {
        "tags": "tag2",
        "data_captured_by": "lan",
        "data_credits": "credit2",
        "institution_name": "Ndsf"
    }
}
```

### sample output

|   **Dataset Name**   | **Project ID** |        **Image Name**       | **Response Code** |  **Upload Time**  | **Image Size** | **Is Image in API?** | **Image URL** |
|:--------------------:|:--------------:|:---------------------------:|:-----------------:|:-----------------:|----------------|----------------------|---------------|
|         test1        |      3174      | DJI_20220519122501_0041.JPG |        201        | 2.770872116088867 |    22500587    |         True         |  (image_url)  |
|         ...          |      ...       |             ...             |        ...        |        ...        |      ...       |         ...          |      ...      |

### .netrc setting for uploading dataset from stac catalog

before uploading from stac catalog, it is critical to set up `.netrc` file for http requests authentication. Put this file in root folder with content like this or add this to existing `.netrc` file:

```text
machine <host url>
login <username>
password <password>
```

#### example: .netrc configuration for TERN data server

1. Create an API key if you don't have one yet:
    1. Sign in [TERN Account](https://account.tern.org.au/).
    2. Click on **Create API key** on the left.
    3. Type a name for your API key and click on **Request API Key**.
    4. Memorize the key.
2. Once you have it, add content below to `<root folder>/.netrc` (or create one if it's not there).

    **Note**: here username is string ***apikey*** and password is the API key generated before or in the previous step.

```text
machine data.tern.org.au
login apikey
password <apikey>
```

## other usages

### searching for dataset by name

Usage: `geonadir-cli search-dataset <SEARCH_STR>`

sample usage and output:

```bash
PS C:\Users\uqtlan> geonadir-cli search-dataset SASMD
[
    {
        "id": 3256,
        "dataset_name": "SASMDD0006"
    },
    {
        "id": 3198,
        "dataset_name": "SASMDD0002"
    },
    {
        "id": 3197,
        "dataset_name": "SASMDD0003"
    },
    {
        "id": 3255,
        "dataset_name": "SASMDD0005"
    },
    {
        "id": 3199,
        "dataset_name": "SASMDD0004"
    },
    {
        "id": 2837,
        "dataset_name": "SASMDD0001"
    }
]
7 results.
```

### searching for dataset by coordinates

Usage: `geonadir-cli range-dataset <coords>`

Coordinates should be like `lon lat lon lat`.

It needs to be stated with `--` if no extra options is specified when coordinates contain negative (see example below).

sample usage and output:

```bash
PS C:\Users\uqtlan> geonadir-cli range-dataset -- 24 -34 29 -27
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
    },
    {
        "id": 2876,
        "latitude": -29.1854623611111,
        "longitude": 26.1971409444444
    },
    {
        "id": 2877,
        "latitude": -29.1813107777778,
        "longitude": 26.1913818888889
    },
    {
        "id": 2883,
        "latitude": -29.1813107777778,
        "longitude": 26.1913818888889
    },
    {
        "id": 3003,
        "latitude": -33.5088568333333,
        "longitude": 26.8160168883333
    },
    {
        "id": 3009,
        "latitude": -33.5098297216667,
        "longitude": 26.815559
    }
]
7 results.
```

### getting dataset information

Usage: `geonadir-cli get-dataset-info <DATASET_ID>`

sample usage and output:

```bash
PS C:\Users\uqtlan> geonadir-cli get-dataset-info 3198
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
```

## Packaging

Ensure `setuptool`, `pip`, `wheel` and `build` are up to date.
To build source and wheel package use `python -m build`.
To upload package to PyPi use `twine`.

## Contributing

- Fork the project and clone locally.
- Create a new branch for what you're going to work on.
- Push to your origin repository.
- Create a new pull request in GitHub.
