'''-------------------------------------------------------------------------------
 Tool Name:   AutomaticRAPIDfileGenerator
 Source Name: AutomaticRAPIDfileGenerator.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/29/2016, version 1.0
 Updated:     Version 1.1, 06/29/2016, initial coding
-------------------------------------------------------------------------------'''
import ArcHydroTools
import arcpy
import csv
import math
import os
import time


class AutomaticRAPIDfileGenerator(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Automatic RAPID file Generator"
        self.description = ("Batch processes HydroSHEDS data to RAPID files")
        self.canRunInBackground = False
        self.category = "Workflows"

    def getParameterInfo(self):
        """Define parameter definitions"""
        rapid_file_Location = arcpy.Parameter(name="rapid_file_Location",
                                              displayName="RAPID File Location",
                                              direction="Input",
                                              parameterType="Required",
                                              datatype="DEFolder")
                                            
        Watershed_Boundaries = arcpy.Parameter(name="Watershed_Boundaries",
                                               displayName="Watershed Boundaries",
                                               direction="Input",
                                               parameterType="Required",
                                               datatype="GPFeatureLayer")
                                               
        Watershed_Boundaries_FC = arcpy.Parameter(name="Watershed_Boundaries_FC",
                                                  displayName="Watershed Boundaries FC",
                                                  direction="Input",
                                                  parameterType="Required",
                                                  datatype="GPFeatureLayer")
                                               
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
                                                           displayName="Number of cells to define stream",
                                                           direction="Input",
                                                           parameterType="Required",
                                                           datatype="GPLong")

        Buffer_Option = arcpy.Parameter(name="Buffer_Option",
                                        displayName="Added 20 kilometer Buffer",
                                        direction="Input",
                                        parameterType="Optional",
                                        datatype="GPBoolean")
                                                           
        Input_Reservoir = arcpy.Parameter(name = 'Reservoir Input',
                                           displayName = 'Input_Reservoirs',
                                           datatype = 'GPFeatureLayer',
                                           parameterType = 'Optional',
                                           direction = 'Input')
        Input_Reservoir.filter.list = ['Polygon']

                                                          
        params = [rapid_file_Location, Watershed_Boundaries, Watershed_Boundaries_FC, Input_DEM_Location,
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
        Watershed_Boundaries = parameters[1].valueAsText
        Watershed_Boundaries_FC = parameters[2].valueAsText
        DEM_Location = parameters[3].valueAsText
        FlowDir_Location = parameters[4].valueAsText
        Number_of_cells_to_define_stream = parameters[5].valueAsText
        Buffer_Option = parameters[6].valueAsText
        Input_Reservoir = parameters[7].valueAsText
        
        #make boundary a feature class
        featureBasins = os.path.join(Watershed_Boundaries, "featureBasins")
        arcpy.MakeFeatureLayer_management(Watershed_Boundaries, featureBasins)
      
        #add utm coordinate information
        arcpy.AddField_management(Watershed_Boundaries_FC, "UTM_Zones", "TEXT", "", "", "600", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateUTMZone_cartography(Watershed_Boundaries_FC, "UTM_Zones")
        AllCoordinates = []
        rows = arcpy.UpdateCursor(Watershed_Boundaries_FC)
        for row in rows:
            UTM = row.getValue("UTM_Zones")
            AllCoordinates.append(UTM)
        del row
        del rows
       
        #Create files with unique name
        AllRegionNames = []
        AllRegionHYBAS_ID = []
        AllRegionNicknames = []
        rows = arcpy.UpdateCursor(Watershed_Boundaries)
        for row in rows:
            HYBAS_ID = int(row.getValue("HYBAS_ID"))
            AllRegionHYBAS_ID.append(HYBAS_ID)
            RegionName = row.getValue("RegionName")
            AllRegionNicknames.append(RegionName)
            regionID = str(HYBAS_ID) + "-" + str(RegionName).lower().replace(" ", "_")
            regionfolder = arcpy.CreateFolder_management(rapid_file_Location, regionID)
            AllRegionNames.append(regionID)
        del row
        del rows

        number_of_basins = len(AllRegionNames)
        index = 0
        script_directory = os.path.dirname(__file__)
        arcpy.ImportToolbox(os.path.join(os.path.dirname(script_directory), "RAPID Tools.pyt"))
        
        while index < number_of_basins:
            #select basin 
            basins = os.path.join("in_memory", "basins")
            basinclip = arcpy.SelectLayerByAttribute_management(featureBasins, "NEW_SELECTION", '"FID" = %d' %index) 
            arcpy.Clip_analysis(basinclip, basinclip, basins) 

            #Determine what data needs to be downloaded
            desc = arcpy.Describe(basins)
            #rectangular bounds of watershed
            xmin = desc.extent.XMin
            xmax = desc.extent.XMax
            ymin = desc.extent.YMin
            ymax = desc.extent.YMax
            #bounds of Hydrosheds data needed
            newxmin = int(math.floor(xmin/5.0) * 5)
            newxmax = int(math.ceil(xmax/5.0) * 5)
            newymin = int(math.floor(ymin/5.0) * 5)
            newymax = int(math.ceil(ymax/5.0) * 5)
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
                    #DEMname = "%s%s%s%s_con_bil" %(latitude, northing, longitude, easting) 
                    DEMfile = "%s%s%s%s_con.bil" %(latitude, northing, longitude, easting)
                    DEMlocationName = os.path.join(DEM_Location, DEMfile)
                    DEMfile_names.append(DEMlocationName)
                    if FlowDir_Location:
                        #FlowDirname = "%s%s%s%s_dir_grid" %(latitude, northing, longitude, easting)
                        flowdirfile ="%s%s%s%s_dir.grid" %(latitude, northing, longitude, easting)
                        FlowDirlocationName = os.path.join(FlowDir_Location, flowdirfile)                
                        FlowDirfile_names.append(FlowDirlocationName)
                    yindex = yindex + 1
                xindex = xindex + 1
                yindex = 0 

            #Create multivalue input 
            DEMmulivalue = ";".join(DEMfile_names )
            if FlowDir_Location:
                FlowDirmulivalue = ";".join(FlowDirfile_names )
            arcpy.AddMessage(DEMmulivalue)
         
            #generate stream network
            regionfolder = os.path.join(rapid_file_Location, AllRegionNames[index])
            regionID = AllRegionNames[index]
            arcpy.HydroSHEDStoStreamNetwork_RAPIDTools(regionID, regionfolder, basins, Number_of_cells_to_define_stream,  AllCoordinates[index], Buffer_Option, DEMmulivalue, "")
            Output_DrainageLine = os.path.join(os.path.join(regionfolder, os.path.join("%s.gdb" % regionID, "Layers")), "DrainageLine")
            Output_Catchment = os.path.join(os.path.join(regionfolder, os.path.join("%s.gdb" % regionID, "Layers")), "Catchment")
            arcpy.AddMessage(Output_DrainageLine)

            #generate RAPID files
            RAPIDregionfolder = arcpy.CreateFolder_management(regionfolder, ("RAPID_Files-%s" % regionID))
            arcpy.StreamNetworktoRAPID_RAPIDTools(RAPIDregionfolder, Output_DrainageLine, "HydroID", "NextDownID", Output_Catchment, "DrainLnID", Input_Reservoir) 
            
            #Generate SPT files
            STPregionfolder = arcpy.CreateFolder_management(regionfolder, ("STP_Files_%s" % regionID))
            arcpy.StreamNetworktoSPT_RAPIDTools(Output_DrainageLine, AllRegionHYBAS_ID[index], AllRegionNicknames[index], "", "", Output_Catchment, STPregionfolder) 
            
            #delete clip
            arcpy.Delete_management(basins)
            
            index = index + 1
        
        return