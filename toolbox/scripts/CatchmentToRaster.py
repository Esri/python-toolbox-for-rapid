'''-------------------------------------------------------------------------------
 Tool Name:   CatchmentToRaster
 Source Name: CatchmentToRaster.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Creates RAPID inflow file based on ECMWF runoff output
              and the weight table previously created.
 History:     Initial coding - 5/13/2016, version 1.0
 Updated:     Tool completed on 6/10/2016, version 1.0
-------------------------------------------------------------------------------'''
import os
import arcpy
import netCDF4 as NET
import numpy as NUM
import csv

class CatchmentToRaster(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Convert Catchment Polygons to Raster"
        self.description = "Convert catchment polygons to raster with stream ID \
                              as values"
        self.canRunInBackground = True
        self.category = "Postprocessing for Flood Inundation"


    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_catchment_features",
                                 displayName = "Input Catchment Features",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPFeatureLayer")
        param0.filter.list = ['Polygon']

        param1 = arcpy.Parameter(name= "stream_ID",
                                 displayName= "Stream ID",
                                 direction= "Input",
                                 parameterType= "Required",
                                 datatype = "Field"
                                 )
        param1.parameterDependencies = ["in_catchment_features"]
        param1.filter.list = ['Short', 'Long']


        param2 = arcpy.Parameter(name="in_HAND_raster_dataset",
                                 displayName="HAND Raster Dataset",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="GPRasterLayer")


        param3 = arcpy.Parameter(name = "out_catchment_raster",
                                 displayName = "Output Catchment Raster",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DERasterDataset")


        params = [param0, param1, param2, param3]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[2].altered:
            try:
                workspace = arcpy.Describe(parameters[2]).path
                parameters[3].value = os.path.join(workspace, "catchment_ras")
            except AttributeError:
                parameters[2].setErrorMessage("{0} does not exist".format(parameters[2]))

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        pass


    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        in_catchment = parameters[0].valueAsText
        streamID = parameters[1].valueAsText
        in_hand_raster = parameters[2].valueAsText
        out_catchment_ras = parameters[3].valueAsText

        # the output catchment raster has exactly the same cell size, extent, and coordinate system as the HAND raster
        arcpy.env.cellSize = in_hand_raster
        arcpy.env.extent = in_hand_raster
        arcpy.env.outputCoordinateSystem = in_hand_raster

        arcpy.PolygonToRaster_conversion(in_catchment, streamID, out_catchment_ras)

        arcpy.ResetEnvironments()

        return




