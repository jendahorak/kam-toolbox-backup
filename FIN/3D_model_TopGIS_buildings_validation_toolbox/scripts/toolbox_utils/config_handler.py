import os
import json
from toolbox_utils.messages_print import log_it


def get_config_data(geometry_type, config_path):
    data_folder = None
    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        log_it("Error: config.json file not found.", 'error', __name__)
        return None
    except json.JSONDecodeError:
        log_it("Error: config.json file is not valid JSON.", 'error', __name__)
        return None

    data_folder = config.get('default_path')
    if data_folder is None:
        log_it("Error: default_path not found in config.json.", 'error', __name__)
        return None

    if geometry_type == 'polygonz':
        out_workspace = os.path.join(
            data_folder, 'PolygonZ_DMR_attributes.gdb')
    elif geometry_type == 'multipatch':
        out_workspace = os.path.join(data_folder, 'Multipatch_attributes.gdb')
    else:
        log_it(f'Error: Wrong geometry type specified.', 'error', __name__)
        return None

    if not os.path.isdir(data_folder):
        log_it(
            f"Error: {data_folder} does not exist or is not a directory.", 'error', __name__)
        return None

    return out_workspace
