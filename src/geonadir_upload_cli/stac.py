import pystac


def get_filelist_from_collection(collection_path:str, root_catalog_url:str):
    collection = pystac.Collection.from_file(collection_path)
    catalog = collection.get_parent()
    root_path = collection.get_root().self_href.removesuffix("/catalog.json")  # /home/user(/catalog.json)
    root_remote_path = root_catalog_url.removesuffix("/catalog.json")  # https://data-test.tern.org.au(/catalog.json)
    self_href = catalog.self_href.removesuffix("/catalog.json")  # /home/user/uas_raw/surveillance/imagery(/catalog.json)
    catalog.normalize_hrefs(root_remote_path + self_href.removeprefix(root_path))  # normalize to 'https://data-test.tern.org.au/uas_raw/surveillance/imagery'
    collection = catalog.get_child(collection.id)
    file_dict = {}
    for name, asset in collection.assets.items():
        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            file_dict[name] = asset.get_absolute_href()

    return file_dict


def really_get_all_collections(catalog:pystac.Catalog):
    yield from catalog.get_collections()
    for child in catalog.get_children():
        yield from really_get_all_collections(child)