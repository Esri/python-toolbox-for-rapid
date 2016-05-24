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
from numpy.lib.recfunctions import append_fields
import netCDF4 as NET
import datetime
import pandas as PD

class CreateWaterLevelTable(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Water Level Table"
        self.description = "Create a water level table in a file geodatabase \
                            or SQL server geodatabase using stream ID and time \
                            from RAPID discharge file as row dimensions of the table"
        self.vars_oi = ["COMID", "Qout"]
        self.dims_oi = ["TIME", "COMID"]
        self.fields_oi = ["TimeValue", "COMID", "H_ft","H_m", "Q_cfs", "Q_cumecs"]
        self.rc_fields_oi = [" Flowrate(ft^3/s)"," Height(ft)"]
        self.errorMessages = ["Missing Variable {0}",
                              "Missing Dimension {0} of Variable {1}"]
        self.canRunInBackground = True
        self.category = "Postprocessing for Flood Inundation"

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

    def createArray(self, in_nc, in_start_time, in_time_interval, dir_rc):
        """create a numpy structured array for the table"""
        data_nc = NET.Dataset(in_nc,"r")
        comid = data_nc.variables[self.vars_oi[0]][:]
        # calculate # of time steps instead of getting the size infor from Time variable in case it's not included in the nc
        n_timesteps = data_nc.variables[self.vars_oi[1]].size / comid.size

        # calculate time
        if (":" in in_start_time):
                start_time = datetime.datetime.strptime(in_start_time, '%m/%d/%Y %I:%M:%S %p')
        else:
                start_time = datetime.datetime.strptime(in_start_time, '%m/%d/%Y')
        time = NUM.empty(n_timesteps, dtype=[(self.fields_oi[0], '<M8[us]')])
        for i in range(0,n_timesteps):
            time[i][self.fields_oi[0]] = start_time + datetime.timedelta(hours=float(in_time_interval)) * i

        # comid with rating curve
        comid_w_rc = []
        files = []
        for file in os.listdir(dir_rc):
            if file.endswith(".csv"):
                files.append(file)
                filename = file.split(" ")
                comid_w_rc.append(long(filename[0]))

        comid_w_rc = NUM.array(comid_w_rc)

        # find the indexes of comids  that have rating curves in the nc file
        sorter = NUM.argsort(comid)
        index_comid_w_rc = sorter[NUM.searchsorted(comid, comid_w_rc, sorter=sorter)]

        # get the qout subset (corresponding to COMIDs that have rating curves) from nc file
        dims = data_nc.variables[self.vars_oi[1]].dimensions
        if len(dims) == 2 and dims[1] == self.vars_oi[0]:
            qout_w_rc = data_nc.variables[self.vars_oi[1]][:,index_comid_w_rc]   #assumming Qout(Time, COMID)
        elif len(dims) == 2 and dims[0] ==self.vars_oi[0]:
            qout_w_rc = data_nc.variables[self.vars_oi[1]][index_comid_w_rc,:]   #assuming Qout(COMID, Time)
            qout_w_rc = NUM.swapaxes(qout_w_rc, 0, 1)
        else:
            arcpy.AddMessage("Qout variable has incorrect dimensions")
            raise arcpy.ExecuteError

        # prepare the arrays
        time_arr = NUM.tile(time, len(comid_w_rc))
        comid_w_rc_arr = NUM.repeat(comid_w_rc, len(time))

        qout_cumecs_w_rc_arr = NUM.ones([len(comid_w_rc)*len(time)])*-9999.0
        qout_cfs_w_rc_arr = NUM.ones([len(comid_w_rc)*len(time)])*-9999.0
        # array of height in feet and meter
        height_arr = NUM.ones([len(comid_w_rc)*len(time), 2])*-9999.0

        counter = 0
        for each in comid_w_rc:
            # hardcoded here for rating curve file name!!!!!
            rc_file = str(each) + " " + "Rating Curve.csv"
            rc_file = os.path.join(dir_rc, rc_file)
            df = PD.read_csv(rc_file)

            # calculate qout of the counter -th comid from m^3 to ft^3
            qout_cumecs_w_rc_arr[counter*n_timesteps:(counter*n_timesteps+n_timesteps)] = qout_w_rc[:,counter] #assumming Qout(COMID, Time)
            qout_in_cft = qout_w_rc[:,counter] * 35.3147     #assumming Qout(COMID, Time)
            qout_cfs_w_rc_arr[counter*n_timesteps:(counter*n_timesteps+n_timesteps)] = qout_in_cft
            # get the flowrate in ft^3/s from the rating curve data
            flowrate = NUM.array(df[self.rc_fields_oi[0]])
            nbr_rc = len(flowrate)
            flowrate = NUM.reshape(flowrate,(nbr_rc,1))
            if nbr_rc > 0: # if the rating curve data is not empty
                # form an array with qout (in ft^3), each row is qout time series, and repeated in # of flowrate records
                qout_in_cft_rep = NUM.vstack([qout_in_cft]*nbr_rc)
                # calculate the absolute difference between qout and flowrates
                diff = NUM.absolute(qout_in_cft_rep - flowrate)
                # identify the index of minimum difference within the flowrates recrods
                index_min = NUM.argmin(diff,axis=0)
                height = NUM.array(df[self.rc_fields_oi[1]])
                height = height[index_min]
                height_arr[counter*n_timesteps:(counter*n_timesteps+n_timesteps),0] = height
                height_arr[counter*n_timesteps:(counter*n_timesteps+n_timesteps),1] = height / 3.28084
            else:
                arcpy.AddMessage("empty rating curve table at {0}".format(each))

            counter +=1

        # Contruct the numpy structured array for the table
        out_nparr = time_arr
        out_nparr = append_fields(out_nparr, self.fields_oi[1], comid_w_rc_arr)
        out_nparr = append_fields(out_nparr, self.fields_oi[2], height_arr[:,0])
        out_nparr = append_fields(out_nparr, self.fields_oi[3], height_arr[:,1])
        out_nparr = append_fields(out_nparr, self.fields_oi[4], qout_cfs_w_rc_arr)
        out_nparr = append_fields(out_nparr, self.fields_oi[5], qout_cumecs_w_rc_arr)
        out_nparr.sort(order=[self.fields_oi[1],self.fields_oi[0]])

        return out_nparr


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
        in_start_datetime = parameters[1].valueAsText
        in_time_interval = parameters[2].valueAsText
        in_rc_folder = parameters[3].valueAsText
        out_table = parameters[4].valueAsText

        # validate the netCDF dataset
        # self.validateNC(in_nc, messages)

        # create a numpy structured array for the output table"
        arr = self.createArray(in_nc,in_start_datetime,in_time_interval,in_rc_folder)

        # numpy array to table
        arcpy.da.NumPyArrayToTable(arr, out_table)

        # add attribute indexes for TimeValue and COMID
        arcpy.AddIndex_management(out_table, self.fields_oi[0], self.fields_oi[0])
        arcpy.AddIndex_management(out_table, self.fields_oi[1], self.fields_oi[1])


        return