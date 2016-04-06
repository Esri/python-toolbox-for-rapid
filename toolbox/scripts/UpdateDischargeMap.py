'''-------------------------------------------------------------------------------
 Tool Name:   UpdateDischargeMap
 Source Name: UpdateDischargeMap.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Create a dischage map document.
 History:     Initial coding - 05/26/2015, version 1.0
 Updated:     Version 1.0, 06/02/2015 Bug fixing: uses arcpy.mapping.UpdateLayer instead of apply symbology
                from layer
              Version 1.1, 06/24/2015 Adapted to the group layer in the map document
              Version 1.1, 04/01/2016 deleted the lines for importing unnecessary modules
-------------------------------------------------------------------------------'''
import os
import arcpy
import time

class UpdateDischargeMap(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Discharge Map"
        self.description = "Update a discharge map document for stream flow visualization based on \
                            the .mxd file and a new discharge table with the same name"
        self.GDBtemplate_layer = os.path.join(os.path.dirname(__file__), "templates", "FGDB_TimeEnabled.lyr")
        self.SQLtemplate_layer = os.path.join(os.path.dirname(__file__), "templates", "SQL_TimeEnabled.lyr")
        self.errorMessages = ["Incorrect map document"]
        self.canRunInBackground = False
        self.category = "Postprocessing"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_discharge_map",
                                 displayName = "Input Discharge Map",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEMapDocument"
                                 )

        param1 = arcpy.Parameter(name = "out_discharge_map",
                                 displayName = "Output Discharge Map",
                                 direction = "Output",
                                 parameterType = "Derived",
                                 datatype = "DEMapDocument"
                                 )

        params = [param0, param1]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        '''Check if .mxd is the suffix of the input map document name'''
        if parameters[0].altered:
            (dirnm, basenm) = os.path.split(parameters[0].valueAsText)
            if not basenm.endswith(".mxd"):
                parameters[0].setErrorMessage(self.errorMessages[0])
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        in_map_document = parameters[0].valueAsText

        '''Update symbology for each layer in the map document'''
        mxd = arcpy.mapping.MapDocument(in_map_document)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        for lyr in arcpy.mapping.ListLayers(mxd):
            if not lyr.isGroupLayer:
                (dirnm, basenm) = os.path.split(lyr.dataSource)
                template_lyr = self.GDBtemplate_layer
                if not dirnm.endswith('.gdb'):
                    template_lyr = self.SQLtemplate_layer
                # Update symbology from template
                templateLayer = arcpy.mapping.Layer(template_lyr)
                arcpy.mapping.UpdateLayer(df,  lyr, templateLayer, True)

        mxd.save()
        del mxd, df, templateLayer

        return


