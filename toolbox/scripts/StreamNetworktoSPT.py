'''-------------------------------------------------------------------------------
 Tool Name:   StreamNetworktoSPT
 Source Name: StreamNetworktoSPT.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann and Alan Snow
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/23/2016, version 1.0
 Updated:     Version 1.0, 06/23/2016, initial coding
-------------------------------------------------------------------------------'''
import arcpy
import re
import os

class StreamNetworktoSPT(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stream Network to SPT"
        self.description = ("Processes stream network data into files for Streamflow Prediction Tool (SPT)")
        self.canRunInBackground = False
        self.category = "Workflows"
        self.errorMessages = ["Need both watershed & subbasin name to add ECMWF names.",
                              "Need both watershed & subbasin name to add WRF-Hydro names.",
                              "Need ECMWF or WRF-Hydro watershed/subbasing names."]
    def getParameterInfo(self):
        """Define parameter definitions""" 

        input_Drainage_Lines = arcpy.Parameter(name="input_Drainage_Lines",
                                         displayName="Input Drainage Lines",
                                         direction="Input",
                                         parameterType="Required",
                                         datatype="GPFeatureLayer")
        input_Drainage_Lines.filter.list = ['Polyline']
        
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
                        
        Catchment_Features = arcpy.Parameter(name="Catchment_Features",
                                     displayName="Input Catchment Features",
                                     direction="Input",
                                     parameterType="Required",
                                     datatype="GPFeatureLayer")
        Catchment_Features.filter.list = ['Polygon']
        
        SPT_out_folder = arcpy.Parameter(name = 'SPT_out_folder',
                                           displayName = 'Folder for SPT Shapefiles',
                                           datatype = 'DEFolder',
                                           parameterType = 'Required',
                                           direction = 'Input')

        params = [input_Drainage_Lines, param1, param2, param3, param4,
                  Catchment_Features, SPT_out_folder]

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
        
        Drainage_Lines = parameters[0].valueAsText
        ecmwf_watershed_name = parameters[1].valueAsText
        ecmwf_subbasin_name = parameters[2].valueAsText
        wrf_hydro_watershed_name = parameters[3].valueAsText
        wrf_hydro_aubbasin_name = parameters[4].valueAsText
        Catchment_Features = parameters[5].valueAsText
        SPT_out_folder = parameters[6].valueAsText
       
        script_directory = os.path.dirname(__file__)
        arcpy.ImportToolbox(os.path.join(os.path.dirname(script_directory), "RAPID Tools.pyt"))
        
        #Add watershed names to drainagelines
        arcpy.AddSPTFields_RAPIDTools(Drainage_Lines,
                                      ecmwf_watershed_name, 
                                      ecmwf_subbasin_name,
                                      wrf_hydro_watershed_name,
                                      wrf_hydro_aubbasin_name)
                                             
        #Dissolve Catchments
        Dissolved_Catchments = os.path.join(os.path.dirname(Catchment_Features), "WatershedBoundary")
        #Input_Catchment_Features to Dissolved_Catchments
        arcpy.Dissolve_management(Catchment_Features, Dissolved_Catchments) 
        
        #export shapefiles to new folder
        inputs = [Dissolved_Catchments, Drainage_Lines]
        arcpy.FeatureClassToShapefile_conversion(inputs, SPT_out_folder)

        return
