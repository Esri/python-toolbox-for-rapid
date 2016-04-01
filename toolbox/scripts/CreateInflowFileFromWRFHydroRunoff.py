'''-------------------------------------------------------------------------------
 Tool Name:   CreateInflowFileFromWRFHydroRunoff
 Source Name: CreateInflowFileFromWRFHydroRunoff.py
 Version:     ArcGIS 10.3
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Creates RAPID inflow file based on the WRF_Hydro land model output
              and the weight table previously created.
 History:     Initial coding - 10/17/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014, modified names of tool and parameters
              Version 1.0, 10/28/2014, added data validation
              Version 1.1, 11/05/2014, modified the algorithm for extracting runoff
                variable from the netcdf dataset to improve computation efficiency
              Version 1.1, 02/03/2015, bug fixing - output netcdf3-classic instead
                of netcdf4 as the format of RAPID inflow file
              Version 1.2, 02/17/2015, tool redesign - input drainage line features
                and compute RAPID inflow in the ascending order of drainag line ID
              Version 1.2, 02/17/2015, bug fixing - included UGDRNOFF as a component
                of RAPID inflow; calculated inflow assuming that WRF-Hydro runoff variables
                are cumulative instead of incremental through time; use 'HydroID' as one of
                the dimension names of m3_riv in the output RAPID inflow file
              Version 1.2, 04/20/2015 Bug fixing - "HydroID", "NextDownID" (case insensitive) as
                the required field names in the input drainage line feature class
              Version 1.3, 04/27/2015 Bug fixing (false zero inflows)- To deal with
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


class CreateInflowFileFromWRFHydroRunoff(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Inflow File From WRF-Hydro Runoff"
        self.description = ("Creates RAPID NetCDF input of water inflow based on the WRF-Hydro land" +
                            " model output and the weight table previously created")
        self.canRunInBackground = False
        self.header_wt = ['StreamID', 'area_sqm', 'west_east', 'south_north',
                                  'npoints', 'weight', 'Lon', 'Lat', 'x', 'y']
        # According to David Gochis, underground runoff is "a major fraction of total river flow in most places"
        self.vars_oi = ['SFCRNOFF', 'INTRFLOW','UGDRNOFF']
        self.dims_var = ('Time', 'south_north', 'west_east')
        self.errorMessages = ["Incorrect number of columns in the weight table",
                              "No or incorrect header in the weight table",
                              "Incorrect sequence of rows in the weight table",
                              "Missing variable: {0} in the input WRF-Hydro runoff file",
                              "Incorrect dimensions of variable {0} in the input WRF-Hydro runoff file"]
        self.category = "Preprocessing"

    def dataValidation(self, in_nc, messages):
        """Check the necessary dimensions and variables in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)
        vars = data_nc.variables.keys()
        for each in self.vars_oi:
            if each not in vars:
                messages.addErrorMessage(self.errorMessages[3].format(each))
                raise arcpy.ExecuteError
            else:
                dims = data_nc.variables[each].dimensions
                if self.dims_var != dims:
                    messages.addErrorMessage(self.errorMessages[4].format(each))
                    raise arcpy.ExecuteError

        data_nc.close()

        return

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_WRF_Hydro_runoff_file",
                                 displayName = "Input WRF-Hydro Runoff File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

##        param1 = arcpy.Parameter(name = 'in_drainage_line_features',
##                                 displayName = 'Input Drainage Line Features',
##                                 direction = 'Input',
##                                 parameterType = 'Required',
##                                 datatype = 'GPFeatureLayer')
##        param1.filter.list = ['Polyline']

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

        params = [param0, param1, param2]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
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
                data_nc.close()
            except Exception as e:
                parameters[0].setErrorMessage(e.message)

##        if parameters[1].altered:
##            field_names = []
##            fields = arcpy.ListFields(parameters[1].valueAsText)
##            for field in fields:
##                field_names.append(field.baseName.upper())
##            if not ("HYDROID" in field_names and "NEXTDOWNID" in field_names):
##                parameters[1].setErrorMessage("Input Drainage Line must contain HydroID and NextDownID.")

        if parameters[1].altered:
            (dirnm, basenm) = os.path.split(parameters[1].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[1].setErrorMessage("The weight table must be in CSV format")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.env.overwriteOutput = True

        in_nc = parameters[0].valueAsText
##        in_drainage_line = parameters[1].valueAsText
        in_weight_table = parameters[1].valueAsText

        out_nc = parameters[2].valueAsText

        # Validate the netcdf dataset
        self.dataValidation(in_nc, messages)

##        '''Get all HydroIDs from the drainage line feature class'''
##        hydroID = arcpy.da.FeatureClassToNumPyArray(in_drainage_line, ["HydroID"])
##        hydroID = hydroID['HydroID']
##        hydroID = NUM.sort(hydroID)  # sort HydroIDs in ascending order


        '''Read .csv weight table'''
        arcpy.AddMessage("Reading the weight table...")
        dict_list = {self.header_wt[0]:[], self.header_wt[1]:[], self.header_wt[2]:[],
                     self.header_wt[3]:[], self.header_wt[4]:[]}
        streamID = ""
        with open(in_weight_table, "rb") as csvfile:
            reader = csv.reader(csvfile)
            count = 0
            for row in reader:
                if count == 0:
                    #check number of columns in the weight table
                    if len(row) != len(self.header_wt):
                        messages.addErrorMessage(self.errorMessages[0])
                        raise arcpy.ExecuteError
                    #check header
                    if row[1:len(self.header_wt)] != self.header_wt[1:len(self.header_wt)]:
                        messages.addErrorMessage(self.errorMessages[1])
                        arcpy.ExecuteError
                    streamID = row[0]
                    count += 1
                else:
                    for i in range(0,5):
                       dict_list[self.header_wt[i]].append(row[i])
                    count += 1

        '''Calculate water inflows'''
        arcpy.AddMessage("Calculating water inflows...")
        data_in_nc = NET.Dataset(in_nc)

        # Obtain size information
        size_time = data_in_nc.variables[self.vars_oi[0]].shape[0]
        size_streamID = len(set(dict_list[self.header_wt[0]]))
##        size_streamID = len(hydroID)

        # Create output inflow netcdf data
        # data_out_nc = NET.Dataset(out_nc, "w") # by default format = "NETCDF4"
        data_out_nc = NET.Dataset(out_nc, "w", format = "NETCDF3_CLASSIC")
        dim_Time = data_out_nc.createDimension('Time', size_time)
        dim_RiverID = data_out_nc.createDimension(streamID, size_streamID)
        var_m3_riv = data_out_nc.createVariable('m3_riv', 'f4', ('Time', streamID))
        data_temp = NUM.empty(shape = [size_time, size_streamID])


        we_ind_all = [long(i) for i in dict_list[self.header_wt[2]]]
        sn_ind_all = [long(j) for j in dict_list[self.header_wt[3]]]

        # Obtain a subset of  runoff data based on the indices in the weight table
        min_we_ind_all = min(we_ind_all)
        max_we_ind_all = max(we_ind_all)
        min_sn_ind_all = min(sn_ind_all)
        max_sn_ind_all = max(sn_ind_all)


        data_subset_all = data_in_nc.variables[self.vars_oi[0]][:,min_sn_ind_all:max_sn_ind_all+1, min_we_ind_all:max_we_ind_all+1]/1000 \
                        + data_in_nc.variables[self.vars_oi[1]][:,min_sn_ind_all:max_sn_ind_all+1, min_we_ind_all:max_we_ind_all+1]/1000 \
                        + data_in_nc.variables[self.vars_oi[2]][:,min_sn_ind_all:max_sn_ind_all+1, min_we_ind_all:max_we_ind_all+1]/1000
        len_time_subset_all = data_subset_all.shape[0]
        len_sn_subset_all = data_subset_all.shape[1]
        len_we_subset_all = data_subset_all.shape[2]
        data_subset_all = data_subset_all.reshape(len_time_subset_all, (len_sn_subset_all * len_we_subset_all))


        # compute new indices based on the data_subset_all
        index_new = []
        for r in range(0,count-1):
            ind_sn_orig = sn_ind_all[r]
            ind_we_orig = we_ind_all[r]
            index_new.append((ind_sn_orig - min_sn_ind_all)*len_we_subset_all + (ind_we_orig - min_we_ind_all))

        # obtain a new subset of data
        data_subset_new = data_subset_all[:,index_new]


        # start compute inflow
        len_wt = len(dict_list[self.header_wt[0]])
        pointer = 0
        for s in range(0, size_streamID):
##            # Check if the stream reach segment has corresponding catchment
##            # Compare the ID values since streamID of the weight table is also in ascending order
##            '''Skip the rows in the weight table if no corresponding drainage line features'''
##            if pointer < len_wt:
##                while int(dict_list[self.header_wt[0]][pointer]) < int(hydroID[s]):
##                    npoints = int(dict_list[self.header_wt[4]][pointer])
##                    pointer += npoints
##
##                if pointer < len_wt and int(dict_list[self.header_wt[0]][pointer]) == int(hydroID[s]):
                    npoints = int(dict_list[self.header_wt[4]][pointer])
                    # Check if all npoints points correspond to the same streamID
                    if len(set(dict_list[self.header_wt[0]][pointer : (pointer + npoints)])) != 1:
                          messages.addErrorMessage(self.errorMessages[2])
                          arcpy.ExecuteError

                    area_sqm_npoints = [float(k) for k in dict_list[self.header_wt[1]][pointer : (pointer + npoints)]]
                    area_sqm_npoints = NUM.array(area_sqm_npoints)
                    area_sqm_npoints = area_sqm_npoints.reshape(1, npoints)
                    data_goal = data_subset_new[:, pointer:(pointer + npoints)]

                    ''''IMPORTANT NOTE: runoff variables in WRF-Hydro dataset is cumulative through time'''
                    rnoff_stream = NUM.concatenate([data_goal[0:1,],
                                    NUM.subtract(data_goal[1:,],data_goal[:-1,])]) * area_sqm_npoints
                    data_temp[:,s] = rnoff_stream.sum(axis = 1)

                    pointer += npoints
##                else:
##                    data_temp[:,s] = 0.0
##            else:
##                data_temp[:,s] = 0.0


        '''Write inflow data'''
        arcpy.AddMessage("Writing inflow data...")
        var_m3_riv[:] = data_temp
        # close the input and output netcdf datasets
        data_in_nc.close()
        data_out_nc.close()


        return