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
                                               
        Input_DEM_Rasters = arcpy.Parameter(name="Input_DEM",
                                            displayName="Input DEM rasters",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DERasterDataset",
                                            multiValue=True)

        Watershed_Flow_Direction_Rasters = arcpy.Parameter(name="Watershed_Flow_Direction_Rasters",
                                                           displayName="Watershed flow direction rasters",
                                                           direction="Input",
                                                           parameterType="Optional",
                                                           datatype="DERasterDataset",
                                                           multiValue=True)
                                                          
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

                                                          
        params = [rapid_file_Location, Watershed_Boundaries, Watershed_Boundaries_FC, Input_DEM_Rasters,
                  Watershed_Flow_Direction_Rasters, Number_of_cells_to_define_stream,
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
        Input_DEM_Rasters = parameters[3].valueAsText
        Watershed_Flow_Direction_Rasters = parameters[4].valueAsText
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
        
        # Process: Mosaic To New Raster for DEM
        Output_Mosaic_Elevation_DEM = os.path.join(rapid_file_Location, "Mosaic_Elevation_DEM")
        arcpy.MosaicToNewRaster_management(Input_DEM_Rasters, rapid_file_Location, "Mosaic_Elevation_DEM",
                                           "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")
        
        Output_Mosiac_Flow_Direction_Raster = os.path.join(rapid_file_Location, "Mosaic_Flow_Direction")
        if Watershed_Flow_Direction_Rasters:
            # Process: Mosaic To New Raster for Flow Direction
            arcpy.MosaicToNewRaster_management(Watershed_Flow_Direction_Rasters, rapid_file_Location, "Mosaic_Flow_Direction", 
                                               "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")
        else:
            #generate flow direction raster
            ArcHydroTools.FlowDirection(Output_Mosaic_Elevation_DEM, Output_Mosiac_Flow_Direction_Raster)
        
        while index < number_of_basins:
            #select basin 
            basins = os.path.join("in_memory", "basins")
            basinclip = arcpy.SelectLayerByAttribute_management(featureBasins, "NEW_SELECTION", '"FID" = %d' %index) 
            arcpy.Clip_analysis(basinclip, basinclip, basins) 

            # Process: Optional Buffer
            if str(Buffer_Option) == 'true':
                arcpy.Buffer_analysis(basins, Watershed_Buffer, Buffer_Distance, 
                                      "FULL", "ROUND", "NONE", "", "PLANAR")
            else:
                Watershed_Buffer = basins
                
            # Process: Extract by Mask for Flow Direction
            Output_Flow_Direction_Raster = os.path.join(rapid_file_Location, "Flow_Direction")
            arcpy.gp.ExtractByMask_sa(Output_Mosiac_Flow_Direction_Raster, Watershed_Buffer, Output_Flow_Direction_Raster)
            arcpy.Delete_management(Output_Mosiac_Flow_Direction_Raster)

            # Process: Extract by Mask for DEM
            Output_Elevation_DEM = os.path.join(rapid_file_Location, "Elevation_DEM")
            arcpy.gp.ExtractByMask_sa(Output_Mosaic_Elevation_DEM, Watershed_Buffer, Output_Elevation_DEM)
            arcpy.Delete_management(Output_Mosaic_Elevation_DEM)

            #generate stream network
            regionfolder = os.path.join(rapid_file_Location, AllRegionNames[index])
            regionID = AllRegionNames[index]
            arcpy.HydroSHEDStoStreamNetwork_RAPIDTools(regionID, regionfolder, Watershed_Buffer, Number_of_cells_to_define_stream,  AllCoordinates[index], "", Output_Elevation_DEM, Output_Flow_Direction_Raster)
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
            arcpy.Delete_management(Watershed_Buffer)
            arcpy.Delete_management(Output_Flow_Direction_Raster)
            arcpy.Delete_management(Output_Elevation_DEM)
            
            index = index + 1
        
        return