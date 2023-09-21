# geonadir_upload_cli

## About

This package is for uploading datasets to Geonadir. You can use it to upload multiple datasets at one time with metadata specified for any or all of them. This cli tool has other functions e.g. searching for dataset or getting dataset information.

## Setup
After cloning this repo, run the commands below to install this package.

```
# create a virtual env before installing if you prefer
(virtualenv env)
(source env/bin/activate)
cd your/repo/directory/geonadir-upload-cli
pip install -e .
```

You can run this cli tool from any location. Call below command for detail.
```
geonadir-upload upload-dataset --help
```
Call below command for showing current version of the package.
```
geonadir-upload --version
```
## option details
Usage: `geonadir-upload upload-dataset [OPTIONS]`

Options:

- `--dry-run`: Show all information of this run without actual running.

- `-u, --base-url`: The base url of geonadir api. 

    - Default is https://api.geonadir.com.

    - Usually leave default.

- `-t, --token`: The user token for authentication. 

    - When not specified in command, there will be a password prompt for it. (recommended for security’s sake)

- `-p, --private / --public`: Whether datasets are private.

    - Default is public.

    - This option is applied to all datasets in a single run. Use metadata if some of the datasets need to be set differently.

- `-m, --metadata`: The path of metadata json file.

    - The path must exist, otherwise error raised.

- `-o, --output-folder`: Whether output csv is created. Generate output at the specified path.

    - Default is false.

    - If flagged without specifying output folder, default is the current path of your terminal.

    - The path must exist, otherwise error raised.

- `-c, --complete`: Whether to trigger the orthomosaic processing once uploading is finished.

    - Default is false.

    - This option is applied to all datasets in a single run.

- `-i, --item`: The name of the dataset and the path of the images.

    - This is a multiple option. user can upload multiple datasets in one command by e.g.  
`... -i dataset1 path1 -i dataset2 path2 ...`

    - All path(s) must exist, otherwise error raised.
# Running
An example of privately uploading `./testimage` as dataset **test1** and `C:\tmp\testimage` as **test2** with metadata file in `./sample_metadata.json`, generating the output csv files in the current folder, and trigger the orthomosaic process when uploading is finished:
```
geonadir-upload -i test1 testimage -i test2 C:\tmp\testimage -p -m sample_metadata.json -o
```
The metadata specified in the json file will override the global settings, e.g. `is_private`.  

## sample metadata json
```
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
        "description": "test descriptu123on",
        "data_captured_by": "lan",
        "data_credits": "credit2",
        "institution_name": "Ndsf"
    }
}
```
## sample output
|   **Dataset Name**   | **Project ID** |        **Image Name**       | **Response Code** |  **Upload Time**  | **Image Size** | **Is Image in API?** | **Image URL** |
|:--------------------:|:--------------:|:---------------------------:|:-----------------:|:-----------------:|----------------|----------------------|---------------|
|         test1        |      3174      | DJI_20220519122501_0041.JPG |        201        | 2.770872116088867 |    22500587    |         True         |  (image_url)  |
|         ...          |      ...       |             ...             |        ...        |        ...        |      ...       |         ...          |      ...      |

## other usages
### searching for dataset
Usage: `geonadir-upload search-dataset SEARCH_STR`

sample usage and output:
```
PS C:\Users\uqtlan> geonadir-upload search-dataset SASMD
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
```

### getting dataset information
Usage: `geonadir-upload get-dataset-info DATASET_ID`

sample usage and output:
```
PS C:\Users\uqtlan> geonadir-upload get-dataset-info 3198
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
