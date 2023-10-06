import os
import sys
import arcpy
import logging
from typing import (List, Union)
numeric = Union[int, float]
from toolbox_utils.messages_print import aprint, log_it, setup_logging # log_it printuje jak do arcgis console tak do souboru
from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms, get_gdb_path_3D_geoms_multiple


class CopyMultipatchWithPolygonZAttributes(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "5. Multipatch manipulation - Copy multipatch and join PolygonZ attributes."
        self.name = 'Copy multipatch and join PolygonZ attributes.'
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
            displayName="Path location of root folders (e.g.: Lokalita_00_YYYY_MM_DD):",
            direction='Input',
            datatype='DEFolder',
            parameterType='Required',
            enabled='True',
            multiValue='True'
        )


        output_mtp_workspace = arcpy.Parameter(
            name="output_mtp_dir",
            displayName="Output Workspace (gdb) for multipatch featureclasses with attributes:",
            direction='Input',
            datatype='DEWorkspace',
            parameterType='Required',
            enabled='True',
            multiValue='False'
        )

        output_mtp_workspace.filter.list = ["Local Database"]
        log_file_path.value = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath))), 'logs')
        output_mtp_workspace.value = os.path.join(os.path.join(os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath), 'DATA'),'Multipatch_attributes.gdb')

        params = [log_file_path, root_dir_lokalita_multiple, output_mtp_workspace]


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

def init_logging(log_dir_path: str) -> None:
    '''
    initializes logging instance (logger object, format, log_file locatio etc.) for current tool
    '''
    class_name = CopyMultipatchWithPolygonZAttributes().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)


# next 3 functions are very prasácký
def get_fc_from_gdb_within_dataset(gdb_path: str) -> str:
    '''
    Returns first feature class from first dataset in given gdb.
    '''
    arcpy.env.workspace = gdb_path

    for dat in arcpy.ListDatasets():
        for fc in arcpy.ListFeatureClasses('','', dat):
            return fc

def get_dataset_from_gdb(gdb_path: str) -> str:
    '''
    Returns first dataset from given gdb.
    '''
    arcpy.env.workspace = gdb_path

    for dat in arcpy.ListDatasets():
        return dat

def get_fc_from_gdb_direct(gdb_path, fc_name=None) -> str:
    '''
    Returns first fc from given gdb or any with specified name fc_name.
    '''
    arcpy.env.workspace = gdb_path

    for fc in arcpy.ListFeatureClasses(fc_name):
        return fc


def main(log_dir_path: str, location_root_folder_paths: str, output_mtp_workspace: str) -> None:
    '''
    Main runtime. Creates copy multipatch feature class in chosen workspace (gdb) and joins given attribute information to it from equivalent PolygonZ featureclass. 
    '''

    fields_to_be_joined = ['RUIAN_IBO', 'STRECHA_KOD', 'PATA_SEG_VYSKA', 'HORIZ_VYSKA', 'ABS_SEG_VYSKA']
    geoms = ['PolygonZ', 'Multipatch']

    # setup file logging
    init_logging(log_dir_path)

    for location_folder in location_root_folder_paths.split(';'): # parse out multiple parameters (multiple folder paths)
        polygon_z_gdb, multipatch_gdb = get_gdb_path_3D_geoms_multiple(location_folder, geoms, __name__)

        log_it(f'{"-"*100}','info', __name__)
        
        poly_dataset_name = get_dataset_from_gdb(polygon_z_gdb) # name of first Polygon_Z dataset
        poly_z_fc_name = get_fc_from_gdb_within_dataset(polygon_z_gdb) # name of first polygon z featureclass 
        mtp_fc = get_fc_from_gdb_within_dataset(multipatch_gdb) # name of first mtp fc 
        mtp_fc_name = f'{mtp_fc}_attrs' # name of new fc with joined attrs
        key_field = 'ID_SEG' # id field on which join will be based on

        if get_fc_from_gdb_direct(output_mtp_workspace, mtp_fc_name) == None:
            arcpy.env.workspace = multipatch_gdb
            log_it(f"CURRENT WORKSPACE: {arcpy.env.workspace}",'info',__name__)

            arcpy.conversion.FeatureClassToFeatureClass(mtp_fc, output_mtp_workspace, mtp_fc_name) # create copy of mtp fc
            log_it(f'Copy FeatureClass {mtp_fc} created in {output_mtp_workspace}', 'info', __name__)
            
            mtp_attrs_in_new_workspace = get_fc_from_gdb_direct(output_mtp_workspace, fc_name=mtp_fc_name) # change working env and get name of new copied mtp fc
            path_to_polygon_z_fc = os.path.join(polygon_z_gdb, poly_dataset_name, poly_z_fc_name) # build path to original polygon z fc with attributes to join to mtp 

            arcpy.management.JoinField(mtp_attrs_in_new_workspace, key_field, path_to_polygon_z_fc, key_field, fields_to_be_joined) # join attrs from polygon z fc to mtp fc
            log_it(f'Attributes {fields_to_be_joined} joined to {mtp_attrs_in_new_workspace}', 'info', __name__)
        else: 
            log_it(f'{mtp_fc_name} already exists in chosen workspace:\n{output_mtp_workspace}\n{mtp_fc_name} will not be created', 'warning', __name__)

###################################################
############# Run the tool from IDE ###############

# # fake parametry
# f = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\Fresh_TOPGIS\Lokalita_44_2022_08_11"
# # # # log_file_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\00_GIS\Budovy_Validation_project'  # bude parameter
# log_file_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_logs'  # bude parameter
# output_mtp_workspace = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_output_workspace\test_workspace_gdb.gdb'
# main(log_file_path, f, output_mtp_workspace)

####################################################