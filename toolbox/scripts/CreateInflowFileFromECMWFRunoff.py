'''-------------------------------------------------------------------------------
 Tool Name:   CreateInflowFileFromECMWFRunoff
 Source Name: CreateInflowFileFromECMWFRunoff.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Creates RAPID inflow file based on the WRF_Hydro land model output
              and the weight table previously created.
 History:     Initial coding - 10/21/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014, modified names of tool and parameters
              Version 1.0, 10/28/2014, added data validation
              Version 1.0, 10/30/2014, initial version completed
              Version 1.1, 11/05/2014, modified the algorithm for extracting runoff
                variable from the netcdf dataset to improve computation efficiency
              Version 1.2, 02/03/2015, bug fixing - output netcdf3-classic instead
                of netcdf4 as the format of RAPID inflow file
              Version 1.2, 02/03/2015, bug fixing - calculate inflow assuming that
                ECMWF runoff data is cumulative instead of incremental through time
              Version 1.3, 02/18/2015, tool redesign - input drainage line features
                and compute RAPID inflow in the ascending order of drainag line ID
              Version 1.3, 02/18/2015, use 'HydroID' as one of the dimension names
                of m3_riv in the output RAPID inflow file
              Version 1.3, 02/20/2015 Enhancement - Added error handling for message
                updating of input drainage line features and output .csv weight table
              Version 1.3, 04/20/2015 Bug fixing - "HydroID", "NextDownID" (case insensitive) as
                the required field names in the input drainage line feature class
              Version 1.4, 04/27/2015 Bug fixing (false zero inflows)- To deal with
                the first several rows of records in the weight table don't correspond
                to any drainage line features (e.g. sink polygon as in Region 12 catchment)
              Version 1.4, 05/29/2015 Bug fixing: the pointer of weight table goes out of range
              Version 2.0, 06/09/2015 tool redesign - remove input drainage line features and
                compute RAPID inflow based on the streamIDs in the weight table given that the
                Create Weight Table tool has already taken care of the mismatch between streamIDs
                in the drainage line feature class and the catchment feature class.
              Version 2.0, 06/10/2015, use streamID in the weight table as the dimension name of
                m3_riv in the output RAPID inflow file

-------------------------------------------------------------------------------'''
import os
import arcpy
import netCDF4 as NET
import numpy as NUM
import csv

