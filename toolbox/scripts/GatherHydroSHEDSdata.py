'''-------------------------------------------------------------------------------
 Tool Name:   GatherHydroSHEDSdata
 Source Name: GatherHydroSHEDSdata.py
 Version:     ArcGIS 10.3
 License:     Apache 2.0
 Author:      Andrew Dohmann
 Updated by:  Andrew Dohmann
 Description: Produces 
 History:     Initial coding - 06/28/2016, version 1.0
 Updated:     Version 1.1, 06/29/2016, initial coding
-------------------------------------------------------------------------------'''
import ArcHydroTools
import arcpy
import os
import math

class GatherHydroSHEDSdata(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Gather HydroSHEDS data"
        self.description = ("downloads DEM and Flowdirection data from HydroSHEDS website")
        self.canRunInBackground = False
        self.category = "Preprocessing"

    def getParameterInfo(self):
        """Define parameter definitions"""
        Watershed_Boundary = arcpy.Parameter(name="Watershed_Boundary",
                                            displayName="Watershed Boundary",
                                            direction="Input",
                                            parameterType="Required",
                                            datatype="DEFeatureClass")
                                            
        DEM_Location = arcpy.Parameter(name="DEM_Location",
                                       displayName="DEM_Location",
                                       direction="Input",
                                       parameterType="Required",
                                       datatype="DEFolder")
                                            
        FlowDir_Location = arcpy.Parameter(name="FlowDir_LocationFlowDir_Location",
                                           displayName="FlowDir_Location",
                                           direction="Input",
                                           parameterType="Optional",
                                           datatype="DEFolder")
                                            

        params = [Watershed_Boundary, 
                  DEM_Location, 
                  FlowDir_Location]

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
        Watershed_Boundary = parameters[0].valueAsText
        DEM_Location = parameters[1].valueAsText
        FlowDir_Location = parameters[2].valueAsText
        
        #Determine what data needs to be downloaded
        desc = arcpy.Describe(Watershed_Boundary)
        #rectangular bounds of watershed
        xmin = desc.extent.XMin
        xmax = desc.extent.XMax
        ymin = desc.extent.YMin
        ymax = desc.extent.YMax
        #bounds of Hydrosheds data needed
        newxmin = int(math.floor(xmin/5.0) * 5)
        newxmax = int(math.ceil(xmax/5.0) * 5)
        newymin = int(math.floor(ymin/5.0) * 5)
        newymax = int(math.ceil(ymax/5.0) * 5)
        #create list of files to download
        xtiles = ((newxmax - newxmin)/5) 
        ytiles = ((newymax-newymin)/5)
        DEMfile_names = []
        FlowDirfile_names = []
        xindex = 0
        yindex = 0
        while xindex < xtiles:
            east = newxmin + (xindex * 5)
            if east >= 0:
                longitude = "e"
                easting = str(east).zfill(3)  #pads with zeros
            else:
                longitude = "w"
                easting = str(-east).zfill(3)  #pads with zeros
            while yindex < ytiles:
                north = newymin + (yindex * 5)
                if north >= 0:
                    latitude = "n"
                    northing = str(north).zfill(2)  #pads with zeros
                else:
                    latitude = "s"
                    northing = str(-north).zfill(2)  #pads with zeros
                DEMname = "%s%s%s%s_con_bil" %(latitude, northing, longitude, easting) 
                DEMfile = "%s%s%s%s_con.bil" %(latitude, northing, longitude, easting)
                DEMlocationName = os.path.join(os.path.join(DEM_Location, DEMname),DEMfile)
                DEMfile_names.append(DEMlocationName)
                if FlowDir_Location:
                    FlowDirname = "%s%s%s%s_dir_grid" %(latitude, northing, longitude, easting)
                    flowdirfile ="%s%s%s%s_dir.grid" %(latitude, northing, longitude, easting)
                    FlowDirlocationName = os.path.join(os.path.join(FlowDir_Location, FlowDirname), flowdirfile)                
                    FlowDirfile_names.append(FlowDirlocationName)
                yindex = yindex + 1
            xindex = xindex + 1
            yindex = 0 

        #Create multivalue input 
        DEMmulivalue = ";".join(DEMfile_names )
        if FlowDir_Location:
            FlowDirmulivalue = ";".join(FlowDirfile_names )
         
        return DEMmulivalue            
