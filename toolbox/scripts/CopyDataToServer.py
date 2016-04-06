'''-------------------------------------------------------------------------------
 Tool Name:   CopyDataToServer
 Source Name: CopyDataToServer.py
 Version:     ArcGIS 10.2
 License:	  Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Copy discharge table and/or NHDFlowLines to a workspace in the
                ArcGIS server machine.
 History:     Initial coding - 06/26/2015, version 1.0
 Updated:
-------------------------------------------------------------------------------'''
import os
import arcpy
import xml.dom.minidom as DOM


class CopyDataToServer(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Copy Data To Server"
        self.description = "Copy discharge table and/or the drainage line features to the ArcGIS \
                            server machine"
        self.fields_oi = ["Time", "COMID", "Qout", "TimeValue"]
        self.name_ID = "COMID"
        self.errorMessages = []
        self.canRunInBackground = False
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_data",
                                 displayName = "Input Discharge Dataset",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPValueTable")
        param0.columns = [['DEType', 'Dataset']]

        param1 = arcpy.Parameter(name = "in_workspace",
                                 displayName = "Input Workspace",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEWorkspace")
        param1.filter.list = ["Local Database", "Remote Database"]

        param2 = arcpy.Parameter(name = "out_workspace",
				 displayName = "Output Workspace",
				 direction = "Output",
				 parameterType = "Derived",
                                 datatype = "DEWorkspace")

        params = [param0, param1, param2]

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
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        in_data = parameters[0].value
        in_workspace_server = parameters[1].valueAsText

        for row in in_data:
            data = row[0]
            name = os.path.basename(str(data))
            if "Discharge_Table" in name:
                outTable = os.path.join(in_workspace_server, name)
                # Copy discharge table
                arcpy.CopyRows_management(data, outTable, '#')
                # Add attribute index to the discharge table
                arcpy.AddIndex_management(outTable, self.fields_oi[1], self.fields_oi[1])
                arcpy.AddIndex_management(outTable, self.fields_oi[3], self.fields_oi[3])
            elif "Flowline_" in name:
                outFlowline = os.path.join(in_workspace_server, name)
                # Copy flowline feature class
                arcpy.CopyFeatures_management(data, outFlowline)
                # Add attribute index to the flowline feature class
                arcpy.AddIndex_management(outFlowline, self.name_ID, self.name_ID, "UNIQUE", "ASCENDING")
            else:
                arcpy.AddMessage("{0} is not copied due to incorrect name".format(name))


        return

