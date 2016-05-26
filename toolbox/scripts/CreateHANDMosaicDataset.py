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
        self.fields_oi = ["TimeValue", "AuxQuery"]
##        self.errorMessages = ["Missing Variable {0}",
##                              "Missing Dimension {0} of Variable {1}"]
        self.canRunInBackground = True
        self.category = "Postprocessing for Flood Inundation"


    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name="in_output_location",
                                 displayName="Output Location",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="DEWorkspace")

        param1 = arcpy.Parameter(name="in_mosaic_dataset_name",
                                 displayName="Mosaic Dataset Name",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="GPString")

        param2 = arcpy.Parameter(name="in_HAND_raster_dataset",
                                 displayName="HAND Raster Dataset",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="DERasterDataset")

        param3 = arcpy.Parameter(name="start_date_time",
                                 displayName="Start Date and Time",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="GPDate")

        param4 = arcpy.Parameter(name="time_interval",
                                 displayName="Time Interval in Hour",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="GPDouble")

        param5 = arcpy.Parameter(name="number_of_time_steps",
                                 displayName="Number of Time Steps",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="GPLong")

        param6 = arcpy.Parameter(name="out_mosaic_dataset",
                                 displayName="Output Mosaic Dataset",
                                 direction="Output",
                                 parameterType="Derived",
                                 datatype="DEMosaicDataset")


        params = [param0, param1, param2, param3, param4, param5, param6]
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
        start_date_str = parameters[3].valueAsText
        time_interval = parameters[4].valueAsText
        n_timesteps = parameters[5].value

        sr = arcpy.Describe(hand_raster).spatialReference


        """Create the mosaic dataset"""
        arcpy.AddMessage("Creating mosaic dataset...")
        noband = "1"
        pixtype = "32_BIT_FLOAT"
        pdef = "NONE"
        wavelength = ""
        arcpy.CreateMosaicDataset_management(out_fgdb, md_name, sr, noband, pixtype, pdef, wavelength)


        """Add the dd raster to the mosaic dataset"""
        arcpy.AddMessage("Adding rasters to the mosaic dataset...")
        md_path = os.path.join(out_fgdb, md_name)
        rastype = "Raster Dataset"
        inpath = os.path.join(out_fgdb, hand_raster)
        updatecs = "UPDATE_CELL_SIZES"
        updatebnd = "UPDATE_BOUNDARY"
        updateovr = "NO_OVERVIEWS"
        maxlevel = "#"
        maxcs = "0"
        maxdim = "1500"
        spatialref = "#"
        inputdatafilter = "#"
        subfolder = "SUBFOLDERS"
        duplicate = "ALLOW_DUPLICATES"
        buildpy = "NO_PYRAMIDS"
        calcstats = "NO_STATISTICS"
        buildthumb = "NO_THUMBNAILS"
        comments = "#"
        forcesr = "NO_FORCE_SPATIAL_REFERENCE"
        eststats = "NO_STATISTICS"
        auxinputs = "#"

        for i in range(0,n_timesteps):
            arcpy.AddRastersToMosaicDataset_management(
                 md_path,  rastype, inpath, updatecs, updatebnd, updateovr,
                 maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
                 subfolder, duplicate, buildpy, calcstats,
                 buildthumb, comments, forcesr, eststats, auxinputs)


        """Add fields to the mosaic dataset and calculate their values"""
        arcpy.AddMessage("Adding and calculating fields...")
        # Add and calculate time field
        fd_name_TimeValue = self.fields_oi[0]
        field_type = "DATE"
        fd_name_TimeIndex = "OBJECTID"
        arcpy.AddField_management(md_path, fd_name_TimeValue, field_type)
        expression = "CalcTimeValue(!" + fd_name_TimeIndex + "!, '" + start_date_str + "', " + time_interval + ")"
        codeBlock = """def CalcTimeValue(timestep, sdatestr, dt):
            if (":" in sdatestr):
                sdate = datetime.datetime.strptime(sdatestr, '%m/%d/%Y %I:%M:%S %p')
            else:
                sdate = datetime.datetime.strptime(sdatestr, '%m/%d/%Y')
            tv = sdate + datetime.timedelta(hours=(timestep - 1) * dt)
            return tv"""
        arcpy.CalculateField_management(md_path, fd_name_TimeValue, expression, "PYTHON_9.3", codeBlock)

        # Add and calculate an auxillary query field
        fd_name_AuxQuery = self.fields_oi[1]
        field_type = "TEXT"
        field_length = "100"
        arcpy.AddField_management(md_path, fd_name_AuxQuery, field_type, field_length)

        arcpy.CalculateField_management(md_path, fd_name_AuxQuery,
                                    expression=""""TimeValue = date '{}'".format( !TimeValue!)""",
                                    expression_type="PYTHON_9.3")

        # Add attribute index to the TimeValue field
        arcpy.AddIndex_management(md_path, fd_name_TimeValue, fd_name_TimeValue)

        print("Enabling time...")
        # Edit mosaic dataset properties to enable time
        use_time = "ENABLED"
        start_time_field = "TimeValue"
        end_time_field = "TimeValue"
        arcpy.SetMosaicDatasetProperties_management(md_path, use_time=use_time, start_time_field=start_time_field,
                                                    end_time_field=end_time_field)

        return