'''-------------------------------------------------------------------------------
 Tool Name:   CreateWaterLevelTable
 Source Name: CreateWaterLevelTable.py
 Version:     ArcGIS 10.2
 License:	  Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Create a water level table from RAPID discharge output and rating curves.
 History:     Initial coding - 05/13/2016, version 0.0
 Updated:
-------------------------------------------------------------------------------'''
import os
import arcpy
import numpy as NUM
import netCDF4 as NET
import datetime

class CreateWaterLevelTable(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Water Level Table"
        self.description = "Create a water level table in a file geodatabase \
                            or SQL server geodatabase using stream ID and time \
                            from RAPID discharge file as row dimensions of the table"
        self.vars_oi = ["COMID", "Qout"]
        self.dims_oi = ["Time", "COMID"]
        self.fields_oi = ["Time", "COMID", "Qout", "TimeValue"]
        self.errorMessages = ["Missing Variable {0}",
                              "Missing Dimension {0} of Variable {1}"]
        self.canRunInBackground = True
        self.category = "Postprocessing"

    def validateNC(self, in_nc, messages):
        """Check the necessary variables and dimensions in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)

        vars = data_nc.variables.keys()
        vars_upper = []
        for eachvar in vars:
            vars_upper.append(eachvar.upper())

        counter = 0
        for eachvar_oi in self.vars_oi:
            try:
                ind = vars_upper.index(eachvar_oi.upper())
                # Update the Uppercase/Lowercase of the names of vars of interests
                self.vars_oi[counter] = vars[ind]
                counter += 1
            except RuntimeError:
                messages.addErrorMessage(self.errorMessages[0].format(eachvar_oi))
                raise arcpy.ExecuteError

        dims = data_nc.variables[self.vars_oi[1]].dimensions
        dims_upper = []
        for eachdim in dims:
            dims_upper.append(eachdim.upper())

        counter = 0
        for eachdim_oi in self.dims_oi:
            try:
                ind = dims_upper.index(eachdim_oi.upper())
                # Update the Uppercase/Lowercase of the names of dims of interests
                self.dims_oi[counter] = dims[ind]
                counter += 1
            except RuntimeError:
                messages.addErrorMessage(self.errorMessages[1].format(eachdim_oi, self.vars_oi[1]))
                raise arcpy.ExecuteError

        data_nc.close()

        return

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_RAPID_discharge_file",
                                 displayName = "Input RAPID Discharge File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param1 = arcpy.Parameter(name = "in_start_date_time",
                                 displayName = "Start Date and Time",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPDate")

        param2 = arcpy.Parameter(name = "in_time_interval",
                                 displayName = "Time Interval in Hour",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPDouble")

        param3 = arcpy.Parameter(name = "in_rating_curves_directory",
								displayName = "Rating Curves Folder",
								direction = "Input",
								parameterType = "Required",
								datatype = "DEFolder")

        param4 = arcpy.Parameter(name = "out_water_level_table",
                                 displayName = "Output Water Level Table",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DETable")



        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[4] is not None:
            (dirnm, basenm) = os.path.split(parameters[4].valueAsText)
            parameters[4].value = os.path.join(dirnm, "WaterLevel_Table")

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if parameters[0].altered:
            in_nc = parameters[0].valueAsText
            try:
                data_nc = NET.Dataset(in_nc)
                data_nc.close()
            except Exception as e:
                parameters[0].setErrorMessage(e.message)

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        in_nc = parameters[0].valueAsText
        start_datetime = parameters[1].valueAsText
        time_interval = parameters[2].valueAsText
        in_rc_folder = parameters[3].valueAsText
        out_uniqueID_table = parameters[4].valueAsText

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