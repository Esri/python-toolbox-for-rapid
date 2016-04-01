'''-------------------------------------------------------------------------------
 Tool Name:   CreateDischargeTable
 Source Name: CreateDischargeTable.py
 Version:     ArcGIS 10.3
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Create a RAPID discharge table using stream ID and time from RAPID
              discharge file as row dimensions.
 History:     Initial coding - 03/25/2015, version 1.0
 Updated:     Version 1.0, 10/30/2015, handle the situations of different Uppercase
              /Lowercase of variable or dimension names, and various sequences of
              the dimensions of Qout. Still have a bug in creating UniqueID table.
-------------------------------------------------------------------------------'''
import os
import arcpy
import numpy as NUM
import netCDF4 as NET
import datetime

class CreateDischargeTable(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Discharge Table"
        self.description = "Create a RAPID discharge table in a file geodatabase \
                            or SQL server geodatabase using stream ID and time \
                            from RAPID discharge file as row dimensions of the table"
        self.vars_oi = ["COMID", "Qout"]
        self.dims_oi = ["Time", "COMID"]
        self.fields_oi = ["Time", "COMID", "Qout", "TimeValue"]
        self.errorMessages = ["Missing Variable {0}",
                              "Missing Dimension {0} of Variable {1}"]
        self.canRunInBackground = False
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

    def createFlatTable(self, in_nc, out_table):
        """Create discharge table"""
        # obtain numpy array from the netCDF data
        data_nc = NET.Dataset(in_nc)
        comid = data_nc.variables[self.vars_oi[0]][:]
        qout = data_nc.variables[self.vars_oi[1]][:]


        #time_size = qout.shape[0]
        time_size = len(data_nc.dimensions[self.dims_oi[0]])  # to adapt to the changes of Qout dimensions
        #comid_size = qout.shape[1]
        comid_size = len(data_nc.dimensions[self.dims_oi[1]]) # to adapt to the changes of Qout dimensions
        total_size = time_size * comid_size

        qout_arr = qout.reshape(total_size, 1)
        time_arr = NUM.repeat(NUM.arange(1,time_size+1), comid_size)
        time_arr = time_arr.reshape(total_size, 1)
        comid_arr = NUM.tile(comid, time_size)
        comid_arr = comid_arr.reshape(total_size, 1)
        data_table = NUM.hstack((time_arr, comid_arr, qout_arr))

        # convert to numpy structured array
        str_arr = NUM.core.records.fromarrays(data_table.transpose(),
                    NUM.dtype([(self.fields_oi[0], NUM.int32), (self.fields_oi[1], NUM.int32), (self.fields_oi[2], NUM.float32)]))

        data_nc.close()

        # numpy structured array to table
        arcpy.da.NumPyArrayToTable(str_arr, out_table)

        return

    def createUniqueIDTable(self, in_nc, out_table):
        """Create a table of unique stream IDs"""
        data_nc = NET.Dataset(in_nc)
        comid_arr = data_nc.variables[self.vars_oi[0]][:]
        comid_size = len(comid_arr)
        comid_arr = comid_arr.reshape(comid_size, 1)
        arcpy.AddMessage(comid_arr.transpose())
        arcpy.AddMessage(self.vars_oi[0])

        #convert to numpy structured array
        str_arr = NUM.core.records.fromarrays(comid_arr.transpose(), NUM.dtype([(self.vars_oi[0], NUM.int32)]))

        # numpy structured array to table
        arcpy.da.NumPyArrayToTable(str_arr, out_table)

        data_nc.close()

        return


    def calculateTimeField(self, out_table, start_datetime, time_interval):
        """Add & calculate TimeValue field: scripts adapted from TimeTools.pyt developed by N. Noman"""
        timeIndexFieldName = self.fields_oi[0]
        timeValueFieldName = self.fields_oi[3]
        #Add TimeValue field
        arcpy.AddField_management(out_table, timeValueFieldName, "DATE", "", "", "", timeValueFieldName, "NULLABLE")
        #Calculate TimeValue field
        expression = "CalcTimeValue(!" + timeIndexFieldName + "!, '" + start_datetime + "', " + time_interval + ")"
        codeBlock = """def CalcTimeValue(timestep, sdatestr, dt):
            if (":" in sdatestr):
                sdate = datetime.datetime.strptime(sdatestr, '%m/%d/%Y %I:%M:%S %p')
            else:
                sdate = datetime.datetime.strptime(sdatestr, '%m/%d/%Y')
            tv = sdate + datetime.timedelta(hours=(timestep - 1) * dt)
            return tv"""

        arcpy.AddMessage("Calculating " + timeValueFieldName + "...")
        arcpy.CalculateField_management(out_table, timeValueFieldName, expression, "PYTHON_9.3", codeBlock)

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

        param3 = arcpy.Parameter(name = "out_discharge_table",
                                 displayName = "Output Discharge Table",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DETable")

        param4 = arcpy.Parameter(name = "out_unique_ID_table",
                                 displayName = "Output Unique ID Table",
                                 direction = "Output",
                                 parameterType = "Optional",
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
        if parameters[3] is not None:
            (dirnm, basenm) = os.path.split(parameters[3].valueAsText)
            parameters[3].value = os.path.join(dirnm, "Discharge_Table")

##        if parameters[4] is not None:
##            (dirnm, basenm) = os.path.split(parameters[3].valueAsText)
##            parameters[4].value = os.path.join(dirnm, "UniqueID_Table")

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
        out_flat_table = parameters[3].valueAsText
        out_uniqueID_table = parameters[4].valueAsText

        # validate the netCDF dataset
        self.validateNC(in_nc, messages)

        # create flat table based on the netcdf data file
        self.createFlatTable(in_nc, out_flat_table)

        # add and calculate TimeValue field
        self.calculateTimeField(out_flat_table, start_datetime, time_interval)

        # add attribute indices for COMID and TimeValue
        arcpy.AddIndex_management(out_flat_table, self.fields_oi[1], self.fields_oi[1])
        arcpy.AddIndex_management(out_flat_table, self.fields_oi[3], self.fields_oi[3])

        # create unique ID table if user defined
        arcpy.AddMessage("unique ID table: {0}".format(out_uniqueID_table))
        if out_uniqueID_table is not None:
            self.createUniqueIDTable(in_nc, out_uniqueID_table)


        return