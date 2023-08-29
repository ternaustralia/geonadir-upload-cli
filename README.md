# geonadir_upload_cli

## About

This package is for uploading datasets to Geonadir. You can use it to upload multiple datasets at one time with metadata specified for any or all of them.

## Setup
After cloning this repo, run the commands below to install this package.

```
# create a virtual env before installing if you prefer
(virtualenv env)
(source env/bin/activate)
cd your/repo/directory/geonadir-upload-cli
pip install -e .
```

You can run this cli tool at any location. Call below command for detail.
```
geonadir-upload upload-dataset --help
```
## option details
Usage: geonadir-upload upload-dataset [OPTIONS]

Options:

- `--version`: show the version of this tool without any other action.

- `--dry-run`: show all information of this run without actual running.

- `-u, --base-url`: the base url of geonadir api. 

    - Default is https://api.geonadir.com

    - usually leave default

- `-t, --token`: the user token for authentication. 

    - When not specified in command, there will be a password prompt for it. (recommended for security’s sake)

- `-p, --private / --public`: whether datasets are private.

    - Default is public.

    - This option is applied to all datasets in a single run. Use metadata if some of the datasets need to be set differently.

- `-m, --metadata`: the path of metadata json file.

    - the path must exist, otherwise error raised

- `-o, --output-folder`: the folder to put output csv file in.

    - the path must exist, otherwise error raised

- `-c, --complete`: whether to trigger the orthomosaic processing once uploading is finished.

    - Default is false.

    - This option is applied to all datasets in a single run.

- `-i, --item`: the name of the dataset and the path of the images

    - this is a multiple option. user can upload multiple datasets in one command by e.g. 
`... -i dataset1 path1 -i dataset2 path2 ...`

    - all path(s) must exist, otherwise error raised

the final dataset name on Geonadir UI will be the name specified here plus the uploading timestamp, e.g., test1-20230825115634
# Running
An example of privately uploading `./testimage` as dataset **test1** and `C:\tmp\testimage` as **test2** with metadata file in `./sample_metadata.json`, and trigger the orthomosaic process when uploading is finished:
```
geonadir-upload -i test1 testimage -i test2 C:\tmp\testimage -p -m sample_metadata.json
```
The metadata specified in the json file will override the global settings, e.g. `is_private`.  
The final dataset name on Geonadir ui will be the name specified by user plus the uploading timestamp, e.g., **test1-20230825115634**

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
| **Project ID** |        **Image Name**       | **Response Code** |  **Upload Time**  | **Image Size** | **Is Image in API?** | **Image URL** |
|:--------------:|:---------------------------:|:-----------------:|:-----------------:|----------------|----------------------|---------------|
|      3174      | DJI_20220519122501_0041.JPG |        201        | 2.770872116088867 |    22500587    |         True         |  (image_url)  |
|      ...       |             ...             |        ...        |        ...        |      ...       |         ...          |      ...      |


## Packaging

Ensure `setuptool`, `pip`, `wheel` and `build` are up to date.
To build source and wheel package use `python -m build`.
To upload package to PyPi use `twine`.

## Contributing

- Fork the project and clone locally.
- Create a new branch for what you're going to work on.
- Push to your origin repository.
- Create a new pull request in GitHub.
