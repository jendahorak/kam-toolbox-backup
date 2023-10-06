import os
import sys
import json
import arcpy
import logging
from typing import (List, Union)
numeric = Union[int, float]
from toolbox_utils.messages_print import aprint, log_it, setup_logging # log_it printuje jak do arcgis console tak do souboru
from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms, get_gdb_path_3D_geoms_multiple
from toolbox_utils.clear_selection import clear_selection


class CheckGeometry(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "3. PolygonZ manipulation - Check geometry against attributes"
        self.name = 'Check Geometry Check geometry against attributes'
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        log_file_path = arcpy.Parameter(
            name='log_dir_path',
            displayName="Output location for the .log file:",
            direction='Input',
            datatype='DEFolder',
            parameterType='Required',
            enabled='True',
        )


        root_dir_lokalita_multiple = arcpy.Parameter(
            name="in_dir_multiple",
            displayName="Path location of root folder (Lokalita_00_YYYY_MM_DD)",
            direction='Input',
            datatype='DEFolder',
            parameterType='Required',
            enabled='True',
            multiValue='True'
        )

        tolerance = arcpy.Parameter(
            name='skewness_tolerance',
            displayName='Specify tolernace in meters for roof skewness',
            direction='Input',
            datatype='GPDouble',
            parameterType='Optional',
            enabled='True',
        )
        

        tolerance.value = 0
        tolerance.filter.type = "Range"
        tolerance.filter.list = [0, 500]
        log_file_path.value = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath))), 'logs')

        params = [log_file_path, root_dir_lokalita_multiple, tolerance]

        return params

    
    def isLicensed(self):
        # TODO - ?? 
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        pass

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        pass

    def execute(self, parameters, messages):
        """Process the parameters"""
        param_values = (p.valueAsText for p in parameters)
        try:
            main(*param_values) 
        except Exception as err:
            arcpy.AddError(err)
            sys.exit(1)
        return

def init_logging(log_dir_path: str) -> None:
    '''
    initializes logging instance (logger object, format, log_file locatio etc.) for current tool
    '''
    class_name = CheckGeometry().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)


def fieldExists(dataset: str, field_name: str) -> bool:
    """Return boolean indicating if field exists in the specified dataset."""
    return field_name in [field.name for field in arcpy.ListFields(dataset)]

def tableExists(table_name: str) -> bool:
    '''Return boolean indicating if table exists in the specified workspace.'''
    return table_name in [table for table in arcpy.ListTables(table_name)]


def get_fc_from_gdb_within_dataset(gdb_path: str, geometry='') -> str:
    '''
    Returns first feature class from first dataset in given gdb.
    '''
    arcpy.env.workspace = gdb_path

    for dat in arcpy.ListDatasets():
        for fc in arcpy.ListFeatureClasses(feature_type=geometry, feature_dataset=dat):
            return fc    

def get_fc_from_gdb_direct(gdb_path: str, fc_name=None) -> str:
    '''
    Returns first fc from given gdb or any with specified name fc_name.
    '''
    arcpy.env.workspace = gdb_path

    for fc in arcpy.ListFeatureClasses(fc_name):
        return fc

def no_geometry(fc_geometry_object: object, plocha_id: int) -> int:
    '''
    Returns list of ID_PLO where feature has no geometry.
    '''
    if fc_geometry_object == None:
        return plocha_id 


# TODO - muzem po nich chtit planaritu? 
# def check_if_planar()
#     return


def check_id_plo_attr_against_geometry(fc_geometry_object: object, plocha_kod: str, plocha_id: int, tolerance:int,  plocha_kod_spec: int=None) -> int:
    '''
    Function takes in geometry object of given feature and checks if geometry of that object coresponds to given attribute of plocha_kod_spec:PLOCHA_TYP
    '''

    # TODO - tolerance
    if plocha_kod == plocha_kod_spec:
        for part in fc_geometry_object:
                z_vals = [pnt.Z for pnt in part]
                x_vals = [pnt.X for pnt in part]
                if plocha_kod_spec == 3 or plocha_kod_spec == 1:
                    if len(set(z_vals)) == 1:
                        return plocha_id
                
                elif plocha_kod_spec == 2 or plocha_kod_spec == 4:
                    if len(set(z_vals)) != 1 and (max(z_vals) - min(z_vals)) > tolerance:
                        # print(set(z_vals))
                        return plocha_id
                else:
                    log_it('Input parameeters were specified incorectly', 'warning', __name__)
 
  

