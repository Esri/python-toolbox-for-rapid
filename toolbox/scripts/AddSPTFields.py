'''-------------------------------------------------------------------------------
 Tool Name:   AddSPTFields.py
 Source Name: AddSPTFields
 Version:     ArcGIS 10.3
 Author:      Alan D. Snow, US Army ERDC
 Updated by:  
 Description: Add fields to drainage line required for Streamflow Prediciton Tool
 History:     Initial coding - 12/21/2015, version 1.0 
 Updated: 
-------------------------------------------------------------------------------'''
import arcpy
import re

class AddSPTFields(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Streamflow Prediction Tool Fields"
        self.description = ("Add fields to drainage line required for SPT")
        self.canRunInBackground = False
        self.errorMessages = ["Need both watershed & subbasin name to add ECMWF names.",
                              "Need both watershed & subbasin name to add WRF-Hydro names.",
                              "Need ECMWF or WRF-Hydro watershed/subbasing names."]
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_drainage_line = arcpy.Parameter(
                    name = 'in_drainage_line_features',
                    displayName = 'Input Drainage Line Features',
                    datatype = 'GPFeatureLayer',
                    parameterType = 'Required',
                    direction = 'Input')
        in_drainage_line.filter.list = ['Polyline']

        param1 = arcpy.Parameter(name = "ECMWF_Watershed_Name",
                                 displayName = "ECMWF Watershed Name",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "Field"
                                 )
        param2 = arcpy.Parameter(name = "ECMWF_Subbasin_Name",
                                 displayName = "ECMWF Subbasin Name",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "Field"
                                 )
        param3 = arcpy.Parameter(name = "WRF_Hydro_Watershed_Name",
                                 displayName = "WRF-Hydro Watershed Name",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "Field"
                                 )
        param4 = arcpy.Parameter(name = "WRF_Hydro_Subbasin_Name",
                                 displayName = "WRF-Hydro Subbasin Name",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "Field"
                                 )

        params = [in_drainage_line, param1, param2, param3, param4]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def format_name(self, string):
        """Cleans string for the streamflow prediction tool input"""
        if string:
            formatted_string = string.strip().replace(" ", "_").lower()
            formatted_string = re.sub(r'[^a-zA-Z0-9_-]', '', formatted_string)
            while formatted_string.startswith('-') or formatted_string.startswith('_'):
                formatted_string = formatted_string[1:]
        else:
            formatted_string = ""
        return formatted_string
        
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        for i in range(1,5):
            if parameters[i].altered:
                parameters[i].value = self.format_name(parameters[i].valueAsText)
        return

        
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        valid_ecmwf_param = False
        if parameters[1].valueAsText and not parameters[2].valueAsText:
            parameters[2].setErrorMessage(self.errorMessages[0])
        elif parameters[2].valueAsText and not parameters[1].valueAsText:
            parameters[1].setErrorMessage(self.errorMessages[0])
        elif parameters[1].valueAsText and parameters[2].valueAsText:
            valid_ecmwf_param = True
            
        valid_wrf_hydro_param = False
        if parameters[3].valueAsText and not parameters[4].valueAsText:
            parameters[4].setErrorMessage(self.errorMessages[1])
        elif parameters[4].valueAsText and not parameters[3].valueAsText:
            parameters[3].setErrorMessage(self.errorMessages[1])
        elif parameters[3].valueAsText and parameters[4].valueAsText:
            valid_wrf_hydro_param = True

        if not valid_ecmwf_param and not valid_wrf_hydro_param:
            parameters[0].setErrorMessage(self.errorMessages[2])
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        # Script arguments
        drainage_line = parameters[0].valueAsText
        ecmwf_watershed_name = parameters[1].valueAsText
        ecmwf_subbasin_name = parameters[2].valueAsText
        wrf_hydro_watershed_name = parameters[3].valueAsText
        wrf_hydro_aubbasin_name = parameters[4].valueAsText

        #add ECMWF fields if necessary
        if ecmwf_watershed_name and ecmwf_subbasin_name:
            arcpy.AddMessage("Adding ECMWF watershed field with value {0}".format(ecmwf_watershed_name))
            arcpy.AddField_management(drainage_line, "watershed", "TEXT")
            arcpy.CalculateField_management(drainage_line, "watershed", "'{0}'".format(ecmwf_watershed_name), "PYTHON")
            arcpy.AddMessage("Adding ECMWF subbasin field with value {0}".format(ecmwf_subbasin_name))
            arcpy.AddField_management(drainage_line, "subbasin", "TEXT")
            arcpy.CalculateField_management(drainage_line, "subbasin", "'{0}'".format(ecmwf_subbasin_name), "PYTHON")
        
        #add WRF-Hydro fields if necessary
        if wrf_hydro_watershed_name and wrf_hydro_aubbasin_name:
            arcpy.AddMessage("Adding WRF-Hydro watershed field with value {0}".format(wrf_hydro_watershed_name))
            arcpy.AddField_management(drainage_line, "wwatershed", "TEXT")
            arcpy.CalculateField_management(drainage_line, "wwatershed", "'{0}'".format(wrf_hydro_watershed_name), "PYTHON")
            arcpy.AddMessage("Adding WRF-Hydro subbasin field with value {0}".format(wrf_hydro_aubbasin_name))
            arcpy.AddField_management(drainage_line, "wsubbasin", "TEXT")
            arcpy.CalculateField_management(drainage_line, "wsubbasin", "'{0}'".format(wrf_hydro_aubbasin_name), "PYTHON")

        return