# import os
# import json
# from toolbox_utils.messages_print import log_it


def get_config_data(geometry_type):
    # try:
    #     with open('config.json') as f:
    #         config = json.load(f)
    # except FileNotFoundError:
    #     log_it("Error: config.json file not found.", 'error', __name__)
    #     exit(1)

    # data_folder = config.get('data_folder')

    # if data_folder is None:
    #     log_it("Error: data_folder not found in config.json.", 'error', __name__)
    #     exit(1)
    # if not os.path.exists(data_folder):
    #     log_it(
    #         f"Error: The folder {data_folder} does not exist.", 'error', __name__)
    #     exit(1)

    # if geometry_type == 'polygonz':
    #     output_PolyZ_workspace = os.path.join(data_folder, 'PolygonZ_DMR_attributes.gdb')
    # else if geometry_type == 'multipatch':
    #     output_PolyZ_workspace = os.path.join(data_folder, 'Multipatch_attributes.gdb.gdb')
    # else:
    #     log_it(f'Error: Wrong geometry type specified.', 'error', __name__)

    return geometry_type
