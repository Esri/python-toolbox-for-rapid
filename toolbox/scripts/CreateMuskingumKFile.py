'''-------------------------------------------------------------------------------
 Tool Name:   CreateMuskingumKFile
 Source Name: CreateMuskingumKFile.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Alan D. Snow (US Army ERDC)
 History:     Initial coding - 10/8/2015, version 1.0
 Description: Version 1.0, 10/8/2015, Generate muskingum K file from kfac file and lambda.
-------------------------------------------------------------------------------'''
import arcpy
import csv
import os

class CreateMuskingumKFile(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Muskingum K File"
        self.description = "Generate muskingum K file for RAPID \
                            based on kfac file and calibrated value for lamda."
        self.canRunInBackground = False
        self.category = "Preprocessing"

    def csvToList(self, csv_file, delimiter=','):
        """
        Reads in a CSV file and returns the contents as list,
        where every row is stored as a sublist, and each element
        in the sublist represents 1 cell in the table.

        """
        with open(csv_file, 'rb') as csv_con:
            reader = csv.reader(csv_con, delimiter=delimiter)
            return list(reader)

    def getParameterInfo(self):
        """Define parameter definitions"""
        lambda_k = arcpy.Parameter(name = "lambda",
                                 displayName = "Lambda (k = lambda*kfac)",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Double"
                                 )

        in_kfac_file = arcpy.Parameter(
                                    displayName = 'Input Muskingum Kfac File',
                                    name = 'in_muskingum_kfac_file',
                                    datatype = 'DEFile',
                                    parameterType = 'Required',
                                    direction = 'Input')

        out_k_file = arcpy.Parameter(
                                    displayName = 'Output Muskingum K File',
                                    name = 'out_muskingum_k_file',
                                    datatype = 'DEFile',
                                    parameterType = 'Required',
                                    direction = 'Output')
        
        
        return [lambda_k,
                in_kfac_file,
                out_k_file]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[2].altered:
            (dirnm, basenm) = os.path.split(parameters[2].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[2].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[2].value = os.path.join(
                arcpy.env.scratchFolder, "k.csv")
                
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

    def execute(self, parameters, messages):
        """The source code of the tool."""
        lambda_k = float(parameters[0].valueAsText)
        in_kfac_file = parameters[1].valueAsText
        out_k_file = parameters[2].valueAsText

        kfac_table = self.csvToList(in_kfac_file)
        
        with open(out_k_file,'wb') as kfile:
            k_writer = csv.writer(kfile)
            for row in kfac_table:
                 k_writer.writerow([lambda_k*float(row[0])])
            
        return

