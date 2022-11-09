import os
import sys
import arcpy
import logging
from typing import (List, Union)
numeric = Union[int, float]
from toolbox_utils.messages_print import aprint, log_it, setup_logging # log_it printuje jak do arcgis console tak do souboru
from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms, get_gdb_path_3D_geoms_multiple

# TODO - optional file logging
class CheckMaxZ(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "6. Multipatch manipulation - Check Max Z"
        self.name = 'Check Max Z'
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

        input_mtp_workspace = arcpy.Parameter(
            name="input_mtp_dir",
            displayName="Input Workspace (gdb) for multipatch featureclasses with attributes result of Copy multipatch and joined PolygonZ attributes.",
            direction='Input',
            datatype='DEWorkspace',
            parameterType='Optional',
            enabled='True',
            multiValue='False'
        )

        
        input_mtp_workspace.filter.list = ["Local Database"]
        log_file_path.value = os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath)
        params = [log_file_path, input_mtp_workspace]

        return params

    
    def isLicensed(self):
        return True


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        input_mtp_gdb_obj = parameters[1]
        if input_mtp_gdb_obj.altered:
            input_mtp_gdb_obj.setWarningMessage('This tool will modify input multipatch data by adding columns')


        # Nefunguje protoze by to muselo prochazet i data sety a muselo by to být univerzální TODO do budoucna - udělat modul Get FC from GDB kdy je jedno jestli je to zapouzdřený v datasetu nebo ne.
        # input_mtp_gdb = parameters[1].valueAsText
       
        # if input_mtp_gdb_obj.altered and input_mtp_gdb_obj.datatype == 'Workspace':
        #     arcpy.env.workspace = input_mtp_gdb
        #     fc_mtps = [fc for fc in arcpy.ListFeatureClasses(feature_type='Multipatch')]
            # fc_mtps = [field.name for field in arcpy.ListFields(fc) for fc in arcpy.ListFeatureClasses(feature_type='Multipatch') if field.name == 'ABS_SEG_VYSKA']

        #     existing_fields = []
        #     for fc in fc_mtps:
        #         existing_fields.append('ABS_SEG_VYSKA' and 'ID_SEG' in [field.name for field in arcpy.ListFields(fc)]) 

        #     input_mtp_gdb_obj.setErrorMessage(fc_mtps)

        #     # if fc_mtps:
        #     #     if all(existing_fields):
        #     #         input_mtp_gdb_obj.clearMessage()
        #     #     else:
        #     #         input_mtp_gdb_obj.setErrorMessage('Data in chosen workspace doesnt have required columns [ABS_SEG_VYSKA or ID_SEG]')
        #     #     input_mtp_gdb_obj.clearMessage()
        #     # else:
        #     #     input_mtp_gdb_obj.setErrorMessage('Chosen workspace is emtpy or it doesnt contain required geometry (Multipatch)')
        # # parameters[1].setErrorMessage(fc_mtps)

        # # if len(fc_mtps) == 0:
        # #     parameters[1].setErrorMessage('Chosen workspace is empty or it doesnt contain required geometry (Multipatch)')
        # # else:
        # #     parameters[1].clearMessage()
        

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
    class_name = CheckMaxZ().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)

def copy_mtp_for_analysis(input_mtp_workspace:str, output_mtp_workspace:str) -> None:
    '''
    Creates copy of every fc inside input workspace in output workspace. 
    '''
    arcpy.env.workspace = input_mtp_workspace
    log_it(f'Copying input featureclasses to output workspace...', 'info', __name__)
    arcpy.env.overwriteOutput = True
    # TODO - dodelat check jestli tam jsou
    log_it(f'featureclasses with same name as input fc in output workspace will be overwritten', 'warning', __name__)

    for fc in arcpy.ListFeatureClasses(feature_type='Multipatch'):
        arcpy.conversion.FeatureClassToFeatureClass(fc, output_mtp_workspace,f'{fc}_analysis')

    arcpy.env.overwriteOutput = False


def log_maxZ_result(ids: List, input_fc: str) -> None:
    if ids != []:
        log_it(f'FC: {input_fc} - Rows (ID_SEG: {ids})  have more than one meter differnece in ABS_SEG_VYSKA and Z_Max', 'warning', __name__)
    else:
        log_it(f'FC: {input_fc} - No segments has more than one meter difference in ABS_SEG_VYSKA and Z_Max', 'info', __name__)



def fieldExists(dataset: str, field_name: str) -> bool:
    # TODO - udelat modul
    """Return boolean indicating if field exists in the specified dataset."""
    return field_name in [field.name for field in arcpy.ListFields(dataset)]


def max_z_check(input_fc):
    rows_with_faulty_Z = []
    required_fields = ['ABS_SEG_VYSKA', 'ID_SEG']
    work_fields = ['ABS_SEG_VYSKA', 'Z_Max', 'Z_Max_ABS_SEG_VYSKA_diff', 'ID_SEG']
    
    are_there = []
    for f in required_fields:
        are_there.append(fieldExists(input_fc, f)) 


    if all(i is True for i in are_there):
        arcpy.ddd.AddZInformation(input_fc, "Z_Max", '')
        arcpy.management.AddField(input_fc, 'Z_Max_ABS_SEG_VYSKA_diff', 'DOUBLE')
        with arcpy.da.UpdateCursor(input_fc, work_fields) as cur:
            for row in cur:
                # vypocita absolutni rozdil mezi ABS_SEG_VYSKA a Z_Max a ulozi do fieldu Z_Max_ABS_SEG_VYSKA_diff
                row[2] = abs(row[0] - row[1])
                cur.updateRow(row)
                # pokud je Z_Max_ABS_SEG_VYSKA_diff vyssi nez 1m priradi ID_SEG dane feature do listu ktery nasledne vyloguje
                if row[2] > 1:
                    rows_with_faulty_Z.append(row[3])
        del row
        del cur

        log_maxZ_result(rows_with_faulty_Z, input_fc)

    else:            
        log_it(f'{input_fc} is missing ABS_SEG_VYSKA or ID_SEG field. Operation for {input_fc} aborted.', 'warning', __name__)



def main(log_dir_path: str, input_mtp_workspace: str, *args) -> None:
    '''
    Main runtime. 
    '''

    init_logging(log_dir_path)

    if input_mtp_workspace:
        arcpy.env.workspace = input_mtp_workspace
        mtp_fcs = arcpy.ListFeatureClasses(feature_type='Multipatch')
        if mtp_fcs:
            for fc in mtp_fcs:
                log_it(fc, 'info', __name__)
                max_z_check(fc)
        else: 
            log_it("Input Workspace doesnt cointain featureclasses with Multipatch geometry or doesnt have flat sturcture - please input GDB with flat structure ommit datasets (only featureclasses with Multipatch geometry)", 'error', __name__)
    else:
        # this should be imposible
        arcpy.AddError('Parameters werent specified.')



###################################################
############# Run the tool from IDE ###############

## fake parametry
# imtpw = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\Broken_for_testing\mtp_with_attrs\mtp_attrs_43_broken.gdb"
# iml = ''
# omptw = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\new_output_workspaces\mtp_attrs_43_Z.gdb'
# log_file_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_logs'  # bude parameter
# main(log_file_path, imtpw, iml,omptw)

####################################################