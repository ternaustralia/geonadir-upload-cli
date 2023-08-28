# geonadir_upload_cli

## About

This package is for uploading datasets to Geonadir. You can use it to upload multiple datasets at one time with metadata specified for any or all of them.

## Setup
After cloning this repo, run the commands below to install this package.

```
(virtualenv env)
(source env/bin/activate)
cd your/repo/directory/geonadir-upload-cli
pip install -e .
```

You can run this cli tool at any location. Call below command for detail.
```
geonadir-upload upload-dataset --help
```

# Running
An example of uploading *./testimage* as dataset **test1** and *C:\tmp\testimage* as **test2** with metadata file in *sample_metadata.json*
```
geonadir-upload -i test1 testimage -i test2 C:\tmp\testimage -p -m sample_metadata.json
```
The metadata specified in the json file will override the global settings, e.g. is_private.  
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