class CreateInflowFileFromECMWFRunoff(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Inflow File From ECMWF Runoff"
        self.description = ("Creates RAPID NetCDF input of water inflow " +
                       "based on ECMWF runoff results and previously created weight table.")
        self.canRunInBackground = False
        self.header_wt = ['StreamID', 'area_sqm', 'lon_index', 'lat_index', 'npoints', 'weight', 'Lon', 'Lat']
        self.dims_oi = ['lon', 'lat', 'time']
        self.vars_oi = ["lon", "lat", "time", "RO"]
        self.length_time = {"LowRes": 61, "HighRes": 125}
        self.length_time_opt = {"LowRes": 61, "HighRes-1hr": 91, "HighRes-3hr": 49, "HighRes-6hr": 41}
        self.errorMessages = ["Missing Variable 'time'",
                              "Incorrect dimensions in the input ECMWF runoff file.",
                              "Incorrect variables in the input ECMWF runoff file.",
                              "Incorrect time variable in the input ECMWF runoff file",
                              "Incorrect number of columns in the weight table",
                              "No or incorrect header in the weight table",
                              "Incorrect sequence of rows in the weight table"]
        self.category = "Preprocessing"


    def dataValidation(self, in_nc, messages):
        """Check the necessary dimensions and variables in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)

        dims = data_nc.dimensions.keys()
        if dims != self.dims_oi:
            messages.addErrorMessage(self.errorMessages[1])
            raise arcpy.ExecuteError

        vars = data_nc.variables.keys()
        if vars != self.vars_oi:
            messages.addErrorMessage(self.errorMessages[2])
            raise arcpy.ExecuteError

        return


    def dataIdentify(self, in_nc):
        """Check if the data is Ensemble 1-51 (low resolution) or 52 (high resolution)"""
        data_nc = NET.Dataset(in_nc)
        name_time = self.vars_oi[2]
        time = data_nc.variables[name_time][:]
        diff = NUM.unique(NUM.diff(time))
        data_nc.close()
        time_interval_highres = NUM.array([1.0,3.0,6.0],dtype=float)
        time_interval_lowres = NUM.array([6.0],dtype=float)
        if (diff == time_interval_highres).all():
            return "HighRes"
        elif (diff == time_interval_lowres).all():
            return "LowRes"
        else:
            return None


    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_ECMWF_runoff_file",
                                 displayName = "Input ECMWF Runoff File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param1 = arcpy.Parameter(name = "in_weight_table",
                                 displayName = "Input Weight Table",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param2 = arcpy.Parameter(name = "out_inflow_file",
                                 displayName = "Output Inflow File",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param3 = arcpy.Parameter(name = "time_interval",
                                 displayName = "Time Interval",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "GPString")

        param3.filter.type = "ValueList"
        list_intervals = []
        param3.filter.list = list_intervals

        params = [param0, param1, param2, param3]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            in_nc = parameters[0].valueAsText
            try:
                data_nc = NET.Dataset(in_nc)
                name_time = self.vars_oi[2]
                time = data_nc.variables[name_time][:]
                diff = NUM.unique(NUM.diff(time))
                max_interval = diff.max()
                parameters[3].filter.list = [(str(int(each)) + "hr") for each in diff]
                if parameters[3].valueAsText is None:
                    parameters[3].value = str(int(max_interval)) + "hr"
                data_nc.close()
            except:
                pass

        if parameters[0].altered and parameters[1].altered:
            if parameters[2].valueAsText is not None:
                (dirnm, basenm) = os.path.split(parameters[2].valueAsText)
                if not basenm.endswith(".nc"):
                    parameters[2].value = os.path.join(dirnm, "{}.nc".format(basenm))

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if parameters[0].altered:
            in_nc = parameters[0].valueAsText
            try:
                data_nc = NET.Dataset(in_nc)
                name_time = self.vars_oi[2]
                time = data_nc.variables[name_time][:]
                data_nc.close()
            except:
                parameters[0].setErrorMessage(self.errorMessages[0])

        try:
            if parameters[1].altered:
                (dirnm, basenm) = os.path.split(parameters[1].valueAsText)
                if not basenm.endswith(".csv"):
                    parameters[1].setErrorMessage("The weight table must be in CSV format")
        except Exception as e:
            parameters[1].setErrorMessage(e.message)

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.env.overwriteOutput = True

        in_nc = parameters[0].valueAsText
        in_weight_table = parameters[1].valueAsText
        out_nc = parameters[2].valueAsText
        in_time_interval = parameters[3].valueAsText

        # Validate the netcdf dataset
        self.dataValidation(in_nc, messages)

        # identify if the input netcdf data is the High Resolution data with three different time intervals
        id_data = self.dataIdentify(in_nc)
        if id_data is None:
            messages.addErrorMessage(self.errorMessages[3])
            raise arcpy.ExecuteError

        ''' Read the netcdf dataset'''
        data_in_nc = NET.Dataset(in_nc)
        time = data_in_nc.variables[self.vars_oi[2]][:]

        # Check the size of time variable in the netcdf data
        if len(time) != self.length_time[id_data]:
            messages.addErrorMessage(self.errorMessages[3])
            raise arcpy.ExecuteError

        ''' Read .csv weight table '''
        arcpy.AddMessage("Reading the weight table...")
        dict_list = {self.header_wt[0]:[], self.header_wt[1]:[], self.header_wt[2]:[],
                     self.header_wt[3]:[], self.header_wt[4]:[], self.header_wt[5]:[],
                     self.header_wt[6]:[]}
        streamID = ""
        with open(in_weight_table, "rb") as csvfile:
            reader = csv.reader(csvfile)
            count = 0
            for row in reader:
                if count == 0:
                    #check number of columns in the weight table
                    if len(row) != len(self.header_wt):
                        messages.addErrorMessage(self.errorMessages[4])
                        raise arcpy.ExecuteError
                    # #check header
                    # if row[1:len(self.header_wt)] != self.header_wt[1:len(self.header_wt)]:
                    #     messages.addErrorMessage(self.errorMessages[5])
                    #     arcpy.ExecuteError
                    streamID = row[0]
                    count += 1
                else:
                    for i in range(0,7):
                       dict_list[self.header_wt[i]].append(row[i])
                    count += 1

        '''Calculate water inflows'''
        arcpy.AddMessage("Calculating water inflows...")

        # Obtain size information
        if id_data == "LowRes":
            size_time = self.length_time_opt["LowRes"]
        else:
            if in_time_interval == "1hr":
                size_time = self.length_time_opt["HighRes-1hr"]
            elif in_time_interval == "3hr":
                size_time = self.length_time_opt["HighRes-3hr"]
            else:
                size_time = self.length_time_opt["HighRes-6hr"]

        size_streamID = len(set(dict_list[self.header_wt[0]]))

        # Create output inflow netcdf data
        data_out_nc = NET.Dataset(out_nc, "w", format = "NETCDF3_CLASSIC")
        dim_Time = data_out_nc.createDimension('Time', size_time)
        dim_RiverID = data_out_nc.createDimension(streamID, size_streamID)
        var_m3_riv = data_out_nc.createVariable('m3_riv', 'f4', ('Time', streamID))
        data_temp = NUM.empty(shape = [size_time, size_streamID])


        lon_ind_all = [long(i) for i in dict_list[self.header_wt[2]]]
        lat_ind_all = [long(j) for j in dict_list[self.header_wt[3]]]

        # Obtain a subset of  runoff data based on the indices in the weight table
        min_lon_ind_all = min(lon_ind_all)
        max_lon_ind_all = max(lon_ind_all)
        min_lat_ind_all = min(lat_ind_all)
        max_lat_ind_all = max(lat_ind_all)


        data_subset_all = data_in_nc.variables[self.vars_oi[3]][:, min_lat_ind_all:max_lat_ind_all+1, min_lon_ind_all:max_lon_ind_all+1]
        len_time_subset_all = data_subset_all.shape[0]
        len_lat_subset_all = data_subset_all.shape[1]
        len_lon_subset_all = data_subset_all.shape[2]
        data_subset_all = data_subset_all.reshape(len_time_subset_all, (len_lat_subset_all * len_lon_subset_all))


        # compute new indices based on the data_subset_all
        index_new = []
        for r in range(0,count-1):
            ind_lat_orig = lat_ind_all[r]
            ind_lon_orig = lon_ind_all[r]
            index_new.append((ind_lat_orig - min_lat_ind_all)*len_lon_subset_all + (ind_lon_orig - min_lon_ind_all))

        # obtain a new subset of data
        data_subset_new = data_subset_all[:,index_new]
        pointer = 0
        # start compute inflow
        len_wt = len(dict_list[self.header_wt[0]])
        for s in range(0, size_streamID):
                    npoints = int(dict_list[self.header_wt[4]][pointer])
                    # Check if all npoints points correspond to the same streamID
                    if len(set(dict_list[self.header_wt[0]][pointer : (pointer + npoints)])) != 1:
                          messages.addErrorMessage(self.errorMessages[2])
                          arcpy.ExecuteError

                    area_sqm_npoints = [float(k) for k in dict_list[self.header_wt[1]][pointer : (pointer + npoints)]]
                    area_sqm_npoints = NUM.array(area_sqm_npoints)
                    area_sqm_npoints = area_sqm_npoints.reshape(1, npoints)
                    data_goal = data_subset_new[:, pointer:(pointer + npoints)]

                    ''''IMPORTANT NOTE: runoff variable in ECMWF dataset is cumulative instead of incremental through time'''
                    # For data with Low Resolution, there's only one time interval 6 hrs
                    if id_data == "LowRes":
                        #ro_stream = data_goal * area_sqm_npoints
                        ro_stream = NUM.concatenate([data_goal[0:1,],
                                        NUM.subtract(data_goal[1:,],data_goal[:-1,])]) * area_sqm_npoints

                    #For data with High Resolution, from Hour 0 to 90 (the first 91 time points) are of 1 hr time interval,
                    # then from Hour 90 to 144 (19 time points) are of 3 hour time interval, and from Hour 144 to 240 (15 time points)
                    # are of 6 hour time interval
                    else:
                        if in_time_interval == "1hr":
                            ro_stream = NUM.concatenate([data_goal[0:1,],
                                        NUM.subtract(data_goal[1:91,],data_goal[:90,])]) * area_sqm_npoints
                        elif in_time_interval == "3hr":
                            # Hour = 0 is a single data point
                            ro_3hr_a = data_goal[0:1,]
                            # calculate time series of 3 hr data from 1 hr data
                            ro_3hr_b = NUM.subtract(data_goal[3:91:3,],data_goal[:88:3,])
                            # get the time series of 3 hr data
                            ro_3hr_c = NUM.subtract(data_goal[91:109,], data_goal[90:108,])
                            # concatenate all time series
                            ro_stream = NUM.concatenate([ro_3hr_a, ro_3hr_b, ro_3hr_c]) * area_sqm_npoints
                        else: 
                            # in_time_interval is "6hr"
                            # Hour = 0 is a single data point
                            ro_6hr_a = data_goal[0:1,]
                            # calculate time series of 6 hr data from 1 hr data
                            ro_6hr_b = NUM.subtract(data_goal[6:91:6,], data_goal[:85:6,])
                            # calculate time series of 6 hr data from 3 hr data
                            ro_6hr_c = NUM.subtract(data_goal[92:109:2,], data_goal[90:107:2,])
                            # get the time series of 6 hr data
                            ro_6hr_d = NUM.subtract(data_goal[109:,], data_goal[108:124,])
                            # concatenate all time series
                            ro_stream = NUM.concatenate([ro_6hr_a, ro_6hr_b, ro_6hr_c, ro_6hr_d]) * area_sqm_npoints


                    data_temp[:,s] = ro_stream.sum(axis = 1)
                    pointer += npoints


        '''Write inflow data'''
        arcpy.AddMessage("Writing inflow data...")
        var_m3_riv[:] = data_temp
        # close the input and output netcdf datasets
        data_in_nc.close()
        data_out_nc.close()


        return
