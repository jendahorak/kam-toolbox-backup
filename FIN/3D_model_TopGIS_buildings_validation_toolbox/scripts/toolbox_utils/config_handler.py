# config_handler.py

import os
import json


def get_config_data():
    try:
        with open('config.json') as f:
            config = json.load(f)
    except FileNotFoundError:
        log_it("Error: config.json file not found.", 'error', __name__)
        exit(1)

    data_folder = config.get('data_folder')

    if data_folder is None:
        log_it("Error: data_folder not found in config.json.", 'error', __name__)
        exit(1)
    if not os.path.exists(data_folder):
        log_it(
            f"Error: The folder {data_folder} does not exist.", 'error', __name__)
        exit(1)

    output_PolyZ_workspace = os.path.join(
        data_folder, 'PolygonZ_DMR_attributes.gdb')

    return output_PolyZ_workspace
