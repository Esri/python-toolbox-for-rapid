'''-------------------------------------------------------------------------------
 Tool Name:   CreateRivIDGageFile
 Source Name: CreateRivIDGageFile.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann and Alan Snow
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/27/2016, version 1.0
 Updated:     Version 1.1, 06/27/2016, initial coding
-------------------------------------------------------------------------------'''
import arcpy
import csv
import os
import time

class CreateRivIDGageFile(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create rivid gage file"
        self.description = ("Creates the rivid gage RAPID")
        self.canRunInBackground = False
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_Drainage_Lines = arcpy.Parameter(name="input_Drainage_Lines",
                                         displayName="Input Drainage Lines",
                                         direction="Input",
                                         parameterType="Required",
                                         datatype="GPFeatureLayer")
        input_Drainage_Lines.filter.list = ['Polyline']

        stream_id = arcpy.Parameter(name = "stream_ID",
                                 displayName = "Stream ID",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        stream_id.parameterDependencies = ["input_Drainage_Lines"]
        stream_id.filter.list = ['Short', 'Long']
        stream_id.value = "HydroID"

        gage_id = arcpy.Parameter(name = "gage_id",
                                  displayName = "Gage ID",
                                  direction = "Input",
                                  parameterType = "Required",
                                  datatype = "Field"
                                  )
        gage_id.parameterDependencies = ["input_Drainage_Lines"]

        gage_adjusted_id = arcpy.Parameter(name = "gage_adjusted_id",
                                  displayName = "Gage adjusted flow ID",
                                  direction = "Input",
                                  parameterType = "Required",
                                  datatype = "Field"
                                  )
        gage_adjusted_id.parameterDependencies = ["input_Drainage_Lines"]

        out_csv_file = arcpy.Parameter(
                                       displayName = 'Output River ID Gage ID File',
                                       name = 'out_rivID_gageID_file',
                                       datatype = 'DEFile',
                                       parameterType = 'Required',
                                       direction = 'Output'
                                       )

        params = [input_Drainage_Lines, 
                  stream_id, 
                  gage_id, 
                  gage_adjusted_id,
                  out_csv_file]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        input_Drainage_Lines = parameters[0].valueAsText
        stream_id = parameters[1].valueAsText
        gage_id = parameters[2].valueAsText
        gage_adjusted_id = parameters[3].valueAsText
        out_csv_file = parameters[4].valueAsText

        #generate file 
        ##make a list of all of the fields in the table
        field_names = [stream_id, gage_adjusted_id, gage_id]
        with open(out_csv_file,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            connectwriter.writerow(['river_id', 'gage_adjusted_flow_id', 'gage_id'])
            for row in sorted(arcpy.da.SearchCursor(input_Drainage_Lines, field_names)):
                connectwriter.writerow(row)
        
        return
