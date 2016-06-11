'''-------------------------------------------------------------------------------
 Tool Name:   CreateMuskingumKfacFile
 Source Name: CreateMuskingumKfacFile.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Alan D. Snow (US Army ERDC)
 History:     Initial coding - 10/8/2015, version 1.0
 Description: Version 1.0, 10/8/2015, Generate muskingum Kfac file based on length and/or slope.
-------------------------------------------------------------------------------'''
import arcpy
import csv
import numpy as np
import os

class CreateMuskingumKfacFile(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Muskingum Kfac File"
        self.description = "Generate muskingum Kfac file for RAPID \
                            based on length and slope of river reaches"
        self.canRunInBackground = False
        self.category = "Calibration"

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
        in_drainage_line = arcpy.Parameter(
                    displayName = 'Input Drainage Line Features',
                    name = 'in_drainage_line_features',
                    datatype = 'GPFeatureLayer',
                    parameterType = 'Required',
                    direction = 'Input')
        in_drainage_line.filter.list = ['Polyline']

        stream_id = arcpy.Parameter(name = "stream_ID",
                                 displayName = "Stream ID Field",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        stream_id.parameterDependencies = ["in_drainage_line_features"]
        stream_id.filter.list = ['Short', 'Long']

        length = arcpy.Parameter(name = "length",
                                 displayName = "Length Field (km)",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        length.parameterDependencies = ["in_drainage_line_features"]
        length.filter.list = ['Float', 'Double']

        slope = arcpy.Parameter(name = "slope",
                                 displayName = "Slope Field",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        slope.parameterDependencies = ["in_drainage_line_features"]
        slope.filter.list = ['Float', 'Double']

        celerity = arcpy.Parameter(name = "co",
                                 displayName = "Co (water wave celerity in m/s)",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Double"
                                 )
        celerity.value = 1000.0/3600.0 #1km/hr in m/s
        
        formula = arcpy.Parameter(name = "in_formula",
                                 displayName = "Muskingum Kfac Formula",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")

        formula.filter.list = ["River Length/Co", 
                               "Eta*River Length/Sqrt(River Slope)",
                               "Eta*River Length/Sqrt(River Slope) [0.05, 0.95]"]

        in_connectivity_file = arcpy.Parameter(
                                    displayName = 'Input Network Connectivity File',
                                    name = 'in_network_connectivity_file',
                                    datatype = 'DEFile',
                                    parameterType = 'Required',
                                    direction = 'Input')

        out_kfac_file = arcpy.Parameter(
                                    displayName = 'Output Muskingum Kfac File',
                                    name = 'out_muskingum_kfac_file',
                                    datatype = 'DEFile',
                                    parameterType = 'Required',
                                    direction = 'Output')
        
        
        return [in_drainage_line,
                stream_id,
                length,
                slope,
                celerity,
                formula,
                in_connectivity_file,
                out_kfac_file]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[7].altered:
            (dirnm, basenm) = os.path.split(parameters[7].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[7].value = os.path.join(
                    dirnm, "{}.csv".format(basenm))
        else:
            parameters[7].value = os.path.join(
                arcpy.env.scratchFolder, "kfac.csv")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

    def execute(self, parameters, messages):
        """The source code of the tool."""
        in_drainage_line = parameters[0].valueAsText
        stream_id = parameters[1].valueAsText
        length = parameters[2].valueAsText
        slope = parameters[3].valueAsText
        celerity = float(parameters[4].valueAsText)
        formula = parameters[5].valueAsText
        in_connectivity_file = parameters[6].valueAsText
        out_kfac_file = parameters[7].valueAsText


        np_table = arcpy.da.TableToNumPyArray(in_drainage_line, [stream_id, length, slope])
        connectivity_table = self.csvToList(in_connectivity_file)
        
        length_slope_array = []
        kfac2_array = []
        formula_type = 2
        if formula == "Eta*River Length/Sqrt(River Slope)":
            formula_type = 3
        elif formula == "Eta*River Length/Sqrt(River Slope) [0.05, 0.95]":
            formula_type = 4
        
        with open(out_kfac_file,'wb') as kfacfile:
            kfac_writer = csv.writer(kfacfile)
            for row in connectivity_table:
                streamID = int(float(row[0]))
                
                streamIDindex = np_table[stream_id]==streamID
                # find the slope
                stream_slope = np_table[streamIDindex][slope]
                
                if stream_slope <= 0:
                    #if no slope, take average of upstream and downstream to get it
                    nextDownID = int(float(row[1]))
                    next_down_slope = 0
                    try:
                        next_down_index = np.where(np_table[stream_id]==nextDownID)[0][0]
                        next_down_slope = np_table[next_down_index][slope]
                    except IndexError:
                        pass
                        
                    nextUpID = int(float(row[3]))
                    next_up_slope = 0
                    try:
                        next_up_index = np.where(np_table[stream_id]==nextUpID)[0][0]
                        next_up_slope = np_table[next_up_index][slope]
                    except IndexError:
                        pass
                        
                    stream_slope = (next_down_slope+next_up_slope)/2
                    if stream_slope <=0:
                        #if still no slope, set to 0.001
                        stream_slope = 0.001
                
                # find the length
                stream_length = np_table[streamIDindex][length]*1000
                if formula_type >= 3:
                    length_slope_array.append(stream_length/stream_slope**0.5)
                    kfac2_array.append(stream_length/celerity)
                else:
                    kfac = stream_length/celerity
                    kfac_writer.writerow(kfac)
            
            if formula_type >= 3:
                if formula_type == 4:
                    arcpy.AddMessage("Filtering Data by 5th and 95th Percentiles ...")
                    length_slope_array = np.array(length_slope_array)
                    percentile_5 = np.percentile(length_slope_array, 5)
                    percentile_95 = np.percentile(length_slope_array, 95)
                    
                    length_slope_array[length_slope_array<percentile_5] = percentile_5
                    length_slope_array[length_slope_array>percentile_95] = percentile_95
                
                eta = np.mean(kfac2_array) / np.mean(length_slope_array)
                arcpy.AddMessage("Kfac2_Avg {}".format(np.mean(kfac2_array)))
                arcpy.AddMessage("Length_Slope Avg {}".format( np.mean(length_slope_array)))
                arcpy.AddMessage("Eta {}".format(eta))
                arcpy.AddMessage("Writing Data ...")
                for len_slope in length_slope_array:
                    kfac_writer.writerow(eta*len_slope)
        return

