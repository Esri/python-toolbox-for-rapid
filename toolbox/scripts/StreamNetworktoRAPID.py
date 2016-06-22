'''-------------------------------------------------------------------------------
 Tool Name:   StreamNetworktoRAPID
 Source Name: StreamNetworktoRAPID.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann and Alan Snow
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/21/2016, version 1.0
 Updated:     Version 1.0, 06/21/2016, initial coding
-------------------------------------------------------------------------------'''
import arcpy
import csv
import os

class StreamNetworktoRAPID(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Network to RAPID"
        self.description = ("Processes stream network data into files for RAPID")
        self.canRunInBackground = False
        self.category = "Workflows"

    def getParameterInfo(self):
        """Define parameter definitions"""
        rapid_out_folder = arcpy.Parameter(name = 'RAPID Output Folder',
                                           displayName = 'rapid_out_folder',
                                           datatype = 'DEFolder',
                                           parameterType = 'Required',
                                           direction = 'Input')
 
        Drainage_Lines = arcpy.Parameter(name="Drainage_Lines",
                                         displayName="Input Drainage Lines",
                                         direction="Input",
                                         parameterType="Required",
                                         datatype="GPFeatureLayer")
        Drainage_Lines.filter.list = ['Polyline']
        
        """
        #THIS SECTION IS FOR WHEN THE PARAMETERS ARE SHOWN IN THE FUTURE
        Stream_ID_DrainageLine = arcpy.Parameter(name="Stream_ID_DrainageLine",
                                                 displayName="Stream ID",
                                                 direction="Input",
                                                 parameterType="Required",
                                                 datatype="Field")
                                                 
        Stream_ID_DrainageLine.parameterDependencies = ["Drainage_Lines"]
        Stream_ID_DrainageLine.filter.list = ['Short', 'Long']
        Stream_ID_DrainageLine.value = "HydroID"
        
        Next_Down_ID = arcpy.Parameter(name="Next_Down_ID",
                                       displayName="Next Down ID",
                                       direction="Input",
                                       parameterType="Required",
                                       datatype="Field")
                                       
        Next_Down_ID.parameterDependencies = ["Drainage_Lines"]
        Next_Down_ID.filter.list = ['Short', 'Long']
        Next_Down_ID.value = "NextDownID"                        
        """
        
        Input_Catchment_Features = arcpy.Parameter(name="Input_Catchment_Features",
                                                   displayName="Input Catchment Features",
                                                   direction="Input",
                                                   parameterType="Required",
                                                   datatype="GPFeatureLayer")

        Input_Catchment_Features.filter.list = ['Polygon']
        
        Stream_ID_Catchments = arcpy.Parameter(name="Stream_ID_Catchments",
                                               displayName="Catchments Stream ID",
                                               direction="Input",
                                               parameterType="Required",
                                               datatype="Field")
                                               
        Stream_ID_Catchments.parameterDependencies = ["Input_Catchment_Features"]
        Stream_ID_Catchments.filter.list = ['Short', 'Long']
        Stream_ID_Catchments.value = "DrainLnID"
        
        params = [rapid_out_folder, Drainage_Lines, 
##                  Stream_ID_DrainageLine, Next_Down_ID,
                  Input_Catchment_Features, 
                  Stream_ID_Catchments]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        #CHECK LICENSING
        #Advanced License
        status = arcpy.SetProduct('arcInfo')
        if status == 'CheckedOut':
            pass
        if status == 'AlreadyInitialized':
            pass
        if status == 'NotLicensed':
            arcpy.ExcecuteError("ERROR: ArcGIS Advanced licence is required to run this tool.")
        if status == 'Failed':
            arcpy.ExcecuteError("ERROR: ArcGIS Advanced licence is required to run this tool.")
            
        #Extensions
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            arcpy.ExcecuteError("ERROR: The Spatial Analyst extension is required to run this tool.")
            
        arcpy.env.overwriteOutput = True
        
        rapid_out_folder = parameters[0].valueAsText
        Drainage_Lines = parameters[1].valueAsText
##        Stream_ID_DrainageLine = parameters[2].valueAsText
##        Next_Down_ID = parameters[3].valueAsText
        Input_Catchment_Features = parameters[2].valueAsText
        Stream_ID_Catchments = parameters[3].valueAsText
       
       
        script_directory = os.path.dirname(__file__)
        arcpy.ImportToolbox(os.path.join(os.path.dirname(script_directory), "RAPID Tools.pyt"))

        #Create Network Connecitivty File
        out_network_connectivity_file = os.path.join(rapid_out_folder, "rapid_connect.csv")
        arcpy.CreateNetworkConnectivityFile_RAPIDTools(Drainage_Lines, 
## Note: Esri's version does not expose thes parameters
##                                                       Stream_ID_DrainageLine, 
##                                                       Next_Down_ID,
                                                       out_network_connectivity_file)
        # Create subset file
        out_subset_file = os.path.join(rapid_out_folder, "riv_bas_id.csv")        
        arcpy.CreateSubsetFile_RAPIDTools(Drainage_Lines, out_subset_file)
        
                                                       
        #Create Muksingum Parameters
        # Process: Muksingum k
        out_muskingum_kfac_file = os.path.join(rapid_out_folder, "kfac.csv")
        arcpy.CreateMuskingumKfacFile_RAPIDTools(in_drainage_line_features=Drainage_Lines, 
                                                 stream_ID="HydroID", 
                                                 length="SLength", 
                                                 slope="Avg_Slope", 
                                                 co=1000.0/3600.0, 
                                                 in_formula="Eta*River Length/Sqrt(River Slope) [0.05, 0.95]", 
                                                 in_network_connectivity_file=out_network_connectivity_file,
                                                 out_muskingum_kfac_file=out_muskingum_kfac_file)
                                                 
        out_muskingum_k_file = os.path.join(rapid_out_folder, "k.csv")
        arcpy.CreateMuskingumKFile_RAPIDTools(0.35, 
                                              out_muskingum_kfac_file, 
                                              out_muskingum_k_file)
        # Process: Muksingum x                out_muskingum_k_file  
        #Add default field to file
        arcpy.AddField_management(Drainage_Lines, "Musk_x", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(Drainage_Lines, "Musk_x", "0.3", "PYTHON", "")

        #generate file #may need to fix
        out_muskingum_x_file = os.path.join(rapid_out_folder, "x.csv")
        with open(out_muskingum_x_file,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            count_result = arcpy.GetCount_management(Drainage_Lines)
            for row_index in xrange(int(count_result.getOutput(0))):
                connectwriter.writerow([0.3])

        lsm_grid_directory = os.path.join(script_directory, "lsm_grids")
        
        # Create ECMWF Low Res Weight Table
        low_resolution_ecmwf_grid =  os.path.join(lsm_grid_directory, "runoff_ecmwf_tco639_grid.nc")
        low_resolution_weight_table = os.path.join(rapid_out_folder, "weight_ecmwf_tco639.csv")        
        arcpy.CreateWeightTableFromECMWFRunoff_RAPIDTools(low_resolution_ecmwf_grid,
                                                          out_network_connectivity_file,
                                                          Input_Catchment_Features,
                                                          Stream_ID_Catchments,
                                                          low_resolution_weight_table) 

        # Create ECMWF High Res Weight Table
        high_resolution_ecmwf_grid =  os.path.join(lsm_grid_directory, "runoff_ecmwf_t1279_grid.nc")
        high_resolution_weight_table = os.path.join(rapid_out_folder, "weight_ecmwf_t1279.csv")        
        arcpy.CreateWeightTableFromECMWFRunoff_RAPIDTools(high_resolution_ecmwf_grid,
                                                          out_network_connectivity_file,
                                                          Input_Catchment_Features,
                                                          Stream_ID_Catchments,
                                                          high_resolution_weight_table) 
        
        # Create ERA Interim Weight Table
        era_interim_ecmwf_grid =  os.path.join(lsm_grid_directory, "runoff_era_t511_grid.nc")
        era_interim_weight_table = os.path.join(rapid_out_folder, "weight_era_t511.csv")        
        arcpy.CreateWeightTableFromECMWFRunoff_RAPIDTools(era_interim_ecmwf_grid,
                                                          out_network_connectivity_file,
                                                          Input_Catchment_Features,
                                                          Stream_ID_Catchments,
                                                          era_interim_weight_table) 

        # Flowline to point
        out_point_file =  os.path.join(rapid_out_folder, "comid_lat_lon_z.csv")
        arcpy.FlowlineToPoint_RAPIDTools(Drainage_Lines, out_point_file)
        
        return
