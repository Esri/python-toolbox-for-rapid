'''-------------------------------------------------------------------------------
 Tool Name:   CreateMuskingumXFile
 Source Name: CreateMuskingumXFile.py
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

class CreateMuskingumXFile(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Muskingum X File"
        self.description = ("Creates the Muskingum X file for RAPID")
        self.canRunInBackground = False
        self.category = "Calibration"

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
        stream_id.filter.list = ['Short', 'Long', 'Double']
        stream_id.value = "HydroID"

        out_muskingum_x_file = arcpy.Parameter(name = 'out_muskingum_x_file',
                                               displayName = 'Muksingum X File',
                                               datatype = 'DEFile',
                                               parameterType = 'Required',
                                               direction = 'Output')
        
        params = [input_Drainage_Lines,
                  stream_id,
                  out_muskingum_x_file]

        return params

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
                arcpy.env.scratchFolder, "x.csv")

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        Drainage_Lines = parameters[0].valueAsText
        stream_id = parameters[1].valueAsText
        out_muskingum_x_file = parameters[2].valueAsText

        Musk_x_field = "Musk_x"
        # Process: Muskingum x  
        #check to see if a Muskingum x already exists, if not, add the field
        fieldList = arcpy.ListFields(Drainage_Lines, Musk_x_field)
        fieldCount = len(fieldList)
        if (fieldCount < 1):
            arcpy.AddError("The Musk_x field is missing. To fix this, run the \"Create Muskingum X Field\" tool.")
       
        #generate file 
        ##make a list of all of the fields in the table
        field_names = [stream_id, Musk_x_field]
        with open(out_muskingum_x_file,'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect='excel')
            for row in sorted(arcpy.da.SearchCursor(Drainage_Lines, field_names)):
                connectwriter.writerow([row[1]])

        
        return
