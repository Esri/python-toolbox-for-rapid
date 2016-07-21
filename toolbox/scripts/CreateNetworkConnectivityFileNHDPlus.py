'''-------------------------------------------------------------------------------
 Tool Name:   CreateNetworkConnectivityFileNHDPlus
 Source Name: CreateNetworkConnectivityFileNHDPlus.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Alan D. Snow, US Army ERDC (Based on script by Cedric David)
 Updated by:  Alan D. Snow, US Army ERDC
 Description: Generates CSV file of stream network connectivity for RAPID based on
              the input NHDPlus flowlines with COMID, FROMNODE, TONODE, and DIVERGENCE.
 History:     Initial coding - 07/08/2016, version 1.0
 Updated:     Version 1.0, Initial coding - 07/08/2016, version 1.0
-------------------------------------------------------------------------------'''
import arcpy
import csv
import numpy as np
import os

class CreateNetworkConnectivityFileNHDPlus(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Connectivity File for NHDPlus"
        self.description = "Creates Network Connectivity input CSV file for RAPID \
        based on the Drainage Line feature class with COMID, FROMNODE, TONODE, and DIVERGENCE fields"
        self.canRunInBackground = False
        self.category = "Preprocessing"

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_drainage_line = arcpy.Parameter(
                                            displayName = 'Input Drainage Line Features',
                                            name = 'in_drainage_line_features',
                                            datatype = 'GPFeatureLayer',
                                            parameterType = 'Required',
                                            direction = 'Input'
                                            )
        in_drainage_line.filter.list = ['Polyline']

        stream_id = arcpy.Parameter(name = "stream_ID",
                                    displayName = "Stream ID",
                                    direction = "Input",
                                    parameterType = "Required",
                                    datatype = "Field"
                                    )
        stream_id.parameterDependencies = ["in_drainage_line_features"]
        stream_id.filter.list = ['Short', 'Long', 'Double']
        stream_id.value = "COMID"
        
        fromnode_field = arcpy.Parameter(name = "fromnode_field",
                                 displayName = "From Node ID",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        fromnode_field.parameterDependencies = ["in_drainage_line_features"]
        fromnode_field.filter.list = ['Short', 'Long', 'Double']
        fromnode_field.value = "FROMNODE"

        tonode_field = arcpy.Parameter(name = "tonode_field",
                                 displayName = "To Node ID",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        tonode_field.parameterDependencies = ["in_drainage_line_features"]
        tonode_field.filter.list = ['Short', 'Long', 'Double']
        tonode_field.value = "TONODE"

        divergence_field = arcpy.Parameter(name = "divergence_field",
                                           displayName = "Divergence ID",
                                           direction = "Input",
                                           parameterType = "Required",
                                           datatype = "Field"
                                           )
                                           
        divergence_field.parameterDependencies = ["in_drainage_line_features"]
        divergence_field.filter.list = ['Short', 'Long', 'Double']
        divergence_field.value = "DIVERGENCE"

        out_csv_file = arcpy.Parameter(
                    displayName = 'Output Network Connectivity File',
                    name = 'out_network_connectivity_file',
                    datatype = 'DEFile',
                    parameterType = 'Required',
                    direction = 'Output')

        in_max_nbr_upstream = arcpy.Parameter(
                    displayName = 'Maximum Number of Upstream Reaches',
                    name = 'max_nbr_upstreams',
                    datatype = 'GPLong',
                    parameterType = 'Optional',
                    direction = 'Input')

        return [in_drainage_line,
                stream_id,
                fromnode_field,
                tonode_field,
                divergence_field,
                out_csv_file,
                in_max_nbr_upstream]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[5].altered:
            (dirnm, basenm) = os.path.split(parameters[5].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[5].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[5].value = os.path.join(
                arcpy.env.scratchFolder, "rapid_connect.csv")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[6].altered:
            max_nbr = parameters[6].value
            if (max_nbr < 0 or max_nbr > 12):
                parameters[6].setErrorMessage("Input Maximum Number of Upstreams must be within [1, 12]")
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_drainage_line = parameters[0].valueAsText
        rivid_field = parameters[1].valueAsText
        fromnode_field = parameters[2].valueAsText
        tonode_field = parameters[3].valueAsText
        divergence_field = parameters[4].valueAsText
        out_csv_file = parameters[5].valueAsText
        in_max_nbr_upstreams = parameters[6].value
            
        #check to see if a NextDownID already exists
        Next_Down_ID = "NextDownID"
        fieldList = arcpy.ListFields(in_drainage_line, Next_Down_ID)
        fieldCount = len(fieldList)
        if (fieldCount > 0):
            arcpy.AddMessage("Skipping the addition of the NextDownID field as it already exists. If you want to re-calculate this field, delete it and re-run this tool ...")
        else:
            arcpy.AddMessage("Adding NextDownID field ...")
            #Add NextDownID field
            result = arcpy.GetCount_management(in_drainage_line)
            number_of_features = int(result.getOutput(0))
            rivid_list = np.zeros(number_of_features, dtype=np.int32)
            fromnode_list = np.zeros(number_of_features, dtype=np.int32)
            tonode_list = np.zeros(number_of_features, dtype=np.int32)
            divergence_list = np.zeros(number_of_features, dtype=np.int32)
            field_names = [rivid_field, fromnode_field, tonode_field, divergence_field]
            for feature_idx, row in enumerate(sorted(arcpy.da.SearchCursor(in_drainage_line, field_names))):
                rivid_list[feature_idx] = row[0]
                fromnode_list[feature_idx] = row[1]
                tonode_list[feature_idx] = row[2]
                divergence_list[feature_idx] = row[3]

            #-------------------------------------------------------------------------------
            #Compute connectivity (based on: https://github.com/c-h-david/rrr/blob/master/src/rrr_riv_tot_gen_all_nhdplus.py)
            #-------------------------------------------------------------------------------
            fromnode_list[fromnode_list==0] = -9999
            #Some NHDPlus v1 reaches have FLOWDIR='With Digitized' but no info in VAA table
            
            fromnode_list[divergence_list==2] = -9999
            #Virtually disconnect the upstream node of all minor divergences
            divergence_list = [] #don't need this anymore

            arcpy.AddField_management(in_drainage_line, Next_Down_ID, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

            #determine the downstream reach for each reach
            with arcpy.da.UpdateCursor(in_drainage_line,
                                       [rivid_field, Next_Down_ID]) as cursor:
                for row in cursor:
                    rivid_index = np.where(rivid_list==row[0])[0][0]
                    try:
                        row[1] = rivid_list[np.where(fromnode_list==tonode_list[rivid_index])[0][0]]
                    except IndexError:
                        row[1] = -1 #this is an outlet
                        pass
                    cursor.updateRow(row)
            
            # Delete cursor and row objects to remove locks on the data
            del row
            del cursor
            
            #empty remaining unecessary lists
            rivid_list = []
            fromnode_list = []
            tonode_list = []

        #Create Network Connecitivty File
        script_directory = os.path.dirname(__file__)
        arcpy.ImportToolbox(os.path.join(os.path.dirname(script_directory), "RAPID Tools.pyt"))
        arcpy.CreateNetworkConnectivityFile_RAPIDTools(in_drainage_line, 
                                                       rivid_field, 
                                                       Next_Down_ID,
                                                       out_csv_file,
                                                       in_max_nbr_upstreams
                                                       )
            
        return

