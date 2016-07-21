'''-------------------------------------------------------------------------------
 Tool Name:   StreamNetworktoRAPID
 Source Name: StreamNetworktoRAPID.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann and Alan Snow
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/21/2016, version 1.0
 Updated:     Version 1.0, 06/27/2016, initial coding
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
        rapid_out_folder = arcpy.Parameter(name = 'rapid_out_folder',
                                           displayName = 'RAPID Output Folder',
                                           datatype = 'DEFolder',
                                           parameterType = 'Required',
                                           direction = 'Input')
                                            
        input_Drainage_Lines = arcpy.Parameter(name="input_Drainage_Lines",
                                         displayName="Input Drainage Lines",
                                         direction="Input",
                                         parameterType="Required",
                                         datatype="GPFeatureLayer")
        input_Drainage_Lines.filter.list = ['Polyline']
        
        Stream_ID_DrainageLine = arcpy.Parameter(name="Stream_ID_DrainageLine",
                                                 displayName="Stream ID",
                                                 direction="Input",
                                                 parameterType="Required",
                                                 datatype="Field")
                                                 
        Stream_ID_DrainageLine.parameterDependencies = ["input_Drainage_Lines"]
        Stream_ID_DrainageLine.filter.list = ['Short', 'Long']
        Stream_ID_DrainageLine.value = "HydroID"
        
        Next_Down_ID = arcpy.Parameter(name="Next_Down_ID",
                                       displayName="Next Down ID",
                                       direction="Input",
                                       parameterType="Required",
                                       datatype="Field")
                                       
        Next_Down_ID.parameterDependencies = ["input_Drainage_Lines"]
        Next_Down_ID.filter.list = ['Short', 'Long']
        Next_Down_ID.value = "NextDownID"                        

        length_field_DrainageLine = arcpy.Parameter(name="length_field_DrainageLine",
                                                    displayName="Length Field (km)",
                                                    direction="Input",
                                                    parameterType="Required",
                                                    datatype="Field")
                                                 
        length_field_DrainageLine.parameterDependencies = ["input_Drainage_Lines"]
        length_field_DrainageLine.filter.list = ['Double']
        length_field_DrainageLine.value = "LENGTHKM"

        Slope_field_DrainageLine = arcpy.Parameter(name="Slope_field_DrainageLine",
                                                   displayName="Slope Field",
                                                   direction="Input",
                                                   parameterType="Required",
                                                   datatype="Field")
                                                 
        Slope_field_DrainageLine.parameterDependencies = ["input_Drainage_Lines"]
        Slope_field_DrainageLine.filter.list = ['Double']
        Slope_field_DrainageLine.value = "Avg_Slope"

        Catchment_Features = arcpy.Parameter(name="Catchment_Features",
                                             displayName="Input Catchment Features",
                                             direction="Input",
                                             parameterType="Required",
                                             datatype="GPFeatureLayer")

        Catchment_Features.filter.list = ['Polygon']

        Stream_ID_Catchments = arcpy.Parameter(name="Stream_ID_Catchments",
                                               displayName="Catchments Stream ID",
                                               direction="Input",
                                               parameterType="Required",
                                               datatype="Field")
                                               
        Stream_ID_Catchments.parameterDependencies = ["Catchment_Features"]
        Stream_ID_Catchments.filter.list = ['Short', 'Long']
        Stream_ID_Catchments.value = "DrainLnID"
        
        Input_Reservoir = arcpy.Parameter(name = 'Input_Reservoir',
                                           displayName = 'Input Reservoir Layer',
                                           datatype = 'GPFeatureLayer',
                                           parameterType = 'Optional',
                                           direction = 'Input')
        Input_Reservoir.filter.list = ['Polygon']

        params = [rapid_out_folder,
                  input_Drainage_Lines, 
                  Stream_ID_DrainageLine,
                  Next_Down_ID,
                  length_field_DrainageLine,
                  Slope_field_DrainageLine,
                  Catchment_Features,
                  Stream_ID_Catchments,
                  Input_Reservoir, 
                  ]

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
        Stream_ID_DrainageLine = parameters[2].valueAsText
        Next_Down_ID = parameters[3].valueAsText
        length_field_DrainageLine = parameters[4].valueAsText
        Slope_field_DrainageLine = parameters[5].valueAsText
        Catchment_Features = parameters[6].valueAsText
        Stream_ID_Catchments = parameters[7].valueAsText
        Input_Reservoirs = parameters[8].valueAsText
       
       
        script_directory = os.path.dirname(__file__)
        arcpy.ImportToolbox(os.path.join(os.path.dirname(script_directory), "RAPID Tools.pyt"))
        
        #Create Network Connecitivty File
        out_network_connectivity_file = os.path.join(rapid_out_folder, "rapid_connect.csv")
        arcpy.CreateNetworkConnectivityFile_RAPIDTools(Drainage_Lines, 
                                                       Stream_ID_DrainageLine, 
                                                       Next_Down_ID,
                                                       out_network_connectivity_file)
        # Create subset file
        out_subset_file = os.path.join(rapid_out_folder, "riv_bas_id.csv")        
        arcpy.CreateSubsetFile_RAPIDTools(Drainage_Lines, Stream_ID_DrainageLine, out_subset_file)
        
                                                       
        #Create Muksingum Parameters
        # Process: Muksingum k
        out_muskingum_kfac_file = os.path.join(rapid_out_folder, "kfac.csv")
        arcpy.CreateMuskingumKfacFile_RAPIDTools(in_drainage_line_features=Drainage_Lines, 
                                                 stream_ID=Stream_ID_DrainageLine, 
                                                 length=length_field_DrainageLine, 
                                                 slope=Slope_field_DrainageLine, 
                                                 co=1000.0/3600.0, 
                                                 in_formula="Eta*River Length/Sqrt(River Slope) [0.05, 0.95]", 
                                                 in_network_connectivity_file=out_network_connectivity_file,
                                                 out_muskingum_kfac_file=out_muskingum_kfac_file)
                                                 
        out_muskingum_k_file = os.path.join(rapid_out_folder, "k.csv")
        arcpy.CreateMuskingumKFile_RAPIDTools(0.35, 
                                              out_muskingum_kfac_file, 
                                              out_muskingum_k_file)
                                              
        # Process: Muskingum x  
        arcpy.CreateMuskingumXfile_RAPIDTools(rapid_out_folder, Drainage_Lines, Stream_ID_DrainageLine,"0.3", Input_Reservoirs)

        lsm_grid_directory = os.path.join(script_directory, "lsm_grids")
        
        # Create ECMWF Low Res Weight Table
        low_resolution_ecmwf_grid =  os.path.join(lsm_grid_directory, "runoff_ecmwf_tco639_grid.nc")
        low_resolution_weight_table = os.path.join(rapid_out_folder, "weight_ecmwf_tco639.csv")        
        arcpy.CreateWeightTableFromECMWFRunoff_RAPIDTools(low_resolution_ecmwf_grid,
                                                          out_network_connectivity_file,
                                                          Catchment_Features,
                                                          Stream_ID_Catchments,
                                                          low_resolution_weight_table) 

        # Create ECMWF High Res Weight Table
        high_resolution_ecmwf_grid =  os.path.join(lsm_grid_directory, "runoff_ecmwf_t1279_grid.nc")
        high_resolution_weight_table = os.path.join(rapid_out_folder, "weight_ecmwf_t1279.csv")        
        arcpy.CreateWeightTableFromECMWFRunoff_RAPIDTools(high_resolution_ecmwf_grid,
                                                          out_network_connectivity_file,
                                                          Catchment_Features,
                                                          Stream_ID_Catchments,
                                                          high_resolution_weight_table) 
        
        # Create ERA Interim Weight Table
        era_interim_ecmwf_grid =  os.path.join(lsm_grid_directory, "runoff_era_t511_grid.nc")
        era_interim_weight_table = os.path.join(rapid_out_folder, "weight_era_t511.csv")        
        arcpy.CreateWeightTableFromECMWFRunoff_RAPIDTools(era_interim_ecmwf_grid,
                                                          out_network_connectivity_file,
                                                          Catchment_Features,
                                                          Stream_ID_Catchments,
                                                          era_interim_weight_table) 

        # Flowline to point
        out_point_file =  os.path.join(rapid_out_folder, "comid_lat_lon_z.csv")
        arcpy.FlowlineToPoint_RAPIDTools(Drainage_Lines, out_point_file)

        return
