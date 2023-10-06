import os, sys, arcpy
import shutil
from typing import (List, Union)
numeric = Union[int, float]
from toolbox_utils.messages_print import log_it, setup_logging

class CopyFoldersForValidaton(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "0. Folder manipulation - Copy folders for validation"
        self.name = 'Copy Folders For Validaton'
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

        destination_folder = arcpy.Parameter(
            name='dest_folder',
            displayName="Path to folder where locations will be copied to",
            direction='Input',
            datatype=['DEFolder'],
            parameterType='Optional',
            enabled='True',
            multiValue='False',
        )



        # TODO - otestovat na neulozenem projektu
        log_file_path.value = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath))), 'logs')
        
        params = [log_file_path, root_dir_lokalita_multiple, destination_folder]

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
    class_name = CopyFoldersForValidaton().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)

def createFolder(fp):
    if not os.path.exists(fp):
        os.makedirs(fp)
        log_it(f"Folder '{os.path.basename(fp)}' created successfully.", 'info', __name__)
    else:
        log_it(f"Folder '{os.path.basename(fp)}' already exists. Chosen folders will be copied to it.", 'warning', __name__)


def main(log_dir_path: str, location_root_folder_paths: str, destination_folder:str = None) -> None:
    '''
    Main runtime - establishes required columns, required geometry.
    # '''

    # setup file logging
    init_logging(log_dir_path)
    log_it(log_dir_path, 'info', __name__)


    if destination_folder is None:
        data_folder = os.path.join(os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath), 'DATA')
        createFolder(data_folder)
    else:
        data_folder = destination_folder



    for location_folder in location_root_folder_paths.split(';'): # parse out multiple parameters (multiple folder paths)
        dest = os.path.join(data_folder, os.path.basename(location_folder))

        try:
            # Copy the entire folder and its contents
            shutil.copytree(location_folder, dest)
            log_it(f"Folder '{os.path.basename(location_folder)}' copied to '{dest}'", 'info', __name__)
        except Exception as e:
            log_it(f"Error copying folder {os.path.basename(location_folder)}", 'warning', __name__) 

###################################################
############# Run the tool from IDE ###############
# logs = r"I:\02_Projekty\17_model_3D\01_Zdrojova_data\01_Externi\TOPGIS\2023\kontrola_dat\Kontrola_dat_06_10_2023\logs"
# # bude nahrazeno za data
# root_folders = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TOPGIS_2023_10_3\Lokalita_93_2023_10_03;I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TOPGIS_2023_10_3\Lokalita_94_2023_10_03"

# # main(logs, folder_null)
# main(logs, root_folders)

####################################################