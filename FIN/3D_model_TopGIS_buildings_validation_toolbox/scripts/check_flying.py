import os
import sys
import arcpy
import logging
from typing import (List, Union)
numeric = Union[int, float]
from toolbox_utils.messages_print import aprint, log_it, setup_logging # log_it printuje jak do arcgis console tak do souboru
from toolbox_utils.gdb_getter import get_gdb_path_3D_geoms, get_gdb_path_3D_geoms_multiple

class CheckFlyingBuildings(object):
    '''
    Class as a arcgis tool abstraction in python
    '''

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4. PolygonZ manipulation - Check difference between geometry and DMR"
        self.name = 'Check difference between geometry and DMR'
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

        input_ground_DMR = arcpy.Parameter(
            name='input_dmr',
            displayName='Input DMR for height comparison',
            direction='Input',
            datatype = ['DERasterDataset','GPRasterLayer'],
            parameterType = 'Required',
            enabled = 'True'
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

        output_PolyZ_workspace = arcpy.Parameter(
            name="output_polyz_dir",
            displayName="Output Workspace (gdb) for PolygonZ featureclasses with attributes:",
            direction='Input',
            datatype='DEWorkspace',
            parameterType='Required',
            enabled='True',
            multiValue='False'
        )

        
        log_file_path.value = os.path.dirname(arcpy.mp.ArcGISProject("CURRENT").filePath)
        input_ground_DMR.value = r"I:\01_Data\02_Prirodni_pomery\04_Vyskopis\Brno\DMR_DMT\TOPGIS\2019\04_GIS\rastr\rastr\DMT2019\DTM_2019_L_025m.tif"
        output_PolyZ_workspace.filter.list = ["Local Database"]

        params = [log_file_path, input_ground_DMR, root_dir_lokalita_multiple, output_PolyZ_workspace]

        return params

    
    def isLicensed(self):
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
            return False  # The tool cannot be run
        
        return True  # The tool can be run

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


# UTILITY
def init_logging(log_dir_path: str) -> None:
    '''
    initializes logging instance (logger object, format, log_file locatio etc.) for current tool
    '''
    class_name = CheckFlyingBuildings().name.replace(' ', '_')
    setup_logging(log_dir_path,class_name, __name__)

def get_fc_from_gdb_within_dataset(gdb_path: str) -> str:
    '''
    Returns first feature class from first dataset in given gdb.
    '''
    arcpy.env.workspace = gdb_path

    for dat in arcpy.ListDatasets():
        for fc in arcpy.ListFeatureClasses('','', dat):
            return fc    

def get_fc_from_gdb_direct(gdb_path: str, fc_name=None) -> str:
    '''
    Returns first fc from given gdb or any with specified name fc_name.
    '''
    arcpy.env.workspace = gdb_path

    for fc in arcpy.ListFeatureClasses(fc_name):
        return fc

def fieldExists(dataset: str, field_name: str) -> bool:
    """Return boolean indicating if field exists in the specified dataset."""
    return field_name in [field.name for field in arcpy.ListFields(dataset)]


def tableExists(table_name: str) -> bool:
    '''Return boolean indicating if table exists in the specified workspace.'''
    # TODO - make optional to create zonal statistics 
    return table_name in [table for table in arcpy.ListTables(table_name)]    



def check_flying_buildings(input_fc:str, ground_dmr:str, workspace:str = None) -> None:
    ''' Updates values for DTM_diff  a DTM_diff_val. Checks if feature is under or over specified terrain.'''
    log_it(f'-'*15, 'info', __name__)
    log_it(f'Updating featureclasses with height attributes.', 'info', __name__)
   
    cols = ['PATA_SEG_VYSKA', 'MIN', 'MAX','DTM_diff_min_max_flatness', 'DTM_diff_max_info', 'ID_SEG','DTM_diff_min_info','DTM_diff_min','DTM_diff_max']

    bad_seg_ids = []

    with arcpy.da.UpdateCursor(input_fc, cols, where_clause='PLOCHA_KOD = 4') as cur:
        for row in cur:
            dtm_diff_min= row[0] - row[1]
            dtm_diff_max = row[0] - row[2]
            row[-2] = dtm_diff_min
            
            if dtm_diff_min > 0:
                row[-3] = 'PATA_SEG_VYSKA je nad DTM'
            elif dtm_diff_min < 0:
                row[-3] = 'PATA_SEG_VYSKA je pod DTM'
            else:
                row[-3] = 'PATA_SEG_VYSKA odpovida DTM'


            if dtm_diff_max >= 0:
                # log_it(f'{dtm_diff_max}', 'info', __name__)
                row[-1] = dtm_diff_max
                row[3] = row[2] -  row[1]
                if dtm_diff_max >= 0.5:
                    bad_seg_ids.append(int(row[5]))

        
            if dtm_diff_max > 0:
                row[4] = 'Celý segment je nad terénem'
            elif dtm_diff_max == 0:
                row[4] = 'Segment sedí na terénu alespoň jedním bodem'
            else:
                # momentálně není možné
                row[4] == 'Segment je pod terénem'    
            

            cur.updateRow(row)
    
    log_it(f'Checking {input_fc}...', 'info', __name__)
    log_it(f'Všechny body podstavy segmentu jsou výše nežli 0.5 m nad DMT ID_SEG: {bad_seg_ids}', 'warning', __name__)



def check_tables_and_fields(fc: str, zonal_stats_table_name: str, key_field: str, workspace: str, ground_dmr) -> None:
    '''Checks if in specified workspace exists a table or fields in existing fc if not creates them.'''
    arcpy.env.workspace = workspace
    out_table = os.path.join(workspace, zonal_stats_table_name)

    if not tableExists(zonal_stats_table_name):
        log_it('Creating new zonal table...', 'info', __name__)
        building_bases = arcpy.management.SelectLayerByAttribute(fc, "NEW_SELECTION", "PLOCHA_KOD = 4")
        out_table = os.path.join(workspace, zonal_stats_table_name)
        arcpy.sa.ZonalStatisticsAsTable(building_bases, key_field, ground_dmr, out_table, statistics_type='MIN_MAX_MEAN')
    else:
        log_it(f'Zonal Statistics for given {fc} in {workspace} were already calculated if you wish to recalculate them choose another output workspace', 'info', __name__)

    if not fieldExists(fc, 'MIN') and not fieldExists(fc, 'MAX'):
        arcpy.management.JoinField(fc, key_field, out_table, key_field, 'MIN')
        arcpy.management.JoinField(fc, key_field, out_table, key_field, 'MAX')
        arcpy.management.AddField(fc, 'DTM_diff_min', 'DOUBLE')
        arcpy.management.AddField(fc, 'DTM_diff_min_info', 'TEXT')
        arcpy.management.AddField(fc, 'DTM_diff_max', 'DOUBLE')
        arcpy.management.AddField(fc, 'DTM_diff_max_info', 'TEXT')
        arcpy.management.AddField(fc, 'DTM_diff_min_max_flatness', 'DOUBLE')
        
        log_it(f'Required fields were created in {fc}', 'info', __name__)
    else:
        log_it(f'Field MIN and MAX already exists in {fc}. Fields MIN, MAX wont be joined from ZonalTable', 'info', __name__)





def aggregate_into_new_workspace(location_root_folder_paths, path_to_copy_analysis_workspace, ground_dmr):
    ''' In output workspace creates copy of input PolygonZ geometry if it doesn not exist already. '''
    geoms = ['PolygonZ', 'Multipatch']
    for location_folder in location_root_folder_paths.split(';'): # parse out multiple parameters (multiple folder paths)
        log_it(f'-'*15, 'info', __name__)
        log_it(f'Checking exitence of featureclasses, tables and fields.', 'info', __name__)

        polygonZgdb = get_gdb_path_3D_geoms(location_folder, geoms[0]) 
        cur_fc = get_fc_from_gdb_within_dataset(polygonZgdb)
        output_fc_name = f'{cur_fc}_polygonZ_geom_analysis'

        key_field = 'ID_PLO'
        zonal_stats_table_name = f'{output_fc_name}_zonal_stat_base'

        if get_fc_from_gdb_direct(path_to_copy_analysis_workspace, output_fc_name) == None:
            arcpy.env.workspace = polygonZgdb
            arcpy.conversion.FeatureClassToFeatureClass(cur_fc,path_to_copy_analysis_workspace,output_fc_name)
            log_it(f'New {output_fc_name} created at {path_to_copy_analysis_workspace}', 'info', __name__)

        else: 
            log_it(f'{output_fc_name} already exists in chosen workspace:\n{path_to_copy_analysis_workspace}\n{output_fc_name} will be updated.', 'warning', __name__)

        
        check_tables_and_fields(output_fc_name, zonal_stats_table_name, key_field, path_to_copy_analysis_workspace, ground_dmr)


def main(log_dir_path: str, input_ground_DMR: str, location_root_folder_paths: str, path_to_copy_analysis_workspace:str, *args) -> None:
    '''
    Main runtime.
    '''
 
    arcpy.CheckOutExtension("Spatial")

    # setup file logging
    init_logging(log_dir_path)

    # copy PolygonZ fcs to specified output workspace
    aggregate_into_new_workspace(location_root_folder_paths, path_to_copy_analysis_workspace, input_ground_DMR)

#   # change workspace to output workspace
    arcpy.env.workspace = path_to_copy_analysis_workspace
    for fc in arcpy.ListFeatureClasses():
        dirname = os.path.dirname(arcpy.Describe(fc).catalogPath)
        check_flying_buildings(fc, input_ground_DMR, dirname)
        pass

###################################################
############# Run the tool from IDE ###############

## fake parametry
# imtpw = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TOPGIS_2021\Lokalita_21_2021_08_10"
# imtpw = r"I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\02_Input_Data\TopGIS_clean\Lokalita_43_2022_08_11"
# raster = r'I:\01_Data\02_Prirodni_pomery\04_Vyskopis\Brno\DMR_DMT\TOPGIS\2019\04_GIS\rastr\rastr\DMT2019\DTM_2019_L_025m.tif'
# omptw = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\new_output_workspaces\polyZ_workspace.gdb'
# log_file_path = r'I:\04_Hall_of_Fame\11_Honza_H\00_Projekty\12_3D_model_validation_refactoring\01_Developement\02_Output\test_logs'  # bude parameter
# main(log_dir_path=log_file_path, input_ground_DMR=raster, location_root_folder_paths=imtpw, path_to_copy_analysis_workspace=omptw)

####################################################