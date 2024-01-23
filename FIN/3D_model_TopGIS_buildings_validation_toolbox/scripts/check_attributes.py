from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms
from toolbox_utils.messages_print import aprint, log_it, setup_logging
import os
import sys
import arcpy
import logging
from typing import (List, Union)
numeric = Union[int, float]


class CheckAttributeValues(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2. PolygonZ manipulation - Validate attribute schema and values"
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
            datatype=['DEFolder'],
            parameterType='Required',
            enabled='True',
            multiValue='True'
        )

        # TODO - otestovat na neulozenem projektu
        log_file_path.value = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath))), 'logs')

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


def has_duplicates(lst):
    return len(lst) != len(set(lst))



def log_out_problematic_features(problematic_features: dict, column_dicts) -> None:
    if problematic_features:
        for problem_k, problem_v in problematic_features.items():
            if len(problem_v) == len(column_dicts):
                log_it(
                    f'Problem {problem_k} found in all features in featureclass', 'warning', __name__)
            # elif (len(problem_v) > 50):
            #     log_it(
            #         f'Problem {problem_k} found in more than 50 ID_PLO: {problem_v[:50]}', 'warning', __name__)
            #     log_it(f'Due to large amount, not all results have been prited into the console, please check the data manualy', 'warning', __name__)
            else:
                if (has_duplicates(problem_v)):
                    uniqued = set(problem_v)
                    log_it(f'Problem {problem_k} occured for ID_SEG in {tuple(uniqued)}', 'warning', __name__)
                else:
                    log_it(f'Problem {problem_k} occured for ID_PLO in {tuple(problem_v)}', 'warning', __name__)

    else:
        log_it('Attribute values are correct', 'info', __name__)
    return


def decide_rimsa_column_name(fc: dict) -> str:
    conflicting_col_name = 'RIMSA_VYSKA'
    if 'HORIZ_VYSKA' in fc.keys():
        conflicting_col_name = 'HORIZ_VYSKA'
    return conflicting_col_name


def check_codelist(feature, column, start, stop) -> bool:
    return True if feature[f'{column}'] not in range(start, stop+1) else False


def evaluate_conds(conds, feature, problems):
    for cond_name, cond_val in conds.items():
        if cond_val:
            if cond_name == 'RIMSA_VYSKA HAS ABNORMALY SMALL VALUES':
                problems.setdefault(cond_name, []).append(int(feature['ID_SEG']))
            else:
                problems.setdefault(cond_name, []).append(int(feature['ID_PLO']))    
            
    return problems


def calculate_rimsa_vyska_rel(rimsa_vyska_val, pata_vyska_val, abs_vyska_val) -> numeric:
    rimsa_vyska_frac = (rimsa_vyska_val - pata_vyska_val) / (abs_vyska_val - pata_vyska_val)
    # log_it(f'RIMSA_VYSKA_REL: {rimsa_vyska_frac}', 'info', __name__)
    return rimsa_vyska_frac


def check_rimsa_vyska_rel_small(rimsa_vyska_frac) -> bool:
    return rimsa_vyska_frac < 0.3

def check_rimsa_vyska_rel_big(rimsa_vyska_frac) -> bool:
    return rimsa_vyska_frac > 0.9

# def check_rimsa_vyska_in_range(rimsa_vyska_frac, lower_bound, upper_bound) -> bool:
#     return lower_bound <= rimsa_vyska_frac <= upper_bound


