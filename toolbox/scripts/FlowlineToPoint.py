'''-------------------------------------------------------------------------------
 Tool Name:   FlowlineToPoint.py
 Source Name: FlowlineToPoint
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Write the centroid coordinates of Flowlines into a CSV file for the
                conventions for CF (Climate and Forecast) metadata.
 History:     Initial coding - 07/15/2015, version 1.0 (Adapted from Alan Snow's
                script)
 Updated:
-------------------------------------------------------------------------------'''
import arcpy
import csv
from numpy import array, isnan
import os

class FlowlineToPoint(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Flowline To Point"
        self.description = ("Write the centroid coordinates of flowlines into a csv file")
        self.canRunInBackground = False
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_drainage_line = arcpy.Parameter(
                    displayName = 'Input Drainage Line Features',
                    name = 'in_drainage_line_features',
                    datatype = 'GPFeatureLayer',
                    parameterType = 'Required',
                    direction = 'Input')
        in_drainage_line.filter.list = ['Polyline']

        param1 = arcpy.Parameter(name = 'out_point_file',
                                 displayName = 'Output Point File',
                                 direction = 'Output',
                                 parameterType = 'Required',
                                 datatype = 'DEFile')

        params = [in_drainage_line, param1]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[1].altered:
            (dirnm, basenm) = os.path.split(parameters[1].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[1].value = os.path.join(dirnm, "{}.csv".format(basenm))

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        # Script arguments
        Input_Features = parameters[0].valueAsText
        Output_Table = parameters[1].valueAsText
        Intermediate_Feature_Points = os.path.join("in_memory","flowline_centroid_points")

        # Process: Feature To Point
        arcpy.AddMessage("Converting flowlines to points ...")
        arcpy.FeatureToPoint_management(Input_Features, Intermediate_Feature_Points, "CENTROID")

        # Process: Add XY Coordinates
        arcpy.AddMessage("Adding XY coordinates to points ...")
        arcpy.AddXY_management(Intermediate_Feature_Points)

        # write only desired fields to csv
        arcpy.AddMessage("Writing output to csv ...")
        original_field_names = [f.name for f in arcpy.ListFields(Intermediate_Feature_Points)]
        #COMID,Lat,Lon,Elev_m
        needed_field_names = [["hydroid","comid"], "point_y", "point_x", "point_z"]
        actual_field_names = ["", "", ""]
        for original_field_name in original_field_names:
            original_field_name_lower = original_field_name.lower()
            if original_field_name_lower == needed_field_names[0][0] \
            or original_field_name_lower == needed_field_names[0][1]:
                actual_field_names[0] = original_field_name
            elif original_field_name_lower == needed_field_names[1]:
                actual_field_names[1] = original_field_name
            elif original_field_name_lower == needed_field_names[2]:
                actual_field_names[2] = original_field_name
            elif original_field_name_lower == needed_field_names[3]:
                actual_field_names.append(original_field_name)
        z_elev_found = True
        if len(actual_field_names) <=3:
            z_elev_found = False
            arcpy.AddMessage("POINT_Z field not found. Replacing with zero.")
            
        #check to make sure all fields exist
        for field_index, field_name in enumerate(actual_field_names):
            if field_name == "":
                messages.addErrorMessage("Field name {0} not found.".format(needed_field_names[field_index]))
                raise arcpy.ExecuteError

        #print valid field names to table
        with open(Output_Table, 'wb') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['COMID','Lat','Lon','Elev_m'])
            with arcpy.da.SearchCursor(Intermediate_Feature_Points, actual_field_names) as cursor:
                z_elev = 0
                for row in cursor:
                    #make sure all values are valid
                    np_row = array(row)
                    np_row[isnan(np_row)] = 0
                    if z_elev_found:
                        z_elev = row[3]
                    writer.writerow([int(row[0]), row[1], row[2], z_elev])

        arcpy.AddMessage("NaN value(s) replaced with zero. Please check output for accuracy.")

        return