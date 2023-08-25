# python-cli-template

A starting point for building Python Command Line Applications.

## About 

This project serves as a starting point to developing command line modules with Python. It is structured in such a way that 
when we call the module it executes the main method in `app/cli.py`. This is typically where you would want to add 
your own logic.

The setup.py file includes some advanced patterns and best 
practices for setup.py, as well as some commented–out nice–to–haves. For example, it provides a `python 
setup.py upload` command, which creates a universal wheel (and sdist) and uploads your package to PyPi using Twine. 
It also creates/uploads a new git tag, automatically.

## Setup

```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
python -m upload_dataset --help
```

# Running
```
python -m app upload-dataset -i test1 testimage -i test2 C:\tmp\testimage -p -m sample_metadata.json -t 83c0a339c7fe47029fd5abc35c835bf08a12d0a6
```

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
|      3174      | DJI_20220519122501_0041.JPG |        201        | 2.770872116088867 | 22500587       | True                 | (sample_url)  |


## Packaging 

Update `setup.py` with your details and then run `python setup.py upload` to package for distribution on PyPi.

## Contributing

- Fork the project and clone locally.
- Create a new branch for what you're going to work on.
- Push to your origin repository.
- Create a new pull request in GitHub.
