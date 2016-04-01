'''-------------------------------------------------------------------------------
 Tool Name:   CreateMuskingumParameterFiles
 Source Name: CreateMuskingumParameterFiles.py
 Version:     ArcGIS 10.2
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Generates CSV file of kfac, k and x Muskingum parameter for RAPID based
			  on the length of river reach and celerity of flow wave
			  the input Drainage Line feature class with Length fields.
 History:     Initial coding - 07/21/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014 Added comments about the order of rows in tool output
              Version 1.1, 10/24/2014 Modified file and tool names
              Version 1.1, 02/19/2015 Enhancement - Added error handling for message updating of
                input drainage line features
-------------------------------------------------------------------------------'''
import os
import arcpy
import csv

class CreateMuskingumParameterFiles(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Muskingum Parameter Files"
        self.description = "Creates Muskingum Parameters input CSV files for RAPID \
        based on the Drainage Line feature class with HydroID and NextDownID fields"
        self.canRunInBackground = False
        self.category = "Preprocessing"

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_drainage_line = arcpy.Parameter(
                    displayName = 'Input Drainage Line Features',
                    name = 'input_drainage_line_features',
                    datatype = 'GPFeatureLayer',
                    parameterType = 'Required',
                    direction = 'Input')
        in_drainage_line.filter.list = ['Polyline']

        out_csv_file1 = arcpy.Parameter(
                    displayName = 'Output kfac File',
                    name = 'out_kfac_file',
                    datatype = 'DEFile',
                    parameterType = 'Required',
                    direction = 'Output')

        out_csv_file2 = arcpy.Parameter(
                    displayName = 'Output k File',
                    name = 'out_k_file',
                    datatype = 'DEFile',
                    parameterType = 'Required',
                    direction = 'Output')

        out_csv_file3 = arcpy.Parameter(
                    displayName = 'Output x File',
                    name = 'out_x_file',
                    datatype = 'DEFile',
                    parameterType = 'Required',
                    direction = 'Output')

        return [in_drainage_line,
				out_csv_file1,
				out_csv_file2,
				out_csv_file3]

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
                arcpy.env.scratchFolder, "kfac.csv")

        if parameters[2].valueAsText is not None:
            (dirnm, basenm) = os.path.split(parameters[2].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[2].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[2].value = os.path.join(
                arcpy.env.scratchFolder, "k.csv")

        if parameters[3].valueAsText is not None:
            (dirnm, basenm) = os.path.split(parameters[3].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[3].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[3].value = os.path.join(
                arcpy.env.scratchFolder, "x.csv")

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        try:
            if parameters[0].altered:
                field_names = []
                fields = arcpy.ListFields(parameters[0].valueAsText)
                for field in fields:
                    field_names.append(field.baseName.upper())
                if not ("MUSK_KFAC" in field_names and "MUSK_K" in field_names and "MUSK_X" in field_names):
                    parameters[0].setErrorMessage("Input Drainage Line must contain Musk_kfac, Musk_k and Musk_x.")
        except Exception as e:
            parameters[0].setErrorMessage(e.message)

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_drainage_line = parameters[0].valueAsText
        out_csv_file1 = parameters[1].valueAsText
        out_csv_file2 = parameters[2].valueAsText
        out_csv_file3 = parameters[3].valueAsText

        fields = ['HydroID', 'Musk_kfac', 'Musk_k', 'Musk_x']

        list_all_kfac = []
        list_all_k = []
        list_all_x = []

        '''The script line below makes sure that rows in the muskingum parameter
            files are arranged in ascending order of HydroIDs of stream segements'''
        for row in sorted(arcpy.da.SearchCursor(in_drainage_line, fields)):
			kfac=row[1]
			k=row[2]
			x=row[3]

			list_all_kfac.append([kfac])
			list_all_k.append([k])
			list_all_x.append([x])

        with open(out_csv_file1,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row_list in list_all_kfac:
                out = row_list
                connectwriter.writerow(out)

        with open(out_csv_file2,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row_list in list_all_k:
                out = row_list
                connectwriter.writerow(out)

        with open(out_csv_file3,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row_list in list_all_x:
                out = row_list
                connectwriter.writerow(out)

        return

