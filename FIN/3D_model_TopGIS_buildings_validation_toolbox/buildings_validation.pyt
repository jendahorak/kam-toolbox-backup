# import libs

import os, sys, importlib

# List of directories where modules are searched
scripts_folder = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.append(scripts_folder)

import check_duplicates, check_attributes, copy_multipatch_with_polygon_z_attributes, check_max_Z, check_flying, check_geometry, create_env

# Utilitka pro reloadování při testování kodu v ArcPRO
for tool in [check_duplicates, check_attributes, copy_multipatch_with_polygon_z_attributes, check_max_Z, check_flying, check_geometry, create_env]:
    importlib.reload(tool)
    
from check_duplicates import CheckDuplicates
from check_attributes import CheckAttributeValues
from copy_multipatch_with_polygon_z_attributes import CopyMultipatchWithPolygonZAttributes
from check_max_Z import CheckMaxZ
from check_flying import CheckFlyingBuildings
from check_geometry import CheckGeometry
from create_env import CopyFoldersForValidaton


class Toolbox(object):
    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""

    def __init__(self) -> None:
        self.label = 'Buildings validation'
        self.alias = 'buildingsvalidation'
        self.tools = [CheckDuplicates, CheckAttributeValues, CheckGeometry, CheckFlyingBuildings, CopyMultipatchWithPolygonZAttributes, CheckMaxZ, CopyFoldersForValidaton]
        pass