def check_parts_in(input_fc: str, level=None) -> List:
    '''
    Function takes feature and loops over coresponding level of abstraction (building, segment, plocha) and checks for given conditions 
    ID_SEG: Checks if segment has only one base polygon PLOCHA_KOD = 4 it returns ID_SEG of segments which have more than one or missing base polygon
    RUIAN_IBO: Checks if building has at least one roof face it returns RUIAN_IBO of buildings that dont have any roof polygon
    '''
    parent_object = {}
    with arcpy.da.SearchCursor(input_fc, [level, 'PLOCHA_KOD']) as cur:
        for row in cur:
            # create hashtable with SEG_ID/RUIAN_IBO: [*PLOCHA_KOD]  
                parent_object.setdefault(int(row[0]), []).append(int(row[1]))
    

    ids = []

    if level == 'ID_SEG':
        # create list of lists segment ids that has multiple or missing base polygons
        ids = [k for k, v in parent_object.items() if v.count(4) != 1]
    elif level == 'RUIAN_IBO':
        for k, v in parent_object.items():
            if v.count(2) + v.count(3) == 0:
                ids.append(k)

    return ids


def build_stats(input_fc: str, tolerance) -> None:
    '''
    Runtime function for chekcing geometry conditions
    '''
    stats = {}
    plocha_kod_types = {
        'svisla-stena': 1,
        'vodorovna-strecha': 2,
        'sikma-stresni-plocha': 3,
        'zakladova-deska': 4,
    }

    with arcpy.da.SearchCursor(input_fc, ["OID@", "SHAPE@", "PLOCHA_KOD", "ID_PLO", "ID_SEG"]) as cursor:
        for row in cursor:
            geometry_object = row[1]
            plocha_kod = row[2]
            plocha_id = row[3]    

            no_geom_ids = no_geometry(geometry_object, plocha_id)
            if no_geom_ids:
                stats.setdefault('plochy_bez_geometrie', []).append(no_geom_ids)

            for k, v in plocha_kod_types.items():
                curr_invalid_id_plo = check_id_plo_attr_against_geometry(geometry_object, plocha_kod, plocha_id, tolerance=tolerance, plocha_kod_spec=v)
                if curr_invalid_id_plo:
                    stats.setdefault(f'attribut_{k}_se_neshoduje_s_geometrii_ploch_ID-PLO', []).append(curr_invalid_id_plo)
    
    stats['segmenty_bez_nebo_s_vice_nezli_jednim_polygonem_pro_plochu_zakladova_deska_ID-SEG'] = check_parts_in(input_fc, level='ID_SEG')
    stats['budovy_bez_stresni_plochy_RUIAN-IBO'] = check_parts_in(input_fc, level='RUIAN_IBO')
    
    return stats


def log_out_stats(stats: dict, fc_name:str)-> None:
    '''
    Logs out ids of invalid features. 
    '''
    i = 0
    for k,v in stats.items():
        if v:
            i += 1
            log_it(f'{k.replace("_", " ").replace("-", "_")}: {v}', 'warning', __name__)
    if i == 0:
        log_it(f'{fc_name} geometry is correct', 'info', __name__)     


def main(log_dir_path: str, location_root_folder_paths: str, tolerance:int = 0) -> None:
    '''
    Main runtime.
    '''
    # setup file logging
    init_logging(log_dir_path)

    geoms = ['PolygonZ', 'Multipatch']
    

    for location_folder in location_root_folder_paths.split(';'):
        log_it('-' * 15 , 'info', __name__)
        log_it(f'Checking {location_folder}', 'info', __name__)
        polygonZgdb = get_gdb_path_3D_geoms(location_folder, geoms[0]) 
        cur_fc = get_fc_from_gdb_within_dataset(polygonZgdb)
        clear_selection(cur_fc)
        log_out_stats(build_stats(cur_fc, float(tolerance)),cur_fc) 



###################################################
############# Run the tool from IDE ###############

## fake parametry
# location_root_folder_paths = fr'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TopGIS_clean\Lokalita_43_2022_08_11'
# location_root_folder_paths_broken = fr'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\Broken_for_testing\PolygonZ_lokality_root_folders_broken\Lokalita_45_2022_08_11'
# log_file_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_logs'  # bude parameter
# main(log_dir_path=log_file_path, location_root_folder_paths=location_root_folder_paths_broken)

####################################################