def check_conditions(data) -> dict:
    '''
    Checks defined conditions for given columns - return dictionary with faulty features 
    '''
    problems = {}

    for feature in data:
        conditions = {}
        has_null = False
        conflicting_col_name = decide_rimsa_column_name(feature)

        for col, val in feature.items():
            if val is None:
                has_null = True
                conditions[f'NULL VALUES FOUND IN {col}'] = True

        if not has_null:
            rimsa_vyska_frac = calculate_rimsa_vyska_rel(feature[f'{conflicting_col_name}'], feature['PATA_SEG_VYSKA'], feature['ABS_SEG_VYSKA'])
            conditions = {
                'PATA_VYSKA >= ABS_VYSKA': feature['PATA_VYSKA'] >= feature['ABS_VYSKA'],
                'PATA_VYSKA >= HREBEN_VYSKA': feature['PATA_VYSKA'] >= feature['HREBEN_VYSKA'],
                'PATA_SEG_VYSKA >= ABS_SEG_VYSKA': feature['PATA_SEG_VYSKA'] >= feature['ABS_SEG_VYSKA'],
                'HORIZ_VYSKA ("RIMSA_VYSKA") > ABS_SEG_VYSKA': round(feature[f'{conflicting_col_name}'], 2) > round(feature['ABS_SEG_VYSKA'], 2),
                'PATA_SEG_VYSKA >= HORIZ_VYSKA ("RIMSA_VYSKA")': feature['PATA_SEG_VYSKA'] >= feature[f'{conflicting_col_name}'],
                'STRECHA_KOD CONTAINS INVALID VALUES': check_codelist(feature, 'STRECHA_KOD', 1, 7),
                'PLOCHA_KOD CONTAINS INVALID VALUES': check_codelist(feature, 'PLOCHA_KOD', 1, 4),
                'RIMSA_VYSKA HAS ABNORMALY SMALL VALUES': check_rimsa_vyska_rel_small(rimsa_vyska_frac),
                # 'RIMSA_VYSKA HAS ABNORMALY BIG VALUES': check_rimsa_vyska_rel_big(rimsa_vyska_frac),
                # 'RIMSA_VYSKA IS IN RANGE 0.3 - 0.7': check_rimsa_vyska_in_range(rimsa_vyska_frac, 0.3, 0.7),
            }   

        # Check if 'CAST_OBJEKTU' exists before adding its condition
        if 'CAST_OBJEKTU' in feature:
            conditions['CAST_OBJEKTU CONTAINS INVALID VALUES'] = check_codelist(
                feature, 'CAST_OBJEKTU', 1, 5)

        problems_out = evaluate_conds(conditions, feature, problems)

    return problems_out


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
            column_dicts = search_cursor_tuple_to_dict_colmn_name_keys(
                cursor, cols)
            log_out_problematic_features(
                check_conditions(column_dicts), column_dicts)

    # TODO - Dát tohle pryč - redundantni kdyz existuje check_feature_class_columns()
    # check if column missing in fc
    except RuntimeError:
        missing = set(cols) - set([str(x.name) for x in arcpy.ListFields(fc)])
        log_it('!! Feature Class is missing one or more required collumns !!',
               'warning', __name__)
        log_it(f'{"Column" if len(missing) == 1 else "Columns"} {" ".join(map(str, missing))} {"is" if len(missing) == 1 else "are"} missing.', 'warning', __name__)
        log_it(
            f'!! Attributes checking for {fc} aborted. Please repair {fc} !!', 'warning', __name__)

    pass


def check_feature_class_columns(fc, required_cols):
    existing_cols = set(field.name for field in arcpy.ListFields(fc))
    missing_cols = set(required_cols) - existing_cols
    extra_cols = existing_cols - set(required_cols)

    if missing_cols:
        log_it(
            f"Missing columns in the feature class {fc}: {', '.join(missing_cols)}", 'warning', __name__)
        return False

    if extra_cols:
        log_it(
            f"Extra columns found in the feature class {fc}: {', '.join(extra_cols)}", 'warning', __name__)
        return False

    return True


def init_logging(log_dir_path: str) -> None:
    '''
    initializes logging instance (logger object, format, log_file locatio etc.) for current tool
    '''
    class_name = CheckAttributeValues().name.replace(' ', '_')
    setup_logging(log_dir_path, class_name, __name__)


def main(log_dir_path: str, location_root_folder_paths: str) -> None:
    '''
    Main runtime - establishes required columns, required geometry.
    # '''

    # TODO - NUTNE VYRESIT V DATECH TAKHLE TO NEJDE
    required_cols = ["OBJECTID", "RUIAN_IBO", "ID_SEG", "ID_PLO", 'PATA_VYSKA', 'HREBEN_VYSKA', 'ABS_VYSKA', 'HORIZ_VYSKA',
                     'STRECHA_KOD', 'PATA_SEG_VYSKA', 'ABS_SEG_VYSKA', 'PLOCHA_KOD', 'CAST_OBJEKTU', 'SHAPE_Area', 'SHAPE_Length', 'SHAPE']
    geoms = ['PolygonZ', 'Multipatch']

    # setup file logging
    init_logging(log_dir_path)

    # parse out multiple parameters (multiple folder paths)
    for location_folder in location_root_folder_paths.split(';'):
        gdb = get_gdb_path_3D_geoms(location_folder, geoms[0])
        log_it(f'{"-"*100}', 'info', __name__)
        log_it(f"CURRENT GEODATABASE: {gdb}", 'info', __name__)

        arcpy.env.workspace = gdb
        datasets = arcpy.ListDatasets()

        for dat in datasets:
            for fc in arcpy.ListFeatureClasses('', '', dat):

                if check_feature_class_columns(fc, required_cols):
                    inspect_attributes(fc=fc, cols=required_cols)
                else:
                    return


###################################################
############# Run the tool from IDE ###############
# folder_null = r'I:\02_Projekty\17_model_3D\01_Zdrojova_data\01_Externi\TOPGIS\2020\UNZIPs\lokality\Lokalita_14'
# folder = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TOPGIS_2023_10_3\Lokalita_94_2023_10_03'
# logs = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\00_GIS\Budovy_Validation_project'

# main(logs, folder_null)

####################################################
