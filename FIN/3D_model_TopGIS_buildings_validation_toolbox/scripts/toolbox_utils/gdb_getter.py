import arcpy
import os
from typing import List


f = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TOPGIS\2022\UNZIPs\Lokalita_43_2022_08_11"
# TODO - predelat do moznosti to get multiple gbs

def get_gdb_path_3D_geoms(location_folder: str, geometry: str) -> str:
    '''
    Gets path to GDB containing desired data type (3D geometry). 
    '''
    for subdir, dirs, files in os.walk(location_folder):
        if geometry == 'Multipatch':
            if subdir.endswith('_multipatch.gdb'):
                return subdir
        elif geometry == 'PolygonZ':
            if subdir.endswith('.gdb') and '_multipatch' not in subdir:
                return subdir
        else:
            print('Geometry wasnt specified correctly.')


# TODO - dat pryc log

def get_gdb_path_3D_geoms_multiple(locality_folder_path: str, desired_geoms: List[str], tool_name) -> List:
    '''
    Returns list with paths to desired geodatabases (PolygonZ, Multipatch).
    '''
    gdb_paths = []

    for geom in desired_geoms:
        gdb_paths.append(get_gdb_path_3D_geoms(locality_folder_path, geom)) 
    
    return gdb_paths