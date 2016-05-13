'''-------------------------------------------------------------------------------
 Tool Name:   CreateHANDMosaicDataset
 Source Name: CreateHANDMosaicDataset.py
 Version:     ArcGIS 10.2
 License:	  Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Create a mosaic dataset and add HAND raster for multiple times to
                the mosaic dataset.
 History:     Initial coding - 05/13/2016, version 0.0
 Updated:
-------------------------------------------------------------------------------'''
import os
import arcpy
import numpy as NUM
import netCDF4 as NET
import datetime

class CreateHANDMosaicDataset(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create HAND Mosaic Dataset"
        self.description = "Create a mosaic dataset and add HAND raster to it for \
                            the same number of times as the number of time steps \
                            of RAPID discharge forecast"
##        self.vars_oi = ["COMID", "Qout"]
##        self.dims_oi = ["Time", "COMID"]
##        self.fields_oi = ["Time", "COMID", "Qout", "TimeValue"]
##        self.errorMessages = ["Missing Variable {0}",
##                              "Missing Dimension {0} of Variable {1}"]
        self.canRunInBackground = True
        self.category = "Postprocessing"


    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_output_location",
                                 displayName = "Output Location",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEWorkspace")

        param1 = arcpy.Parameter(name = "in_mosaic_dataset_name",
                                 displayName = "Mosaic Dataset Name",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")

        param2 = arcpy.Parameter(name = "in_HAND_raster_dataset",
                                 displayName = "HAND Raster Dataset",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DERasterDataset")

        param3 = arcpy.Parameter(name = "out_mosaic_dataset",
								displayName = "Output Mosaic Dataset",
								direction = "Output",
								parameterType = "Derived",
								datatype = "DEMosaicDataset")


        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
##        if parameters[4] is not None:
##            (dirnm, basenm) = os.path.split(parameters[4].valueAsText)
##            parameters[4].value = os.path.join(dirnm, "WaterLevel_Table")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

##        if parameters[0].altered:
##            in_nc = parameters[0].valueAsText
##            try:
##                data_nc = NET.Dataset(in_nc)
##                data_nc.close()
##            except Exception as e:
##                parameters[0].setErrorMessage(e.message)

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        out_fgdb = parameters[0].valueAsText
        md_name = parameters[1].valueAsText
        hand_raster = parameters[2].valueAsText


##        # validate the netCDF dataset
##        self.validateNC(in_nc, messages)
##
##        # create flat table based on the netcdf data file
##        self.createFlatTable(in_nc, out_flat_table)
##
##        # add and calculate TimeValue field
##        self.calculateTimeField(out_flat_table, start_datetime, time_interval)
##
##        # add attribute indices for COMID and TimeValue
##        arcpy.AddIndex_management(out_flat_table, self.fields_oi[1], self.fields_oi[1])
##        arcpy.AddIndex_management(out_flat_table, self.fields_oi[3], self.fields_oi[3])
##
##        # create unique ID table if user defined
##        arcpy.AddMessage("unique ID table: {0}".format(out_uniqueID_table))
##        if out_uniqueID_table is not None:
##            self.createUniqueIDTable(in_nc, out_uniqueID_table)


        return