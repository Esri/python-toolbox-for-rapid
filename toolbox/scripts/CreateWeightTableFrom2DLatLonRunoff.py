'''-------------------------------------------------------------------------------
 Tool Name:   CreateWeightTableFrom2DLatLonRunoff
 Source Name: CreateWeightTableFrom2DLatLonRunoff.py
 Version:     ArcGIS 10.3
 Author:      Alan Dee Snow
 Description: Creates RAPID inflow file based on 2D Latitude and Longitude runoff output
              and the weight table previously created.
 History:     Initial coding - 9/30/2015, version 1.0
 ------------------------------------------------------------------------------'''
import os
import arcpy
import netCDF4 as NET
import numpy as NUM
import csv

class CreateWeightTableFrom2DLatLonRunoff(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Weight Table From 2D Lat Lon LSM Grid Runoff"
        self.description = ("Creates RAPID inflow file based on 2D Latitude and Longitude runoff output" +
                            " and catchment features")
        self.canRunInBackground = False
        self.errorMessages = ["Incorrect dimensions in the input LIS runoff file.",
                              "Incorrect variables in the input LIS runoff file."]
        self.category = "Preprocessing"


    def dataValidation(self, in_nc, messages):
        """Check the necessary dimensions and variables in the input netcdf data"""
        return

    def createPolygon(self, extent, out_polygons, scratchWorkspace):
        """Create a Thiessen polygon feature class from numpy.ndarray lat and lon
           Each polygon represents the area described by the center point
        """
        lsm_dx = NUM.max(NUM.absolute(NUM.diff(self.lsm_lon_array)))
        lsm_dy = NUM.max(NUM.absolute(NUM.diff(self.lsm_lat_array, axis=0)))
        
        lsm_lat_indices_from_lat, lsm_lon_indices_from_lat = NUM.where((self.lsm_lat_array >= (extent.YMin - 2*lsm_dy)) & (self.lsm_lat_array <= (extent.YMax + 2*lsm_dy)))
        lsm_lat_indices_from_lon, lsm_lon_indices_from_lon = NUM.where((self.lsm_lon_array >= (extent.XMin - 2*lsm_dx)) & (self.lsm_lon_array <= (extent.XMax + 2*lsm_dx)))

        lsm_lat_indices = NUM.intersect1d(lsm_lat_indices_from_lat, lsm_lat_indices_from_lon)
        lsm_lon_indices = NUM.intersect1d(lsm_lon_indices_from_lat, lsm_lon_indices_from_lon)

        lsm_lat_list = self.lsm_lat_array[lsm_lat_indices,:][:,lsm_lon_indices]
        lsm_lon_list = self.lsm_lon_array[lsm_lat_indices,:][:,lsm_lon_indices]

        # Spatial reference
        sr = arcpy.SpatialReference(4326) #CGS_WGS_1984

        # Create a list of geographic coordinate pairs
        pointGeometryList = []
        for i in range(len(lsm_lat_indices)):
            for j in range(len(lsm_lon_indices)):
                point = arcpy.Point()
                point.X = float(lsm_lon_list[i][j])
                point.Y = float(lsm_lat_list[i][j])
                pointGeometry = arcpy.PointGeometry(point, sr)
                pointGeometryList.append(pointGeometry)

        # Create a point feature class with longitude in Point_X, latitude in Point_Y
        out_points = os.path.join(scratchWorkspace, 'points_subset')
        result2 = arcpy.CopyFeatures_management(pointGeometryList, out_points)
        out_points = result2.getOutput(0)
        arcpy.AddGeometryAttributes_management(out_points, 'POINT_X_Y_Z_M')

        # Create Thiessen polygon based on the point feature
        result3 = arcpy.CreateThiessenPolygons_analysis(out_points, out_polygons, 'ALL')
        out_polygons = result3.getOutput(0)

        return out_points, out_polygons

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
        param0 = arcpy.Parameter(name = "in_runoff_file",
                                 displayName = "Input Runoff File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param1 = arcpy.Parameter(name = "in_lat_variable",
                                 displayName = "2D Latitude Variable [-90,90]",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")
        param1.filter.list = []

        param2 = arcpy.Parameter(name = "in_lon_variable",
                                 displayName = "2D Longitude Variable [-180,180]",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")
        param2.filter.list = []

        param3 = arcpy.Parameter(name="in_rapid_connect_file",
                                 displayName="Input RAPID Connect File",
                                 direction="Input",
                                 parameterType="Required",
                                 datatype="DEFile")

        param4 = arcpy.Parameter(name = "in_catchment_features",
                                 displayName = "Input Catchment Features",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPFeatureLayer")

        param4.filter.list = ['Polygon']

        param5 = arcpy.Parameter(name = "stream_ID",
                                 displayName = "Stream ID",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        param5.parameterDependencies = ["in_catchment_features"]
        param5.filter.list = ['Short', 'Long']


        param6 = arcpy.Parameter(name="out_weight_table",
                                 displayName="Output Weight Table",
                                 direction="Output",
                                 parameterType="Required",
                                 datatype="DEFile")

        params = [param0, param1, param2, param3, param4, param5, param6]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[6].valueAsText is None:
                scratchWorkspace = arcpy.env.scratchWorkspace
                if not scratchWorkspace:
                    scratchWorkspace = arcpy.env.scratchGDB
                parameters[6].value = os.path.join(scratchWorkspace, "Weight_Table.csv")

        if parameters[6].altered:
            (dirnm, basenm) = os.path.split(parameters[6].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[6].value = os.path.join(dirnm, "{}.csv".format(basenm))

        if parameters[0].altered:
            #get list of variables in the netcdf file
            data_nc = NET.Dataset(parameters[0].valueAsText)
            variables_list = data_nc.variables.keys()
            dimensions_list = data_nc.dimensions.keys()
            data_nc.close()
            parameters[1].filter.list = variables_list
            parameters[2].filter.list = variables_list
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[0].altered:
            in_nc = parameters[0].valueAsText
            try:
                data_nc = NET.Dataset(in_nc)
                data_nc.close()
            except Exception as e:
                parameters[0].setErrorMessage(e.message)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        scratchWorkspace = arcpy.env.scratchWorkspace
        if not scratchWorkspace:
            scratchWorkspace = arcpy.env.scratchGDB

        in_nc = parameters[0].valueAsText
        in_nc_lat_var = parameters[1].valueAsText
        in_nc_lon_var = parameters[2].valueAsText
        in_rapid_connect_file = parameters[3].valueAsText
        in_catchment = parameters[4].valueAsText
        streamID = parameters[5].valueAsText
        out_WeightTable = parameters[6].valueAsText

        # validate the netcdf dataset
        self.dataValidation(in_nc, messages)

        # Obtain catchment extent in lat and lon in GCS_WGS_1984
        sr_cat = arcpy.Describe(in_catchment).SpatialReference
        extent = arcpy.Describe(in_catchment).extent
        #if (sr_cat.name == 'World_Equidistant_Cylindrical'):
        if (sr_cat.name == 'GCS_WGS_1984'):
            extent = extent
        else:
            envelope = os.path.join(scratchWorkspace, 'envelope')
            result0 = arcpy.MinimumBoundingGeometry_management(in_catchment, envelope, 'ENVELOPE', 'ALL')
            envelope = result0.getOutput(0)
            sr_out = arcpy.SpatialReference(4326) # GCS_WGS_1984
            envelope_proj = os.path.join(scratchWorkspace,'envelope_proj')
            result1 = arcpy.Project_management(envelope, envelope_proj, sr_out)
            envelope_proj = result1.getOutput(0)
            extent = arcpy.Describe(envelope_proj).extent

        #Open nc file
        data_nc = NET.Dataset(in_nc)

        # Obtain geographic coordinates
        self.lsm_lon_array = data_nc.variables[in_nc_lon_var][:] #assume [-180, 180]
        self.lsm_lat_array = data_nc.variables[in_nc_lat_var][:] #assume [-90,90]
        data_nc.close()
        
        #convert 3d to 2d if time dimension
        if(len( self.lsm_lon_array.shape) == 3):
            self.lsm_lon_array = self.lsm_lon_array[0]
            self.lsm_lat_array = self.lsm_lat_array[0]

        # Create Thiessen polygons based on the points within the extent
        arcpy.AddMessage("Generating Thiessen polygons...")
        polygon_thiessen = os.path.join(scratchWorkspace,'polygon_thiessen')
        
        result4 = self.createPolygon(extent, polygon_thiessen, scratchWorkspace)
        polygon_thiessen = result4[1]

        # Intersect the catchment polygons with the Thiessen polygons
        arcpy.AddMessage("Intersecting Thiessen polygons with catchment...")
        intersect = os.path.join(scratchWorkspace, 'intersect')
        result5 = arcpy.Intersect_analysis([in_catchment, polygon_thiessen], intersect, 'ALL', '#', 'INPUT')
        intersect = result5.getOutput(0)

        # Calculate the geodesic area in square meters for each intersected polygon (no need to project if it's not projected yet)
        arcpy.AddMessage("Calculating geodesic areas...")
        arcpy.AddGeometryAttributes_management(intersect, 'AREA_GEODESIC', '', 'SQUARE_METERS', '')

        # Calculate the total geodesic area of each catchment based on the contributing areas of points
        fields = [streamID, 'POINT_X', 'POINT_Y', 'AREA_GEO']
        area_arr = arcpy.da.FeatureClassToNumPyArray(intersect, fields)

        arcpy.AddMessage("Writing the weight table...")
        #get list of COMIDs in rapid_connect file so only those are included in computations
        connectivity_table = self.csvToList(in_rapid_connect_file)
        streamID_unique_arr = [int(row[0]) for row in connectivity_table]

        #if point not in array append dummy data for one point of data
        lon_dummy = area_arr['POINT_X'][0]
        lat_dummy = area_arr['POINT_Y'][0]
        #find point index in 2d grid
        lsm_lat_indices_from_lat, lsm_lon_indices_from_lat = NUM.where(self.lsm_lat_array == lat_dummy)
        lsm_lat_indices_from_lon, lsm_lon_indices_from_lon = NUM.where(self.lsm_lon_array == lon_dummy)

        index_lat_dummy = NUM.intersect1d(lsm_lat_indices_from_lat, lsm_lat_indices_from_lon)[0]
        index_lon_dummy = NUM.intersect1d(lsm_lon_indices_from_lat, lsm_lon_indices_from_lon)[0]

        with open(out_WeightTable, 'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect = 'excel')
            connectwriter.writerow([streamID, 'area_sqm', 'lon_index', 'lat_index', 'npoints'])
            for streamID_unique in streamID_unique_arr:
                ind_points = NUM.where(area_arr[streamID]==streamID_unique)[0]
                num_ind_points = len(ind_points)

                if num_ind_points <= 0:
                    #FEATUREID,area_sqm,lon_index,lat_index,npoints,Lon,Lat
                    connectwriter.writerow([streamID_unique, 0, index_lon_dummy, index_lat_dummy, 1])
                else:
                    for ind_point in ind_points:
                        area_geo_each = float(area_arr['AREA_GEO'][ind_point])
                        lon_each = area_arr['POINT_X'][ind_point]
                        lat_each = area_arr['POINT_Y'][ind_point]
                        
                        #find point index in 2d grid
                        lsm_lat_indices_from_lat, lsm_lon_indices_from_lat = NUM.where(self.lsm_lat_array == lat_each)
                        lsm_lat_indices_from_lon, lsm_lon_indices_from_lon = NUM.where(self.lsm_lon_array == lon_each)

                        index_lat_each = NUM.intersect1d(lsm_lat_indices_from_lat, lsm_lat_indices_from_lon)[0]
                        index_lon_each = NUM.intersect1d(lsm_lon_indices_from_lat, lsm_lon_indices_from_lon)[0]

                        #write to file
                        connectwriter.writerow([streamID_unique, area_geo_each, index_lon_each, 
                                                index_lat_each, num_ind_points])

        return
