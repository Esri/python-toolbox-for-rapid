'''-------------------------------------------------------------------------------
 Tool Name:   AutomaticRAPIDfileGenerator
 Source Name: AutomaticRAPIDfileGenerator.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann
 Updated by:  Andrew Dohmann and Alan Snow
 Description: Batch processes HydroSHEDS data to RAPID files 
 History:     Initial coding - 06/29/2016, version 1.0
 Updated:     Version 1.1, 06/29/2016, initial coding
-------------------------------------------------------------------------------'''
import arcpy
import math
import os

class AutomaticRAPIDfileGenerator(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Automatic RAPID File Generator"
        self.description = ("Batch processes HydroSHEDS data to RAPID files")
        self.canRunInBackground = False
        self.category = "Workflows"

    def getParameterInfo(self):
        """Define parameter definitions"""
        rapid_file_Location = arcpy.Parameter(name="rapid_file_Location",
                                              displayName="RAPID Output File Location",
                                              direction="Input",
                                              parameterType="Required",
                                              datatype="DEFolder")
                                            
        Watershed_Boundaries_FC = arcpy.Parameter(name="Watershed_Boundaries_FC",
                                                  displayName="Watershed Boundaries Feature Class",
                                                  direction="Input",
                                                  parameterType="Required",
                                                  datatype="GPFeatureLayer")
        Watershed_Boundaries_FC.filter.list = ['Polygon'] 
        
        Input_DEM_Location = arcpy.Parameter(name="Input_DEM_Location",
                                             displayName="Input DEM Location",
                                             direction="Input",
                                             parameterType="Required",
                                             datatype="DEFolder")
                                                                                         
        Input_Flow_Location = arcpy.Parameter(name="Input_Flow_Location",
                                              displayName="Input Flow Direction Location",
                                              direction="Input",
                                              parameterType="Optional",
                                              datatype="DEFolder")

        Number_of_cells_to_define_stream = arcpy.Parameter(name="Number_of_cells_to_define_stream",
                                                           displayName="Number of Cells to Define Stream",
                                                           direction="Input",
                                                           parameterType="Required",
                                                           datatype="GPLong")

        Buffer_Option = arcpy.Parameter(name="Buffer_Option",
                                        displayName="Add 20 Kilometer Buffer",
                                        direction="Input",
                                        parameterType="Optional",
                                        datatype="GPBoolean")
        Buffer_Option.value = False                
                                                           
        Input_Reservoir = arcpy.Parameter(name = 'Input_Reservoir',
                                           displayName = 'Input Reservoir Layer',
                                           datatype = 'GPFeatureLayer',
                                           parameterType = 'Optional',
                                           direction = 'Input')
        Input_Reservoir.filter.list = ['Polygon']

                                                          
        params = [rapid_file_Location, Watershed_Boundaries_FC, Input_DEM_Location,
                  Input_Flow_Location, Number_of_cells_to_define_stream,
                  Buffer_Option, Input_Reservoir]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
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
        """The source code of the tool."""
        #Extensions
        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")
        else:
            arcpy.ExcecuteError("ERROR: The 3D Analyst extension is required to run this tool.")

        arcpy.env.overwriteOutput = True
        
        #Parameters
        rapid_file_Location = parameters[0].valueAsText
        Watershed_Boundaries_FC = parameters[1].valueAsText
        DEM_Location = parameters[2].valueAsText
        FlowDir_Location = parameters[3].valueAsText
        Number_of_cells_to_define_stream = parameters[4].valueAsText
        Buffer_Option = parameters[5].valueAsText
        Input_Reservoir = parameters[6].valueAsText
        
        #add utm coordinate information
        arcpy.AddField_management(Watershed_Boundaries_FC, "UTM_Zones", "TEXT", "", "", "600", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateUTMZone_cartography(Watershed_Boundaries_FC, "UTM_Zones")
 
        script_directory = os.path.dirname(__file__)
        arcpy.ImportToolbox(os.path.join(os.path.dirname(script_directory), "RAPID Tools.pyt"))
        
        shapeName = arcpy.Describe(Watershed_Boundaries_FC).shapeFieldName
        rows = arcpy.SearchCursor(Watershed_Boundaries_FC)
        for row in rows:
            UTM_Zone = row.getValue("UTM_Zones")
            HYBAS_ID = row.getValue("HYBAS_ID")
            RegionName = row.getValue("RegionName").replace(" ", "_").lower()
            regionID = str(int(HYBAS_ID)) + "-" + str(RegionName)
            
            arcpy.AddMessage("Running process for {}".format(regionID))
            arcpy.AddMessage("Searching for DEM/Flow Direction files ...")

            #Determine what data needs to be downloaded
            #get geometry feature of watershed
            basin_feat = row.getValue(shapeName)
            
            #bounds of Hydrosheds data needed
            newxmin = int(math.floor(basin_feat.extent.XMin/5.0) * 5)
            newxmax = int(math.ceil(basin_feat.extent.XMax/5.0) * 5)
            newymin = int(math.floor(basin_feat.extent.YMin/5.0) * 5)
            newymax = int(math.ceil(basin_feat.extent.YMax/5.0) * 5)
            
            #create list of files to download
            xtiles = ((newxmax - newxmin)/5) 
            ytiles = ((newymax-newymin)/5)
            DEMfile_names = []
            FlowDirfile_names = []
            xindex = 0
            yindex = 0
            while xindex < xtiles:
                east = newxmin + (xindex * 5)
                if east >= 0:
                    longitude = "e"
                    easting = str(east).zfill(3)  #pads with zeros
                else:
                    longitude = "w"
                    easting = str(-east).zfill(3)  #pads with zeros
                while yindex < ytiles:
                    north = newymin + (yindex * 5)
                    if north >= 0:
                        latitude = "n"
                        northing = str(north).zfill(2)  #pads with zeros
                    else:
                        latitude = "s"
                        northing = str(-north).zfill(2)  #pads with zeros
                    DEMfile = "%s%s%s%s_con.bil" % (latitude, northing, longitude, easting)
                    DEMfile_names.append(os.path.join(DEM_Location, DEMfile))
                    if FlowDir_Location:
                        flowdirfile ="%s%s%s%s_dir.grid" % (latitude, northing, longitude, easting)
                        FlowDirfile_names.append(os.path.join(FlowDir_Location, flowdirfile))
                    yindex = yindex + 1
                xindex = xindex + 1
                yindex = 0 
            
            #delete nonexistant files
            file_exist_index = 0
            existing_DEM_files = []
            existing_FlowDir_files = []
            for DEMfile_index in xrange(len(DEMfile_names)):
                if (arcpy.Exists(DEMfile_names[DEMfile_index])):
                    if FlowDir_Location:
                        if arcpy.Exists(FlowDirfile_names[DEMfile_index]):
                            existing_FlowDir_files.append(FlowDirfile_names[DEMfile_index])
                        else:
                            arcpy.AddError("Flow direction file not found: {0}".format(FlowDirfile_names[DEMfile_index]))
                    existing_DEM_files.append(DEMfile_names[DEMfile_index])
                else:
                    arcpy.AddMessage("WARNING: Could not find {} ...".format(DEMfile_names[DEMfile_index]))
            DEMfile_names = []
            FlowDirfile_names = []
            
            #Create multivalue input 
            DEMmulivalue = ";".join(existing_DEM_files)
            if FlowDir_Location:
                FlowDirmulivalue = ";".join(existing_FlowDir_files )
            else:
                FlowDirmulivalue = ""
            arcpy.AddMessage(DEMmulivalue)
            arcpy.AddMessage(FlowDirmulivalue)
            
            if DEMmulivalue:
                #create folder for file output
                regionfolder = arcpy.CreateFolder_management(rapid_file_Location, regionID)
                
                #generate stream network
                regionfolder = os.path.join(rapid_file_Location, regionID)
                arcpy.DEMtoStreamNetwork_RAPIDTools(regionID, regionfolder, basin_feat, Number_of_cells_to_define_stream, 
                                                    UTM_Zone, False, Buffer_Option, DEMmulivalue, FlowDirmulivalue)
                Output_DrainageLine = os.path.join(regionfolder, "{0}.gdb".format(regionID), "Layers", "DrainageLine")
                Output_Catchment = os.path.join(regionfolder, "{0}.gdb".format(regionID), "Layers", "Catchment")
                arcpy.AddMessage(Output_DrainageLine)

                #generate RAPID files
                RAPIDregionfolder = arcpy.CreateFolder_management(regionfolder, "RAPID_Files")
                arcpy.StreamNetworktoRAPID_RAPIDTools(RAPIDregionfolder, Output_DrainageLine, "HydroID", "NextDownID", "LENGTHKM", 
                                                      "Avg_Slope", Output_Catchment, "DrainLnID", Input_Reservoir) 
                
                #Generate SPT files
                STPregionfolder = arcpy.CreateFolder_management(regionfolder, "SPT_Files")
                arcpy.StreamNetworktoSPT_RAPIDTools(Output_DrainageLine, HYBAS_ID, RegionName, "", "", Output_Catchment, STPregionfolder) 
            else:
                arcpy.AddMessage("No DEM files found. Skipping ...")
        del row
        del rows
        
        return