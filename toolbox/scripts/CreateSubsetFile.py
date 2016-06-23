'''-------------------------------------------------------------------------------
 Tool Name:   CreateSubsetFile
 Source Name: CreateSubsetFile.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Generates CSV file of HydroID river network subset for RAPID based
			  on the selected features of the input Drainage Line feature class.
 History:     Initial coding - 07/22/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014 Added comments about the order of rows in tool output
              Version 1.1, 10/24/2014 Modified file and tool names
              Version 1.1, 02/19/2015 Enhancement - Added error handling for message updating of
                input drainage line features
              Version 1.2, 12/18/2015 Enhancement - Allow for any field to be used as the stream id field (Alan Snow, US Army ERDC)
              Version 1.2, 12/18/2015 Enhancement - Sort by NHDPlus HYDROSEQ if available (Alan Snow, US Army ERDC)
-------------------------------------------------------------------------------'''
import arcpy
import csv
import os

class CreateSubsetFile(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Subset File"
        self.description = "Creates CSV file of HydroID river network subset for RAPID\
        based on the selected features of the input Drainage Line feature class"
        self.canRunInBackground = False
        self.category = "Preprocessing"

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_drainage_line = arcpy.Parameter(
                    displayName = 'Input Drainage Line Features',
                    name = 'in_drainage_line_features',
                    datatype = 'GPFeatureLayer',
                    parameterType = 'Required',
                    direction = 'Input')
        in_drainage_line.filter.list = ['Polyline']

        in_stream_id = arcpy.Parameter(name = "stream_ID",
                                       displayName = "Stream ID",
                                       direction = "Input",
                                       parameterType = "Required",
                                       datatype = "Field"
                                       )
        in_stream_id.parameterDependencies = ["in_drainage_line_features"]
        in_stream_id.filter.list = ['Short', 'Long']
        in_stream_id.value = "HydroID"
        
        out_csv_file = arcpy.Parameter(
                    displayName = 'Output Subset File',
                    name = 'out_subset_file',
                    datatype = 'DEFile',
                    parameterType = 'Required',
                    direction = 'Output')

        return [in_drainage_line,
                in_stream_id,
				out_csv_file]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[2].valueAsText is not None:
            (dirnm, basenm) = os.path.split(parameters[2].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[2].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[2].value = os.path.join(
                arcpy.env.scratchFolder, "riv_bas_id.csv")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_drainage_line = parameters[0].valueAsText
        in_stream_id = parameters[1].valueAsText
        out_csv_file = parameters[2].valueAsText

        query_fields = [in_stream_id, in_stream_id]
        sort_reverse = False

        fields = arcpy.ListFields(parameters[0].valueAsText)
        upper_field_names = [field.baseName.upper() for field in fields]
        orig_field_names = [field.name for field in fields]
        #Sort by HYDROSEQ order if the option exists
        if 'HYDROSEQ' in upper_field_names:
            #with this method, smaller is downstream
            sort_field = orig_field_names[upper_field_names.index('HYDROSEQ')]
            query_fields = [sort_field, in_stream_id]
            sort_reverse = True
            arcpy.AddMessage("Sorting by %s" % sort_field)

        list_all = []

        '''The script line below makes sure that rows in the subset file are
           arranged in descending order of NextDownID of stream segements'''
        for row in sorted(arcpy.da.SearchCursor(in_drainage_line, query_fields), reverse=sort_reverse):
			list_all.append([row[1]])

        with open(out_csv_file,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row_list in list_all:
                out = row_list
                connectwriter.writerow(out)

        return

