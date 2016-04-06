'''-------------------------------------------------------------------------------
 Tool Name:   UpdateWeightTable
 Source Name: UpdateWeightTable.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Update weight table by comparing the IDs with those in connectivity
              file. This is a temporary tool to deal with the problem that there
              are more drainage line features than catchment features. Its functionality
              will be integrated into CreateWeightTableFrom***.py and the CreateInflowFile***
              .py tool will be redesigned.
 History:     Initial coding - 05/12/2015, version 1.0
 Updated:     Version 1.0, 05/12/2015, initial coding adapted from Alan Snow's script
              "format_weight_table_from_connecitivity.py", bug fixing: the rows appended by
                replacement_row in the new_weight_table get overwritten when replacement_row is
                updated.
              Version 1.0, 05/24/2015, bug fixing: set npoints as 1 in the replacement_row,
                and fixed the overwritting problem of the replacement_row (contributor: Alan Snow)
-------------------------------------------------------------------------------'''
import arcpy
import csv
import operator
import os



class UpdateWeightTable(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Weight Table"
        self.description = ("Update the weight table from the connnectivity file")
        self.canRunInBackground = False
        self.category = "Postprocessing"
        self.category = "Preprocessing"

    def csv_to_list(self, csv_file, delimiter=','):
        """
        Reads in a CSV file and returns the contents as list,
        where every row is stored as a sublist, and each element
        in the sublist represents 1 cell in the table.

        """
        with open(csv_file, 'rb') as csv_con:
            reader = csv.reader(csv_con, delimiter=delimiter)
            return list(reader)

    def convert_comid_to_int(self, csv_cont):
        """
        Converts cells to floats if possible
        (modifies input CSV content list).

        """
        for row in range(len(csv_cont)):
            try:
                csv_cont[row][0] = int(csv_cont[row][0])
            except ValueError:
                pass

    def get_comid_list(self, csv_cont):
        """
        Converts cells to floats if possible
        (modifies input CSV content list).

        """
        comid_list = []
        for row in range(len(csv_cont)):
            try:
                comid_list.append(int(csv_cont[row][0]))
            except ValueError:
                pass
        return comid_list

    def sort_by_column(self, csv_cont, col, reverse=False):
        """
        Sorts CSV contents by column name (if col argument is type <str>)
        or column index (if col argument is type <int>).

        """
        header = csv_cont[0]
        body = csv_cont[1:]
        if isinstance(col, str):
            col_index = header.index(col)
        else:
            col_index = col
        body = sorted(body,
               key=operator.itemgetter(col_index),
               reverse=reverse)
        body.insert(0, header)
        return body

    def find_comid_weight_table(self, comid, weight_table):
        """
        Gives COMID row of weight table and remove it

        """
        for row in range(len(weight_table)):
            if weight_table[row][0] == comid:
                comid_row =  weight_table[row]
                weight_table.remove(comid_row)
                return comid_row
        return None


    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name="in_weight_table",
                                 displayName="Input Weight Table",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="DEFile")

        param1 = arcpy.Parameter(name = 'in_network_connectivity_file',
                                 displayName = 'Input Network Connectivity File',
                                 direction = 'Input',
                                 parameterType = 'Required',
                                 datatype = 'DEFile')

        param2 = arcpy.Parameter(name = "out_weight_table",
                                 displayName = "Output Weight Table",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        params = [param0, param1, param2]

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
                parameters[2].value = os.path.join(dirnm, "{}.csv".format(basenm))

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        in_WeightTable = parameters[0].valueAsText
        in_ConnectivityFile = parameters[1].valueAsText
        out_WeightTable = parameters[2].valueAsText

        #get all flowline comids
        connectivity = self.csv_to_list(in_ConnectivityFile)
        all_flowline_comid = self.get_comid_list(connectivity)

        #get all catchment comids
        weight_table = self.csv_to_list(in_WeightTable)
        self.convert_comid_to_int(weight_table)

        #FEATUREID,area_sqm,lon_index,lat_index,npoints,weight,Lon,Lat
        new_weight_table = weight_table[0:1][:]

        replacement_row = weight_table[1][1:]
        #set area_sqm to zero
        replacement_row[0] = 0
        #set npoints to one
        replacement_row[3] = 1

        for comid in all_flowline_comid:
            #delete rows in catchment but not in flowline
            new_row = self.find_comid_weight_table(comid, weight_table)
            row_count = 0
            while new_row:
                new_weight_table.append(new_row)
                new_row = self.find_comid_weight_table(comid, weight_table)
                row_count += 1
            if row_count <= 0:
                #add rows for each flowline not in catchment
                new_replacement_row = [comid]
                new_replacement_row.extend(replacement_row)
                #FEATUREID,area_sqm,lon_index,lat_index,npoints,weight,Lon,Lat
                new_weight_table.append(new_replacement_row)


        #print to file
        with open(out_WeightTable, 'wb') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(new_weight_table)



        return
