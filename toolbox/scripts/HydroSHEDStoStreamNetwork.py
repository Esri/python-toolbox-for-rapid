'''-------------------------------------------------------------------------------
 Tool Name:   HydroSHEDStoStreamNetwork
 Source Name: HydroSHEDStoStreamNetwork.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Andrew Dohmann
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/17/2016, version 1.0
 Updated:     Version 1.0, 06/17/2016, initial coding
-------------------------------------------------------------------------------'''
import arcpy
import os

class HydroSHEDStoStreamNetwork(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "HydroSHEDS to Stream Network"
        self.description = ("Processes DEM data to stream network")
        self.canRunInBackground = False
        self.category = "Workflows"

    def getParameterInfo(self):
        """Define parameter definitions"""
        File_GDB_Name = arcpy.Parameter(name="File_GDB_Name",
                                        displayName="File Geodatabase Name",
                                        direction="Input",
                                        parameterType="Required",
                                        datatype="GPString")

        File_GDB_Location = arcpy.Parameter(name="File_GDB_Location",
                                            displayName="File Geodatabase Location",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DEFolder")
                                            
        Watershed_Boundary = arcpy.Parameter(name="Watershed_Boundary",
                                            displayName="Watershed Boundary",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DEFeatureClass")

        Input_DEM_Rasters = arcpy.Parameter(name="Input_DEM",
                                    displayName="Input DEM rasters",
                                    direction="Input",
                                    parameterType="Required",
                                    datatype="DERasterDataset",
                                    multiValue=True)

        Watershed_Flow_Direction_Rasters = arcpy.Parameter(name="Watershed_Flow_Direction_Rasters",
                                                           displayName="Watershed flow direction rasters",
                                                           direction="Input",
                                                           parameterType="Required",
                                                           datatype="DERasterDataset",
                                                           multiValue=True)

        params = [File_GDB_Name, File_GDB_Location, Watershed_Boundary,
                  Input_DEM_Rasters, Watershed_Flow_Direction_Rasters]

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
        arcpy.env.overwriteOutput = True
        
        File_GDB_Name = parameters[0].valueAsText
        File_GDB_Location = parameters[1].valueAsText
        Watershed_Boundary = parameters[2].valueAsText
        Input_DEM_Rasters = parameters[3].valueAsText
        Watershed_Flow_Direction_Rasters = parameters[4].valueAsText
        
        # Local variables:
        Dataset = "Layers"
        Path_to_GDB = os.path.join(File_GDB_Location, File_GDB_Name)
        Path_to_GDB_dataset = os.path.join(Path_to_GDB, Dataset)

        Coordinate_System = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984'," \
                            "SPHEROID['WGS_1984',6378137.0,298.257223563]]," \
                            "PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];" \
                            "-400 -400 1000000000;-100000 10000;-100000 10000;" \
                            "8.98315284119522E-09;0.001;0.001;IsHighPrecision"
                            
        Buffer_Distance = "20 Kilometers"
        Watershed_Buffer = os.path.join(Path_to_GDB_dataset, "Watershed_Buffer")
        Output_Mosaic_Elevation_DEM = os.path.join(Path_to_GDB, "Mosaic_Elevation_DEM")
        Output_Elevation_DEM = os.path.join(Path_to_GDB, "Elevation_DEM")
        Output_Mosiac_Flow_Direction_Raster = os.path.join(Path_to_GDB, "Mosaic_Flow_Direction")
        Output_Flow_Direction_Raster = os.path.join(Path_to_GDB, "Flow_Direction")
        
        # Process: Create File GDB
        arcpy.CreateFileGDB_management(File_GDB_Location, File_GDB_Name, "CURRENT")

        # Process: Create Feature Dataset
        arcpy.CreateFeatureDataset_management(Path_to_GDB, Dataset, Coordinate_System)

        # Process: Buffer
        arcpy.Buffer_analysis(Watershed_Boundary, Watershed_Buffer, Buffer_Distance, 
                              "FULL", "ROUND", "NONE", "", "PLANAR")

        # Process: Mosaic To New Raster for DEM
        arcpy.MosaicToNewRaster_management(Input_DEM_Rasters, Path_to_GDB, "Mosaic_Elevation_DEM",
                                           "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")

        # Process: Extract by Mask for DEM
        arcpy.gp.ExtractByMask_sa(Output_Mosaic_Elevation_DEM, Watershed_Buffer, Output_Elevation_DEM)
        arcpy.Delete_management(Output_Mosaic_Elevation_DEM)

        # Process: Mosaic To New Raster for Flow Direction
        arcpy.MosaicToNewRaster_management(Watershed_Flow_Direction_Rasters, Path_to_GDB, "Mosaic_Flow_Direction", 
                                           "", "16_BIT_SIGNED", "", "1", "LAST", "FIRST")

        # Process: Extract by Mask for Flow Direction
        arcpy.gp.ExtractByMask_sa(Output_Mosiac_Flow_Direction_Raster, Watershed_Buffer, Output_Flow_Direction_Raster)
        arcpy.Delete_management(Output_Mosiac_Flow_Direction_Raster)

        return
