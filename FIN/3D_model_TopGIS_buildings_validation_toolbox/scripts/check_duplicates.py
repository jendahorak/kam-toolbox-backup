import os
import sys
import arcpy
from typing import List
from toolbox_utils.messages_print import aprint, log_it, setup_logging
from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms, get_gdb_path_3D_geoms_multiple


# TODO - dodealt metadata
class CheckDuplicates(object):
    '''
    Class as a arcgis tool abstraction in python
    '''
    def __init__(self):
        """Define tool parameters"""
        self.label = "1. All - Check Duplicates and ID fields"
        self.description = ""
        self.canRunInBackground = False
        self.name = 'Check Duplicates'

    def getParameterInfo(self):
        """Define parameter definitions"""

        log_file_path = arcpy.Parameter(
            name='log_dir_path',
            displayName="Output location for .log file:",
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

        log_file_path.value = os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath)
        params = [log_file_path,root_dir_lokalita_multiple]

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

def check_unique(id_list_non_uniqe: List, id_list_unique: List, id_field: str) -> str:
    '''
    Checks if given column id has duplicates, returns coresponding string. 
    '''
    if sorted(id_list_non_uniqe) == id_list_unique:
        log_it(f'FEATURE CLASS IS CORRECT - NO DUPLICATES', 'info', __name__) 
    else:
        log_it('FEATURE CLASS IS INCORRECT - HAS DUPLICATES','warning', __name__)
        log_it(f'{get_duplicates(id_list_non_uniqe, id_field)}', 'warning', __name__)
        pass

def get_duplicates(id_list_non_uniqe: List, id_field:str) -> str:
    '''
    Gets duplicate values returs coresponding string with list of duplicate values. 
    '''
    return f'DUPLICATE VALUES OF {id_field}: {list(set([x for x in id_list_non_uniqe if id_list_non_uniqe.count(x) > 1]))}' 

def build_stats(curr_col: str, num_of: int) -> str:
    '''
    Returns str with stats (number of features) for given column. 
    '''
    options = {'OBJECTID': f'NUMBER OF FEATURES: {num_of}','RUIAN_IBO': f'NUMBER OF BUILDINGS: {num_of}', 'ID_SEG': f'NUMBER OF SEGMENTS: {num_of}', 'ID_PLO': f'NUMBER OF ID_PLO: {num_of}' }

    if curr_col in options.keys():
        return options[curr_col]
    else:
        # TODO - test it out
        log_it('!! Some unexpected behaviour regarding names of columns !!','warning', __name__)



def inspect_columns(fc: str, cols: List[str], id_field: str) -> None:
    '''
    Loops thru individual features (rows) columns (cols) and checks if given featureclass (fc) contains duplicate features based on given unique field (id_field). Prints out corresponding statistics. 
    '''
    try:
        with arcpy.da.SearchCursor(fc, cols) as cursor:
            # list of tuples with values of given columns (cols)
            column_list = [row for row in cursor]
                
            abs_count_of_features = []
            for i in range(len(cols)):
                # list of unique values of given column
                list_of_unique = list(set([row[cols.index(cols[i])] for row in column_list]))
                # log stats    
                log_it(build_stats(cols[i], len(list_of_unique)),'info', __name__)
                # check uniqness
                if cols[i] == id_field:
                    # create non uniqe list of values
                    id_field_non_unique_list = [row[cols.index(id_field)] for row in column_list]
                    check_unique(id_field_non_unique_list,list_of_unique, id_field)
                
    except RuntimeError:
        missing = set(cols) - set([str(x.name) for x in arcpy.ListFields(fc)])
        log_it('!! Feature Class is missing one or more required collumns !!','warning', __name__)
        log_it(f'{"Column" if len(missing) == 1 else "Columns"} {" ".join(map(str, missing))} {"is" if len(missing) == 1 else "are"} missing.','warning', __name__)
        log_it(f'!! Attributes checking for {fc} aborted. Please repair {fc} !!','warning', __name__)


def init_logging(log_dir_path: str) -> object:
    class_name = CheckDuplicates().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)


def main(log_dir_path: str, location_root_folder_paths: str) -> None:
    '''
    Establishes required field names for PolygonZ and Multipatch FeatureClass. Loops thru GDBs and datasets, checks for missing columns, duplicates and prints out statistics. 
    '''

    # columns to be checked - id columns
    cols_fc_budovy = ["OBJECTID", "RUIAN_IBO", "ID_SEG", "ID_PLO"]
    cols_fc_mtp = ["OBJECTID", "ID_SEG"]

    # geometries to identify each gdb
    geoms = ['PolygonZ', 'Multipatch']


    # init logging
    init_logging(log_dir_path)

    # works for multiple input location root folders
    for location_folder in location_root_folder_paths.split(';'):
        # gets gdb paths 
        gdbs = get_gdb_path_3D_geoms_multiple(location_folder, geoms, __name__)
        # main loop 
        for gdb in gdbs:
            log_it('-' * 15 , 'info', __name__)
            log_it(f'Checking {location_folder}', 'info', __name__)
            arcpy.env.workspace = gdb
            datasets = arcpy.ListDatasets()

            for dat in datasets:
                for fc in arcpy.ListFeatureClasses("", "", dat):
                    log_it(f"CURRENT FEATURE CLASS: {fc} \nCURRENT DATASET: {dat}",'info',__name__)
                    if fc.startswith(f"lokalita"):
                        inspect_columns(fc, cols_fc_budovy, cols_fc_budovy[-1])
                    elif fc.startswith("multipatch"):
                        inspect_columns(fc, cols_fc_mtp, cols_fc_mtp[1])
                    else:
                        log_it("Given dataset doesnt contain any correctly named Feature Class",'info',__name__)



###################################################
############# Run the tool from IDE ###############
# Keep this commented when running tool in ArcGIS
# f = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TOPGIS\2022\UNZIPs\Lokalita_43_2022_08_11"  # bude parameter
# log_dir_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_logs'  # bude parameter
# main(log_dir_path, f)
####################################################