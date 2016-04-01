'''-------------------------------------------------------------------------------
 Tool Name:   CreateDischargeMap
 Source Name: CreateDischargeMap.py
 Version:     ArcGIS 10.3
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Create a dischage map document.
 History:     Initial coding - 05/8/2015, version 1.0
 Updated:     Version 1.0, 06/02/2015, rename the default template layer file names
                from FGDB_TimeEnabled_5NaturalBreaks.lyr and SQL_TimeEnabled_5NaturalBreaks.lyr
                to FGDB_TimeEnabled.lyr and SQL_TimeEnabled.lyr
              Version 1.1, 06/24/2015, add all layers into a group layer named as "AllScales",
                which is specified in the template .mxd
-------------------------------------------------------------------------------'''
import os
import arcpy
import numpy as NUM
import netCDF4 as NET
import time

class CreateDischargeMap(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Discharge Map"
        self.description = "Create a discharge map document for stream flow visualization based on \
                            the discharge table and the drainage line feature class"
        self.name_ID = "COMID"
        self.GDBtemplate_layer = os.path.join(os.path.dirname(__file__), "templates", "FGDB_TimeEnabled.lyr")
        self.SQLtemplate_layer = os.path.join(os.path.dirname(__file__), "templates", "SQL_TimeEnabled.lyr")
        self.template_mxd = os.path.join(os.path.dirname(__file__), "templates", "template_mxd.mxd")
        self.name_df = "DischargeMap"
        self.field_streamOrder = "StreamOrde"
        # Define the minScale and maxScale for each layer and its corresponding threshold for query definition about StreamOrder
##        self.layer_minScale_maxScale_query = {"High": [750000, None, None],
##                                                    "Medium": [3000000, 750000, "StreamOrde >= 3"],
##                                                    "Low":[None, 3000000, "StreamOrde >= 5"]}
        self.layer_minScale_maxScale_query = {"All": [None, None, None]}
        self.canRunInBackground = False
        self.category = "Postprocessing"

    def copyFlowlines(self, in_drainage_line, path_database, list_uniqueID):
        """Create copies of flowlines based on the layer query definitions"""
        # make a feature layer for query selection
        name_lyr = "flowlines"
        arcpy.MakeFeatureLayer_management(in_drainage_line, name_lyr)

        '''Create the query expression for line features with matching records in the flat table'''
        expression_base = self.name_ID + " IN ("
        count = len(list_uniqueID)
        counter = 1
        for each_ID in list_uniqueID:
            if counter == count:
                expression_base = expression_base + str(each_ID) + ")"
            else:
                expression_base = expression_base + str(each_ID) + ", "
            counter += 1


        for each_key in self.layer_minScale_maxScale_query.keys():
            out_copy = os.path.join(path_database, "Flowline_"+each_key)
            pars = self.layer_minScale_maxScale_query[each_key]
            query = pars[2]
            expression = expression_base
            if query is not None:
                expression = expression_base + "AND " + query

            arcpy.SelectLayerByAttribute_management(name_lyr, "NEW_SELECTION", expression)
            arcpy.CopyFeatures_management(name_lyr, out_copy)
            arcpy.AddIndex_management(out_copy, self.name_ID, self.name_ID, "UNIQUE", "ASCENDING")

        return


    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_drainage_line",
                                 displayName = "Input Drainage Line Features",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPFeatureLayer")

        param1 = arcpy.Parameter(name = "in_discharge_table",
                                 displayName = "Input Discharge Table",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DETable")

        param2 = arcpy.Parameter(name = "out_discharge_map",
                                 displayName = "Output Discharge Map",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DEMapDocument"
                                 )

        param3 = arcpy.Parameter(name = "in_unique_ID_table",
                                 displayName = "Input Unique ID Table",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "DETable")

        param4 = arcpy.Parameter(name = "in_layer_info",
                                 displayName = "Input Layer Information",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "GPValueTable")
        param4.columns = [['String', 'Layer Name'], ['Long', 'Minimum Scale'], ['Long', 'Maximum Scale'], ['Long', 'Minimum Stream Order']]


        params = [param0, param1, param2, param3, param4]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        '''Add .mxd suffix to the output map document name'''
        if parameters[2].altered:
            (dirnm, basenm) = os.path.split(parameters[2].valueAsText)
            if not basenm.endswith(".mxd"):
                parameters[2].value = os.path.join(dirnm, "{}.mxd".format(basenm))
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        in_drainage_line = parameters[0].valueAsText
        in_flat_table = parameters[1].valueAsText
        out_map_document = parameters[2].valueAsText
        in_uniqueID_table = parameters[3].valueAsText
        in_layer_info = parameters[4].value
##        in_drainage_line = r'C:\temp\TestVisualization\Experiment2.gdb\NHDFLowlineRegion12_wStreamLeve'
##        in_flat_table = r'D:\Temp\RAPIDVisualization.gdb\Flow_map'


        ''' Obtain a list of unique IDs '''
        list_uniqueID = []
        if in_uniqueID_table is not None:
            arr_uniqueID = arcpy.da.TableToNumPyArray(in_uniqueID_table, self.name_ID)
            arr_uniqueID = arr_uniqueID[self.name_ID]
            list_uniqueID = list(arr_uniqueID)
        else:
            arr_ID = arcpy.da.TableToNumPyArray(in_flat_table, self.name_ID)
            arr_ID = arr_ID[self.name_ID]
            list_uniqueID = list(NUM.unique(arr_ID))


        ''' Update self.layer_minScale_maxScale_query if user defines the map layer information'''
        if in_layer_info is not None:
            self.layer_minScale_maxScale_query = {}
            for each_list in in_layer_info:
                layer_minScale = None
                layer_maxScale = None
                layer_query = None

                if each_list[1] > 0:
                    layer_minScale = each_list[1]
                if each_list[2] > 0:
                    layer_maxScale = each_list[2]
                if each_list[3] > 0:
                    layer_query = self.field_streamOrder + " >= " + str(each_list[3])

                key_in_dict = each_list[0]
                list_in_dict = [layer_minScale, layer_maxScale, layer_query]
                self.layer_minScale_maxScale_query[key_in_dict] = list_in_dict


        # Get the database path of the flat table
        (dirnm, basenm) = os.path.split(in_flat_table)

        '''Copy Flow line features and add attribute index'''
        self.copyFlowlines(in_drainage_line, dirnm, list_uniqueID)

        '''Create Map Document'''
        mxd = arcpy.mapping.MapDocument(self.template_mxd)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        df.name = self.name_df

        mxd.saveACopy(out_map_document)
        del mxd, df

        template_lyr = self.GDBtemplate_layer
        if not dirnm.endswith('.gdb'):
            template_lyr = self.SQLtemplate_layer


        for each_key in self.layer_minScale_maxScale_query.keys():
            mxd = arcpy.mapping.MapDocument(out_map_document)
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            targetGroupLayer = arcpy.mapping.ListLayers(mxd, "AllScales", df)[0]
            lyrFile = arcpy.mapping.Layer(template_lyr)

            out_flowlines = os.path.join(dirnm, "Flowline_"+each_key)
            # Create Layer
            lyr = arcpy.mapping.Layer(out_flowlines)

            # Add join to layer
            arcpy.AddJoin_management(lyr, self.name_ID, in_flat_table, self.name_ID, "KEEP_COMMON")

            # Set min and max scales for layers
            minScale = self.layer_minScale_maxScale_query[each_key][0]
            maxScale = self.layer_minScale_maxScale_query[each_key][1]

            if minScale is not None:
                lyr.minScale = minScale
            if maxScale is not None:
                lyr.maxScale = maxScale

            # Apply symbology from template
            arcpy.ApplySymbologyFromLayer_management(lyr, template_lyr)

            # Add layer
            arcpy.mapping.AddLayerToGroup(df, targetGroupLayer, lyr, "BOTTOM")

            mxd.save()
            del mxd, df, lyr, targetGroupLayer

        # Update layer time property
        for each_key in self.layer_minScale_maxScale_query.keys():
            mxd = arcpy.mapping.MapDocument(out_map_document)
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            lyr = arcpy.mapping.ListLayers(mxd, "Flowline_"+each_key, df)[0]
            arcpy.mapping.UpdateLayerTime(df, lyr, lyrFile)

            dft = df.time
            dft.startTime = lyr.time.startTime
            dft.endTime = lyr.time.endTime

            mxd.save()
            del mxd, df, lyr


        # Add the flat table into map: as a workaround for a potential bug in publishing
        mxd = arcpy.mapping.MapDocument(out_map_document)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        flat_Table = arcpy.mapping.TableView(in_flat_table)
        arcpy.mapping.AddTableView(df, flat_Table)

        mxd.save()
        del mxd, df, flat_Table



        return

##def main():
##    tool = CreateMapDocument()
##    tool.execute(tool.getParameterInfo(), None)
##
##if __name__ == '__main__':
##    main()


