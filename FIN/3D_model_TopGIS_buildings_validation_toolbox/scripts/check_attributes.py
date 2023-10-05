import os, sys, arcpy, logging
from typing import (List, Union)
numeric = Union[int, float]
from toolbox_utils.messages_print import aprint, log_it, setup_logging
from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms

class CheckAttributeValues(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2. PolygonZ manipulation - Check Attribute Values"
        self.name = 'Check Attribute Values'
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
            displayName="Path location of root folders (e.g.: Lokalita_00_YYYY_MM_DD)",
            direction='Input',
            datatype='DEFolder',
            parameterType='Required',
            enabled='True',
            multiValue='True'
        )

        # TODO - otestovat na neulozenem projektu
        log_file_path.value = os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath)
        params = [log_file_path, root_dir_lokalita_multiple]

        return params

    
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """Process the parameters"""
        param_values = (p.valueAsText for p in parameters)
        try:
            main(*param_values) 
        except Exception as err:
            arcpy.AddError(err)
            sys.exit(1)
        return

def log_out_problematic_features(problematic_features: dict, column_dicts) -> None:
    if problematic_features:
        for problem_k, problem_v in problematic_features.items():
            if len(problem_v) == len(column_dicts):
                log_it(f'Problem {problem_k} found in all features in featureclass', 'warning', __name__)
            else:
                log_it(f'Problem {problem_k} occured in ID_PLO: {problem_v}', 'warning', __name__)
    else:
        log_it('Attribute values are correct', 'info', __name__)
    return

def check_codelist(feature, column, start, stop,  ) -> bool:
    return True if feature[f'{column}'] not in range(start,stop+1) else False

def check_conditions(data) -> dict:
    '''
    Checks defined conditions for given columns - return dictionary with faulty features 
    '''
    # TODO - otestovat
    problems = {}

    for feature in data:
        conditions = {
        # TODO - check for  non null
        # TODO - check if segment has all same
        f'PATA_VYSKA >= ABS_VYSKA': feature['PATA_VYSKA'] >= feature['ABS_VYSKA'],
        f'PATA_VYSKA >= HREBEN_VYSKA': feature['PATA_VYSKA'] >= feature['HREBEN_VYSKA'],
        f'PATA_SEG_VYSKA >= ABS_SEG_VYSKA': feature['PATA_SEG_VYSKA'] >= feature['ABS_SEG_VYSKA'],
        f'HORIZ_VYSKA ("RIMSA_VYSKA") > ABS_SEG_VYSKA': round(feature['HORIZ_VYSKA'],2) > round(feature['ABS_SEG_VYSKA'],2),
        f'PATA_SEG_VYSKA >= HORIZ_VYSKA ("RIMSA_VYSKA")': feature['PATA_SEG_VYSKA'] >= feature['HORIZ_VYSKA'],
        f'STRECHA_KOD CONTAINS INVALID VALUES': check_codelist(feature, 'STRECHA_KOD', 1, 7),
        f'PLOCHA_KOD CONTAINS INVALID VALUES': check_codelist(feature, 'PLOCHA_KOD', 1, 4),
        f'CAST_OBJEKTU CONTAINS INVALID VALUES': check_codelist(feature, 'CAST_OBJEKTU', 1, 5)
        }
        for cond_name, cond_val in conditions.items():
            if cond_val:
                problems.setdefault(cond_name, []).append(feature['ID_PLO'])
    return problems
    
def search_cursor_tuple_to_dict_colmn_name_keys(cursor, cols) -> List[dict]:
    ''' 
    creates list of dicts instead of list of tuples -> feature: {column_name: column value}
    '''
    column_dicts = []
    for row in cursor:
        row_dict = {}
        for col_i in range(len(row)):
            row_dict[cols[col_i]] = row[col_i]                    
        column_dicts.append(row_dict)

    return column_dicts

def inspect_attributes(fc: str, cols: List[str]) -> None:
    '''
    Loop over all features of given feature class (fc) and specified columns.
    '''
    try:
        with arcpy.da.SearchCursor(fc, cols) as cursor:
            column_dicts = search_cursor_tuple_to_dict_colmn_name_keys(cursor, cols)
            log_out_problematic_features(check_conditions(column_dicts), column_dicts) 

    # check if column missing in fc 
    except RuntimeError:
        missing = set(cols) - set([str(x.name) for x in arcpy.ListFields(fc)])
        log_it('!! Feature Class is missing one or more required collumns !!','warning',__name__)
        log_it(f'{"Column" if len(missing) == 1 else "Columns"} {" ".join(map(str, missing))} {"is" if len(missing) == 1 else "are"} missing.','warning',__name__)
        log_it(f'!! Attributes checking for {fc} aborted. Please repair {fc} !!','warning',__name__)

    pass

def init_logging(log_dir_path: str) -> None:
    '''
    initializes logging instance (logger object, format, log_file locatio etc.) for current tool
    '''
    class_name = CheckAttributeValues().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)

def main(log_dir_path: str, location_root_folder_paths: str) -> None:
    '''
    Main runtime - establishes required columns, required geometry.
    '''
    required_cols = ["OBJECTID", "RUIAN_IBO","ID_SEG", "ID_PLO", 'PATA_VYSKA', 'HREBEN_VYSKA', 'ABS_VYSKA','HORIZ_VYSKA', 'STRECHA_KOD', 'PATA_SEG_VYSKA', 'ABS_SEG_VYSKA', 'PLOCHA_KOD', 'CAST_OBJEKTU']
    geoms = ['PolygonZ', 'Multipatch']

    # setup file logging
    init_logging(log_dir_path)

    for location_folder in location_root_folder_paths.split(';'): # parse out multiple parameters (multiple folder paths)
        gdb = get_gdb_path_3D_geoms(location_folder, geoms[0]) 
        log_it(f'{"-"*100}','info', __name__)
        log_it(f"CURRENT GEODATABASE: {gdb}",'info',__name__)

        arcpy.env.workspace = gdb
        datasets = arcpy.ListDatasets()

        for dat in datasets:
            for fc in arcpy.ListFeatureClasses('', '', dat):
                inspect_attributes(fc=fc, cols=required_cols)
    

###################################################
############# Run the tool from IDE ###############
# location_root_folder_paths_broken = fr'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\Broken_for_testing\PolygonZ_lokality_root_folders_broken\Lokalita_45_2022_08_11'
# log_file_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_logs'  # bude parameter
# main(log_file_path, location_root_folder_paths=location_root_folder_paths_broken)

####################################################