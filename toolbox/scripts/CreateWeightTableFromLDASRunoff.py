'''-------------------------------------------------------------------------------
 Tool Name:   CreateWeightTableFromLDASRunoff
 Source Name: CreateWeightTableFromLDASRunoff.py
 Version:     ArcGIS 10.3
 Author:      Alan Dee Snow
 Description: Creates RAPID inflow file based on LDAS runoff output
              and the weight table previously created.
 History:     Initial coding - 9/30/2015, version 1.0
 ------------------------------------------------------------------------------'''
import os
import arcpy
import netCDF4 as NET
import numpy as NUM
import csv

class CreateWeightTableFromLDASRunoff(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Weight Table From GLDAS/NLDAS Runoff"
        self.description = ("Creates weight table based on the GLDAS/NLDAS Runoff file" +
                            " and catchment features")
        self.canRunInBackground = False
        self.dims_oi = [['g0_lat_0', 'g0_lon_1'], #GLDAS/NLDAS MOSAIC
                        ['lat_110', 'lon_110']] #NLDAS NOAH/VIC
        self.vars_oi = [["SSRUN_GDS0_SFC_ave1h", "BGRUN_GDS0_SFC_ave1h", 'g0_lat_0', 'g0_lon_1'], #GLDAS
                        ["SSRUNsfc_GDS0_SFC_ave1h", "BGRUNsfc_GDS0_SFC_ave1h", 'g0_lat_0', 'g0_lon_1'], #GLDAS
                        ["SSRUN_GDS0_SFC_ave2h", "BGRUN_GDS0_SFC_ave2h", 'g0_lat_0', 'g0_lon_1'], #NLDAS MOSAIC
                        ["SSRUNsfc_GDS0_SFC_ave2h", "BGRUNsfc_GDS0_SFC_ave2h", 'g0_lat_0', 'g0_lon_1'], #NLDAS MOSAIC
                        ["SSRUNsfc_110_SFC_ave2h", "BGRUNsfc_110_SFC_ave2h", 'lat_110', 'lon_110'], #NLDAS NOAH/VIC
                        ["SSRUN_110_SFC_ave2h", "BGRUN_110_SFC_ave2h", 'lat_110', 'lon_110']] #NLDAS NOAH/VIC
        self.errorMessages = ["Incorrect dimensions in the input GLDAS/NLDAS runoff file.",
                              "Incorrect variables in the input GLDAS/NLDAS runoff file."]
        self.category = "Preprocessing"


    def dataValidation(self, in_nc, messages):
        """Check the necessary dimensions and variables in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)

        dims = data_nc.dimensions.keys()
        dim_found = False
        for dim_list in self.dims_oi:
            if dim_list == dims[:2]:
                dim_found = True
                break
        if not dim_found:      
            messages.addErrorMessage(self.errorMessages[0])
            raise arcpy.ExecuteError

        vars = data_nc.variables.keys()
        for var_list in self.vars_oi:
            vars_found = True
            for var in var_list:
                if var not in vars:
                    vars_found = False
                    break
            if vars_found:
                break
                
        if not vars_found:
            messages.addErrorMessage(self.errorMessages[1])
            raise arcpy.ExecuteError
        return

    def createPolygon(self, lat, lon, extent, out_polygons, scratchWorkspace):
        """Create a Thiessen polygon feature class from numpy.ndarray lat and lon
           Each polygon represents the area described by the center point
        """
        buffer = 2 * max(abs(lat[0]-lat[1]),abs(lon[0] - lon[1]))
        # Spatial reference: Cylindrical Equidistant Projection Grid
        #sr = arcpy.SpatialReference(54002)
        sr = arcpy.SpatialReference(4326) #CGS_WGS_1984

        # Extract the lat and lon within buffered extent (buffer with 2* interval degree)
        lat0 = lat[(lat >= (extent.YMin - buffer)) & (lat <= (extent.YMax + buffer))]
        lon0 = lon[(lon >= (extent.XMin - buffer)) & (lon <= (extent.XMax + buffer))]

        # Create a list of geographic coordinate pairs
        count_lon = len(lon0)
        count_lat = len(lat0)
        pointGeometryList = []
        for i in range(0,count_lon):
            for j in range(0, count_lat):
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
        param0 = arcpy.Parameter(name = "in_LDAS_runoff_file",
                                 displayName = "Input GLDAS/NLDAS Runoff File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param1 = arcpy.Parameter(name = "in_LDAS_lat_variable",
                                 displayName = "GLDAS/NLDAS File Latitude Variable [-90,90]",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")
        param1.filter.list = []

        param2 = arcpy.Parameter(name = "in_LDAS_lon_variable",
                                 displayName = "GLDAS/NLDAS File Longitude Variable [-180,180]",
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

        param7 = arcpy.Parameter(name = "out_cg_polygon_feature_class",
                                 displayName = "Output Computational Grid Polygon Feature Class",
                                 direction = "Output",
                                 parameterType = "Optional",
                                 datatype = "DEFeatureClass")

        param8 = arcpy.Parameter(name = "out_cg_point_feature_class",
                                 displayName = "Output Computational Grid Point Feature Class",
                                 direction = "Output",
                                 parameterType = "Optional",
                                 datatype = "DEFeatureClass")


        params = [param0, param1, param2, param3, param4, 
                  param5, param6, param7, param8]

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

        if parameters[0].altered and parameters[0].valueAsText is not None:
            #get list of variables in the netcdf file
            data_nc = NET.Dataset(parameters[0].valueAsText)
            variables_list = data_nc.variables.keys()
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

    def find_nearest(self, array, value):
        return (NUM.abs(array-value)).argmin()

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
        out_CGPolygon = parameters[7].valueAsText
        out_CGPoint = parameters[8].valueAsText

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
            #sr_out = arcpy.SpatialReference(54002)  # 'Cylindrical Equidistant Projection Grid'
            envelope_proj = os.path.join(scratchWorkspace,'envelope_proj')
            result1 = arcpy.Project_management(envelope, envelope_proj, sr_out)
            envelope_proj = result1.getOutput(0)
            extent = arcpy.Describe(envelope_proj).extent


        #Open nc file
        """ 
        GLDAS NC FILE
        dimensions:
            g0_lat_0 = 600 ;
            g0_lon_1 = 1440 ;
            lv_DBLY2 = 4 ;
        variables:
        ...
            float g0_lat_0(g0_lat_0) ;
                g0_lat_0:La1 = -59.875f ;
                g0_lat_0:Lo1 = -179.875f ;
                g0_lat_0:La2 = 89.875f ;
                g0_lat_0:Lo2 = 179.875f ;
                g0_lat_0:Di = 0.25f ;
                g0_lat_0:Dj = 0.25f ;
                g0_lat_0:units = "degrees_north" ;
                g0_lat_0:GridType = "Cylindrical Equidistant Projection Grid" ;
                g0_lat_0:long_name = "latitude" ;
            float g0_lon_1(g0_lon_1) ;
                g0_lon_1:La1 = -59.875f ;
                g0_lon_1:Lo1 = -179.875f ;
                g0_lon_1:La2 = 89.875f ;
                g0_lon_1:Lo2 = 179.875f ;
                g0_lon_1:Di = 0.25f ;
                g0_lon_1:Dj = 0.25f ;
                g0_lon_1:units = "degrees_east" ;
                g0_lon_1:GridType = "Cylindrical Equidistant Projection Grid" ;
                g0_lon_1:long_name = "longitude" ;
        
        NLDAS MOSAIC FILE
        dimensions:
            g0_lat_0 = 224 ;
            g0_lon_1 = 464 ;
            ...

        variables:
            ...
            float g0_lat_0(g0_lat_0) ;
                g0_lat_0:La1 = 25.063f ;
                g0_lat_0:Lo1 = -124.938f ;
                g0_lat_0:La2 = 52.938f ;
                g0_lat_0:Lo2 = -67.063f ;
                g0_lat_0:Di = 0.125f ;
                g0_lat_0:Dj = 0.125f ;
                g0_lat_0:units = "degrees_north" ;
                g0_lat_0:GridType = "Cylindrical Equidistant Projection Grid" ;
                g0_lat_0:long_name = "latitude" ;

            float g0_lon_1(g0_lon_1) ;
                g0_lon_1:La1 = 25.063f ;
                g0_lon_1:Lo1 = -124.938f ;
                g0_lon_1:La2 = 52.938f ;
                g0_lon_1:Lo2 = -67.063f ;
                g0_lon_1:Di = 0.125f ;
                g0_lon_1:Dj = 0.125f ;
                g0_lon_1:units = "degrees_east" ;
                g0_lon_1:GridType = "Cylindrical Equidistant Projection Grid" ;
                g0_lon_1:long_name = "longitude" ;

        NLDAS NOAH/VIC FILE
        dimensions:
            lat_110 = 224 ;
            lon_110 = 464 ;
            ...
        variables:
            ...
            float lat_110(lat_110) ;
                lat_110:La1 = 25.063f ;
                lat_110:Lo1 = -124.938f ;
                lat_110:La2 = 52.938f ;
                lat_110:Lo2 = -67.063f ;
                lat_110:Di = 0.125f ;
                lat_110:Dj = 0.125f ;
                lat_110:units = "degrees_north" ;
                lat_110:GridType = "Cylindrical Equidistant Projection Grid" ;
                lat_110:long_name = "latitude" ;

            float lon_110(lon_110) ;
                lon_110:La1 = 25.063f ;
                lon_110:Lo1 = -124.938f ;
                lon_110:La2 = 52.938f ;
                lon_110:Lo2 = -67.063f ;
                lon_110:Di = 0.125f ;
                lon_110:Dj = 0.125f ;
                lon_110:units = "degrees_east" ;
                lon_110:GridType = "Cylindrical Equidistant Projection Grid" ;
                lon_110:long_name = "longitude" ;
        """

        data_nc = NET.Dataset(in_nc)

        # Obtain geographic coordinates
        lon = data_nc.variables[in_nc_lon_var][:] #assume [-180,180]
        lat = data_nc.variables[in_nc_lat_var][:] #assume [-90,90]
        lon = NUM.float32(lon)
        lat = NUM.float32(lat)
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
        #get list of COMIDs in rapid_connect file so only those are included in computations
        connectivity_table = self.csvToList(in_rapid_connect_file)
        streamID_unique_arr = [int(row[0]) for row in connectivity_table]

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

        with open(out_WeightTable, 'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect = 'excel')
            connectwriter.writerow([streamID, 'area_sqm', 'lon_index', 'lat_index', 'npoints'])
            for streamID_unique in streamID_unique_arr:
                ind_points = NUM.where(area_arr[streamID]==streamID_unique)[0]
                num_ind_points = len(ind_points)

                if num_ind_points <= 0:
                    #FEATUREID,area_sqm,lon_index,lat_index,npoints
                    connectwriter.writerow([streamID_unique, 0, index_lon_dummy, index_lat_dummy, 1])
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
                        row = [streamID_unique, area_geo_each, index_lon_each, index_lat_each, num_ind_points]
                        connectwriter.writerow(row)

        return
