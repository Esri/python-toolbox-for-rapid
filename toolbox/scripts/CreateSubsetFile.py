'''-------------------------------------------------------------------------------
 Tool Name:   CreateSubsetFile
 Source Name: CreateSubsetFile.py
 Version:     ArcGIS 10.2
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Generates CSV file of HydroID river network subset for RAPID based
			  on the selected features of the input Drainage Line feature class.
 History:     Initial coding - 07/22/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014 Added comments about the order of rows in tool output
              Version 1.1, 10/24/2014 Modified file and tool names
              Version 1.1, 02/19/2015 Enhancement - Added error handling for message updating of
                input drainage line features
-------------------------------------------------------------------------------'''
import os
import arcpy
import csv

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

        out_csv_file = arcpy.Parameter(
                    displayName = 'Output Subset File',
                    name = 'out_subset_file',
                    datatype = 'DEFile',
                    parameterType = 'Required',
                    direction = 'Output')

        return [in_drainage_line,
				out_csv_file]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[1].valueAsText is not None:
            (dirnm, basenm) = os.path.split(parameters[1].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[1].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[1].value = os.path.join(
                arcpy.env.scratchFolder, "riv_bas_id.csv")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        try:
            if parameters[0].altered:
                field_names = []
                fields = arcpy.ListFields(parameters[0].valueAsText)
                for field in fields:
                    field_names.append(field.baseName.upper())
                if not ("HYDROID" in field_names and "NEXTDOWNID" in field_names):
                    parameters[0].setErrorMessage("Input Drainage Line must contain HydroID and NextDownID.")
        except Exception as e:
            parameters[0].setErrorMessage(e.message)

        return


    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_drainage_line = parameters[0].valueAsText
        out_csv_file = parameters[1].valueAsText

        fields = ['NextDownID', 'HydroID']

        list_all = []

        '''The script line below makes sure that rows in the subset file are
           arranged in descending order of NextDownID of stream segements'''
        for row in sorted(arcpy.da.SearchCursor(in_drainage_line, fields), reverse=True):
			list_all.append([row[1]])

        with open(out_csv_file,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row_list in list_all:
                out = row_list
                connectwriter.writerow(out)

        return

