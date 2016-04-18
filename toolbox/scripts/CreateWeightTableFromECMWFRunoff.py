'''-------------------------------------------------------------------------------
 Tool Name:   CreateWeightTableFromECMWFRunoff
 Source Name: CreateWeightTableFromECMWFRunoff.py
 Version:     ArcGIS 10.3
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Creates RAPID inflow file based on ECMWF runoff output
              and the weight table previously created.
 History:     Initial coding - 10/21/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014, modified names of tool and parameters
              Version 1.0, 10/28/2014, added data validation
              Version 1.1, 10/30/2014, added lon_index, lat_index in output weight table
              Version 1.1, 11/07/2014, bug fixing - enables input catchment feature class
                with spatial reference that is not PCS_WGS_1984.
              Version 2.0, 06/04/2015, integrated Update Weight Table (according to Alan Snow, US Army ERDC)
-------------------------------------------------------------------------------'''
import os
import arcpy
import netCDF4 as NET
import numpy as NUM
import csv

class CreateWeightTableFromECMWFRunoff(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Weight Table From ECMWF Runoff"
        self.description = ("Creates weight table based on the ECMWF Runoff file" +
                            " and catchment features")
        self.canRunInBackground = False
        self.dims_oi = [['lon', 'lat', 'time'], 
                        ['longitude', 'latitude', 'time'],
                        ['lon', 'lat'], 
                        ['longitude', 'latitude']]
        self.vars_oi = [["lon", "lat", "time", "RO"],
                        ["longitude", "latitude", "time", "ro"],
                        ["lon", "lat"],
                        ["longitude", "latitude"]]
        self.errorMessages = ["Incorrect dimensions in the input ECMWF runoff file.",
                              "Incorrect variables in the input ECMWF runoff file."]
        self.category = "Preprocessing"

    def dataValidation(self, in_nc, messages):
        """Check the necessary dimensions and variables in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)

        dims = data_nc.dimensions.keys()
        if dims not in self.dims_oi:
            messages.addErrorMessage(self.errorMessages[0])
            raise arcpy.ExecuteError

        vars = data_nc.variables.keys()
        if vars not in self.vars_oi:
            messages.addErrorMessage(self.errorMessages[1])
            raise arcpy.ExecuteError

        return

    def createPolygon(self, lat, lon, extent, out_polygons, scratchWorkspace):
        """Create a Thiessen polygon feature class from numpy.ndarray lat and lon
           Each polygon represents the area described by the center point
        """
        buffer = 2 * max(abs(lat[0]-lat[1]),abs(lon[0] - lon[1]))
        # Extract the lat and lon within buffered extent (buffer with 2* interval degree)
        lat0 = lat[(lat >= (extent.YMin - buffer)) & (lat <= (extent.YMax + buffer))]
        lon0 = lon[(lon >= (extent.XMin - buffer)) & (lon <= (extent.XMax + buffer))]
        # Spatial reference: GCS_WGS_1984
        sr = arcpy.SpatialReference(4326)

        # Create a list of geographic coordinate pairs
        pointGeometryList = []
        for i in range(len(lon0)):
            for j in range(len(lat0)):
                point = arcpy.Point()
                point.X = float(lon0[i])
                point.Y = float(lat0[j])
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
        param0 = arcpy.Parameter(name = "in_ECMWF_runoff_file",
                                 displayName = "Input ECMWF Runoff File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param1 = arcpy.Parameter(name = "in_network_connectivity_file",
                                 displayName = "Input Network Connecitivity File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param2 = arcpy.Parameter(name = "in_catchment_features",
                                 displayName = "Input Catchment Features",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPFeatureLayer")

        param2.filter.list = ['Polygon']


        param3 = arcpy.Parameter(name = "stream_ID",
                                 displayName = "Stream ID",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "Field"
                                 )
        param3.parameterDependencies = ["in_catchment_features"]
        param3.filter.list = ['Short', 'Long']


        param4 = arcpy.Parameter(name="out_weight_table",
                                 displayName="Output Weight Table",
                                 direction="Output",
                                 parameterType="Required",
                                 datatype="DEFile")

        param5 = arcpy.Parameter(name = "out_cg_polygon_feature_class",
                                 displayName = "Output Computational Grid Polygon Feature Class",
                                 direction = "Output",
                                 parameterType = "Optional",
                                 datatype = "DEFeatureClass")

        param6 = arcpy.Parameter(name = "out_cg_point_feature_class",
                                 displayName = "Output Computational Grid Point Feature Class",
                                 direction = "Output",
                                 parameterType = "Optional",
                                 datatype = "DEFeatureClass")


        params = [param0, param1, param2, param3, param4, param5, param6]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].valueAsText is not None and parameters[2].valueAsText is not None \
            and parameters[3].valueAsText is not None and parameters[4].valueAsText is None:
                scratchWorkspace = arcpy.env.scratchWorkspace
                if not scratchWorkspace:
                    scratchWorkspace = arcpy.env.scratchGDB
                parameters[4].value = os.path.join(scratchWorkspace, "Weight_Table.csv")

        if parameters[4].altered:
            (dirnm, basenm) = os.path.split(parameters[4].valueAsText)
            if not basenm.endswith(".csv"):
                parameters[4].value = os.path.join(dirnm, "{}.csv".format(basenm))

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
    
    def find_nearest(self, array, value):
        """Gets value in array closest to the value searching for"""
        return (NUM.abs(array-value)).argmin()
        
    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True

        scratchWorkspace = arcpy.env.scratchWorkspace
        if not scratchWorkspace:
            scratchWorkspace = arcpy.env.scratchGDB

        in_nc = parameters[0].valueAsText
        in_rapid_connect_file = parameters[1].valueAsText
        in_catchment = parameters[2].valueAsText
        streamID = parameters[3].valueAsText
        out_WeightTable = parameters[4].valueAsText
        out_CGPolygon = parameters[5].valueAsText
        out_CGPoint = parameters[6].valueAsText

        # validate the netcdf dataset
        self.dataValidation(in_nc, messages)

        # Obtain catchment extent in lat and lon in GCS_WGS_1984
        sr_cat = arcpy.Describe(in_catchment).SpatialReference
        extent = arcpy.Describe(in_catchment).extent
        if (sr_cat.name == 'GCS_WGS_1984'):
            extent = extent
        else:
            envelope = os.path.join(scratchWorkspace, 'envelope')
            result0 = arcpy.MinimumBoundingGeometry_management(in_catchment, envelope, 'ENVELOPE', 'ALL')
            envelope = result0.getOutput(0)
            sr_out = arcpy.SpatialReference(4326)  # 'GCS_WGS_1984'
            envelope_proj = os.path.join(scratchWorkspace,'envelope_proj')
            result1 = arcpy.Project_management(envelope, envelope_proj, sr_out)
            envelope_proj = result1.getOutput(0)
            extent = arcpy.Describe(envelope_proj).extent


        #Open nc file
        """ Variables in the netcdf file 1-51
            lat (1D): -89.78 to 89.78 by 0.28 (Size: 640)
            lon (1D): 0.0 to 359.72 by 0.28 (Size: 1280)
            RO (Geo2D): runoff (3 dimensions)
            time (1D): 0 to 360 by 6 (Size: 61)
        """
        """ Variables in the netcdf file 52 (High Resolution)
            lat (1D): -89.89 to 89.89 by 0.14 (Size: 1280)
            lon (1D): 0.0 to 359.86 by 0.14 (Size: 2560)
            RO (Geo2D): runoff (3 dimensions)
            time (1D): 0 to 240 (0 to 90 by 1, 90 to 144 by 3, 144 to 240 by 6) (Size: 125)
        """

        data_nc = NET.Dataset(in_nc)

        # Obtain geographic coordinates
        variables_list = data_nc.variables.keys()
        lat_var = 'lat'
        if 'latitude' in variables_list:
            lat_var = 'latitude'
        lon_var = 'lon'
        if 'longitude' in variables_list:
            lon_var = 'longitude'
        lon = (data_nc.variables[lon_var][:] + 180) % 360 - 180 # convert [0, 360] to [-180, 180]
        lat = data_nc.variables[lat_var][:]

        data_nc.close()

        # Create Thiessen polygons based on the points within the extent
        arcpy.AddMessage("Generating Thiessen polygons...")
        polygon_thiessen = os.path.join(scratchWorkspace,'polygon_thiessen')
        result4 = self.createPolygon(lat, lon, extent, polygon_thiessen, scratchWorkspace)
        polygon_thiessen = result4[1]


        # Output Thiessen polygons (computational grid polygons) and CG points if they are specified.
        if out_CGPolygon and out_CGPolygon != polygon_thiessen:
            arcpy.CopyFeatures_management(polygon_thiessen, out_CGPolygon)
        if out_CGPoint and out_CGPoint != result4[0]:
            arcpy.CopyFeatures_management(result4[0], out_CGPoint)


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
        # Get list of COMIDs in rapid_connect file so only those area included in computations
        connectivity_table = self.csvToList(in_rapid_connect_file)
        streamID_unique_list = [int(row[0]) for row in connectivity_table]

        #if point not in array append dummy data for one point of data
        lon_dummy = area_arr['POINT_X'][0]
        lat_dummy = area_arr['POINT_Y'][0]
        try:
            index_lon_dummy = int(NUM.where(lon == lon_dummy)[0])
        except TypeError as ex:
            #This happens when near meridian - lon_dummy ~ 0
            #arcpy.AddMessage("GRIDID: %s" % streamID_unique)
            #arcpy.AddMessage("Old Lon: %s" % lon_dummy)
            index_lon_dummy = int(self.find_nearest(lon, lon_dummy))
            #arcpy.AddMessage("Lon Index: %s" % index_lon_dummy)
            #arcpy.AddMessage("Lon Val: %s" % lon[index_lon_dummy])
            pass
            
        try:
            index_lat_dummy= int(NUM.where(lat == lat_dummy)[0])
        except TypeError as ex:
            #This happens when near equator - lat_dummy ~ 0
            #arcpy.AddMessage("GRIDID: %s" % streamID_unique)
            #arcpy.AddMessage("Old Lat: %s" % lat_dummy)
            index_lat_dummy = int(self.find_nearest(lat, lat_dummy))
            #arcpy.AddMessage("Lat Index: %s" % index_lat_dummy)
            #arcpy.AddMessage("Lat Val: %s" % lat[index_lat_dummy])
            pass

        # Output the weight table
        with open(out_WeightTable, 'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect = 'excel')
            #header
            connectwriter.writerow([streamID, 'area_sqm', 'lon_index', 'lat_index', 
                                    'npoints', 'lon', 'lat'])

            for streamID_unique in streamID_unique_list:
                ind_points = NUM.where(area_arr[streamID]==streamID_unique)[0]
                num_ind_points = len(ind_points)

                if num_ind_points <= 0:
                    # if point not in array, append dummy data for one point of data
                    # streamID, area_sqm, lon_index, lat_index, npoints
                    connectwriter.writerow([streamID_unique, 0, index_lon_dummy, index_lat_dummy,
                                            1, lon_dummy, lat_dummy])
                else:
                    for ind_point in ind_points:
                        area_geo_each = float(area_arr['AREA_GEO'][ind_point])
                        lon_each = area_arr['POINT_X'][ind_point]
                        lat_each = area_arr['POINT_Y'][ind_point]
                        try:
                            index_lon_each = int(NUM.where(lon == lon_each)[0])
                        except TypeError as ex:
                            #This happens when near meridian - lon_each ~ 0
                            index_lon_each = int(self.find_nearest(lon, lon_each))
                            #arcpy.AddMessage("GRIDID: %s" % streamID_unique)
                            #arcpy.AddMessage("Old Lon: %s" % lon_each)
                            #arcpy.AddMessage("Lon Index: %s" % index_lon_each)
                            #arcpy.AddMessage("Lon Val: %s" % lon[index_lon_each])
                            pass
                            
                        try:
                            index_lat_each = int(NUM.where(lat == lat_each)[0])
                        except TypeError as ex:
                            #This happens when near equator - lat_each ~ 0
                            index_lat_each = int(self.find_nearest(lat, lat_each))
                            #arcpy.AddMessage("GRIDID: %s" % streamID_unique)
                            #arcpy.AddMessage("Old Lat: %s" % lat_each)
                            #arcpy.AddMessage("Lat Index: %s" % index_lat_each)
                            #arcpy.AddMessage("Lat Val: %s" % lat[index_lat_each])
                            pass
                        connectwriter.writerow([streamID_unique, area_geo_each, index_lon_each, index_lat_each, 
                                                num_ind_points, lon, lat])
        return
