'''-------------------------------------------------------------------------------
 Tool Name:   CreateWeightTableFromWRFGeogrid
 Source Name: CreateWeightTableFromWRFGeogrid.py
 Version:     ArcGIS 10.2
 License:     Apache 2.0
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Creates the computation grid polygon feature class within the buffered
              extent of the input catchment based on the WRF_Hydro GeoGrid netcdf data
 History:     Initial coding - 10/10/2014, version 1.0
 Updated:     Version 1.0, 10/23/2014, modified names of tool and parameters
              Version 1.0, 10/28/2014, added data validation
              Version 1.1, 02/03/2015, bug fixing -- CGPoint output file can be named
                by users instead of arbitrarily depending on CGPolygon output file name;
              Version 1.1, 02/03/2015, adapted Kevin Sampson's script lines for all
                four types of map projections (MAP_PROJ = 1, 2, 3, 6);
              Version 1.1, 04/20/2015, modified the equation for calculating central
                scale factor for MAP_PROJ = 2 according to Kevin Sampson
              Version 2.0, 06/04/2015, integrated Update Weight Table (according to Alan Snow)
              Version 2.1, 02/26/2016, fixed the bug of writing total area instead of individual
                area in the weight table, pulled the table writing out of the for loop for
                calculation, these changes were adapted from Alan D Snow, US Army ERDC
-------------------------------------------------------------------------------'''
import os, math
import arcpy
import netCDF4 as NET
import numpy as NUM
import csv


class CreateWeightTableFromWRFGeogrid(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Weight Table From WRF Geogrid"
        self.description = ("Creates weight table based on the WRF Geogrid file" +
                            " and catchment features")
        self.canRunInBackground = False
        self.dimensions = ["west_east", "south_north"]
        self.globalattributes = ["MAP_PROJ", "corner_lats", "corner_lons", "DX", "DY",
                                 "TRUELAT1", "TRUELAT2", "STAND_LON", "POLE_LAT",
                                 "POLE_LON", "CEN_LAT"]
        self.errorMessages = [  "Map Projection is incorrect in the input WRF geogrid file.",
                                "Missing dimension: {0} in the input WRF geogrid file.",
                                "Missing global attribute: {0} in the input WRF geogrid file."
                                "The input catchment features exceed the WRF Geogrid data extent."]
        self.category = "Preprocessing"

    def dataValidation(self, in_nc, messages):
        """Check the necessary dimensions and variables in the input netcdf data"""
        data_nc = NET.Dataset(in_nc)
        dims = data_nc.dimensions.keys()
        globalattrs = data_nc.__dict__.keys()
        for each in self.dimensions:
            if each not in dims:
                messages.addErrorMessage(self.errorMessages[1].format(each))
                raise arcpy.ExecuteError
        for each in self.globalattributes:
            if each not in globalattrs:
                messages.addErrorMessage(self.errorMessages[2].format(each))
                raise arcpy.ExecuteError

        data_nc.close()

        return

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
        param0 = arcpy.Parameter(name = "in_WRF_geogrid_file",
                                 displayName = "Input WRF Geogrid File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

        param1 = arcpy.Parameter(name = "in_lat_variable",
                                 displayName = "Latitude Variable",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")
        param1.filter.list = []
        param1.value = "XLAT_M"
        
        param2 = arcpy.Parameter(name = "in_lon_variable",
                                 displayName = "Longitude Variable",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")
        param2.filter.list = []
        param2.value = "XLONG_M"
        
        param3 = arcpy.Parameter(name = "in_network_connectivity_file",
                                 displayName = "Input Network Connecitivity File",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEFile")

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

        param6 = arcpy.Parameter(name = "out_weight_table",
                                 displayName = "Output Weight Table",
                                 direction = "Output",
                                 parameterType = "Required",
                                 datatype = "DEFile")

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

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].valueAsText is not None and parameters[4].valueAsText is not None \
            and parameters[5].valueAsText is not None and parameters[6].valueAsText is None:
                scratchWorkspace = arcpy.env.scratchWorkspace
                if not scratchWorkspace:
                    scratchWorkspace = arcpy.env.scratchGDB
                parameters[6].value = os.path.join(scratchWorkspace, "Weight_Table.csv")

        if parameters[6].valueAsText is not None:
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

    def execute(self, parameters, messages):
        """The source code of the tool."""

        arcpy.env.overwriteOutput = True

        scratchWorkspace = arcpy.env.scratchWorkspace
        if not scratchWorkspace:
            scratchWorkspace = arcpy.env.scratchGDB

        in_nc = parameters[0].valueAsText
        lat_var_name = parameters[1].valueAsText
        lon_var_name = parameters[2].valueAsText
        in_rapid_connect_file = parameters[3].valueAsText
        in_catchment = parameters[4].valueAsText
        streamID = parameters[5].valueAsText
        out_WeightTable = parameters[6].valueAsText
        out_CGPolygon = parameters[7].valueAsText
        out_CGPoint = parameters[8].valueAsText

        # validate the netcdf dataset
        self.dataValidation(in_nc, messages)

        # open netcdf dataset
        data_nc = NET.Dataset(in_nc)


        '''Obtain west-east, south-north dimension information'''
        name_xdim = 'west_east'
        name_ydim = 'south_north'
        size_xdim = len(data_nc.dimensions['west_east'])
        size_ydim = len(data_nc.dimensions['south_north'])



        #####################Start of script adaption###############################################################
        '''Obtain projection information'''
        map_proj = data_nc.__dict__['MAP_PROJ']

        # read projection information from global attributes
        corner_lats = data_nc.__dict__['corner_lats']
        corner_lons = data_nc.__dict__['corner_lons']
        DX = data_nc.__dict__['DX']
        DY = data_nc.__dict__['DY']
        standard_parallel_1 = data_nc.__dict__['TRUELAT1']
        standard_parallel_2 = data_nc.__dict__['TRUELAT2']
        central_meridian = data_nc.__dict__['STAND_LON']
        pole_latitude = data_nc.__dict__['POLE_LAT']
        pole_longitude = data_nc.__dict__['POLE_LON']
        latitude_of_origin = data_nc.__dict__['CEN_LAT']

        # Create Projection file with information from NetCDF global attributes
        sr2 = arcpy.SpatialReference()
        if map_proj == 1:
            # Lambert Conformal Conic
            if 'standard_parallel_2' in locals():
                arcpy.AddMessage('    Using Standard Parallel 2 in Lambert Conformal Conic map projection.')
            else:
                # According to http://webhelp.esri.com/arcgisdesktop/9.2/index.cfm?TopicName=Lambert_Conformal_Conic
                standard_parallel_2 = standard_parallel_1
                latitude_of_origin = standard_parallel_1
            Projection_String = ('PROJCS["North_America_Lambert_Conformal_Conic",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Lambert_Conformal_Conic"],'
                                 'PARAMETER["false_easting",0.0],'
                                 'PARAMETER["false_northing",0.0],'
                                 'PARAMETER["central_meridian",' + str(central_meridian) + '],'
                                 'PARAMETER["standard_parallel_1",' + str(standard_parallel_1) + '],'
                                 'PARAMETER["standard_parallel_2",' + str(standard_parallel_2) + '],'
                                 'PARAMETER["latitude_of_origin",' + str(latitude_of_origin) + '],'
                                 'UNIT["Meter",1.0]]')

        elif map_proj == 2:
            # Polar Stereographic

            # Set up pole latitude
            phi1 = float(standard_parallel_1)

            ### Back out the central_scale_factor (minimum scale factor?) using formula below using Snyder 1987 p.157 (USGS Paper 1395)
            ##phi = math.copysign(float(pole_latitude), float(latitude_of_origin))    # Get the sign right for the pole using sign of CEN_LAT (latitude_of_origin)
            ##central_scale_factor = (1 + (math.sin(math.radians(phi1))*math.sin(math.radians(phi))) + (math.cos(math.radians(float(phi1)))*math.cos(math.radians(phi))))/2

            # Method where central scale factor is k0, Derivation from C. Rollins 2011, equation 1: http://earth-info.nga.mil/GandG/coordsys/polar_stereographic/Polar_Stereo_phi1_from_k0_memo.pdf
            # Using Rollins 2011 to perform central scale factor calculations. For a sphere, the equation collapses to be much  more compact (e=0, k90=1)
            central_scale_factor = (1 + math.sin(math.radians(abs(phi1))))/2                            # Equation for k0, assumes k90 = 1, e=0. This is a sphere, so no flattening

            loglines.append('      Central Scale Factor: %s' %central_scale_factor)
            arcpy.AddMessage(loglines[-1])
            Projection_String = ('PROJCS["Sphere_Stereographic",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",'
                                 'SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Stereographic"],'
                                 'PARAMETER["False_Easting",0.0],'
                                 'PARAMETER["False_Northing",0.0],'
                                 'PARAMETER["Central_Meridian",' + str(central_meridian) + '],'
                                 'PARAMETER["Scale_Factor",' + str(central_scale_factor) + '],'
                                 'PARAMETER["Latitude_Of_Origin",' + str(standard_parallel_1) + '],'
                                 'UNIT["Meter",1.0]]')

        elif map_proj == 3:
            # Mercator Projection
            Projection_String = ('PROJCS["Sphere_Mercator",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",'
                                 'SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Mercator"],'
                                 'PARAMETER["False_Easting",0.0],'
                                 'PARAMETER["False_Northing",0.0],'
                                 'PARAMETER["Central_Meridian",' + str(central_meridian) + '],'
                                 'PARAMETER["Standard_Parallel_1",' + str(standard_parallel_1) + '],'
                                 'UNIT["Meter",1.0],AUTHORITY["ESRI",53004]]')

        elif map_proj == 6:
            # Cylindrical Equidistant (or Rotated Pole)
            # Check units (linear unit not used in this projection).  GCS?
            Projection_String = ('PROJCS["Sphere_Equidistant_Cylindrical",'
                                 'GEOGCS["GCS_Sphere",'
                                 'DATUM["D_Sphere",'
                                 'SPHEROID["Sphere",6370000.0,0.0]],'
                                 'PRIMEM["Greenwich",0.0],'
                                 'UNIT["Degree",0.0174532925199433]],'
                                 'PROJECTION["Equidistant_Cylindrical"],'
                                 'PARAMETER["False_Easting",0.0],'
                                 'PARAMETER["False_Northing",0.0],'
                                 'PARAMETER["Central_Meridian",' + str(central_meridian) + '],'
                                 'PARAMETER["Standard_Parallel_1",' + str(standard_parallel_1) + '],'
                                 'UNIT["Meter",1.0],AUTHORITY["ESRI",53002]]')

        sr2.loadFromString(Projection_String)


        '''Create a projected ones raster'''
        arr_ones = NUM.ones((size_ydim, size_xdim), dtype = NUM.uint16)

        #####################Start of script adaption###############################################################
        # Create a point geometry object from gathered corner point data
        sr1 = arcpy.SpatialReference(104128)            # Using EMEP Sphere (6370000m)
        point = arcpy.Point()
        point.X = float(corner_lons[0])
        point.Y = float(corner_lats[0])
        pointGeometry = arcpy.PointGeometry(point, sr1)
        projpoint = pointGeometry.projectAs(sr2)

        # Get projected X and Y of the point geometry and adjust so lower left corner becomes lower left center
        point2 = arcpy.Point((projpoint.firstPoint.X - (float(DX)/2)), (projpoint.firstPoint.Y - (float(DY)/2))) # Adjust by half a grid cell

        # Process: Numpy Array to Raster
        ras_ones = arcpy.NumPyArrayToRaster(arr_ones, point2, float(DX), float(DY))

        # Process: Define Projection
        arcpy.DefineProjection_management(ras_ones, sr2)

        ras_ones.save(os.path.join(scratchWorkspace, "ras_ones"))
        ################End of script adaption######################################################################


        '''Create CG Polygon for the buffered catchment'''
        arcpy.AddMessage("Creating computation grid polygons...")
        # Obtain a minimum bounding envelope of the catchment with the same spatial reference as the WRF-Hydro data
        envelope = os.path.join(scratchWorkspace,"envelope")
        arcpy.env.outputCoordinateSystem = sr2
        result0 = arcpy.MinimumBoundingGeometry_management(in_catchment, envelope, "ENVELOPE", "ALL")
        arcpy.ResetEnvironments()
        envelope = result0.getOutput(0)
        # Determine whether the input catchment is within the WRF-Hydro data extent
        ext_ras_ones = arcpy.Describe(ras_ones).extent
        ext_envelope = arcpy.Describe(envelope).extent
        if ext_envelope.XMin < ext_ras_ones.XMin \
            or ext_envelope.XMax > ext_ras_ones.XMax \
            or ext_envelope.YMin < ext_ras_ones.YMin \
            or ext_envelope.YMax > ext_ras_ones.YMax:
                # Input Catchments exceed the WRF data extent
                messages.addErrorMessage(self.errorMessages[2])
                raise arcpy.ExecuteError


        # Buffer the minimum bounding envelope
        envelope_b = os.path.join(scratchWorkspace, "envelope_b")
        dist_buffer = str(int(DX)*3) + " Meters"
        result1 = arcpy.Buffer_analysis(envelope, envelope_b, dist_buffer, "FULL", "#", "ALL")
        envelope_b = result1.getOutput(0)

		
        # Convert the buffered envelope into raster with cellsize, and snapraster the same as ras_ones
        arcpy.env.snapRaster = ras_ones
        arcpy.env.cellSize = ras_ones
        name_OID = arcpy.Describe(envelope_b).OIDFieldName
        ras_env_b = os.path.join(scratchWorkspace, "ras_env_b")
        arcpy.PolygonToRaster_conversion(envelope_b, name_OID, ras_env_b, 'CELL_CENTER', 'NONE', ras_ones)
        arcpy.ResetEnvironments()


        # Create fishnet based on the clipped raster
        # Get the extent of the raster
        ext_ras = arcpy.Describe(ras_env_b).extent
        xmin_ras = ext_ras.XMin
        ymin_ras = ext_ras.YMin

        # Set parameters of the output fishnet
        originCoordinate = str(xmin_ras) + ' ' + str(ymin_ras)  # the origin
        yAxiCoordinate = str(xmin_ras) + ' ' + str(ymin_ras + 10)  # the orientation
        cellSizeWidth = str(DX)
        cellSizeHeight = str(DY)
        ras_temp = arcpy.sa.Raster(ras_env_b)
        numRows = str(ras_temp.height)
        numCols = str(ras_temp.width)
        labels = "NO_LABELS"
        if out_CGPoint is not None:
            labels = "LABELS"
        oppositeCorner = ""
        templateExtent = ras_env_b
        geometryType = "POLYGON"

        if out_CGPolygon is None:
            out_CGPolygon = os.path.join(scratchWorkspace, "out_CGPolygon")

        # Create fishnet (computation grid polygon) (and point if specified)
        result2 = arcpy.CreateFishnet_management(out_CGPolygon, originCoordinate, yAxiCoordinate,
                                        cellSizeWidth, cellSizeHeight, numRows, numCols,
                                        oppositeCorner, labels, templateExtent, geometryType)
        out_CGPolygon = result2.getOutput(0)

        # Add and calculate fields of CENTROID_X and CENTROD_Y for fishnet (computation grid polygon)
        arcpy.AddGeometryAttributes_management(out_CGPolygon, "CENTROID", "#", "#", "#")
        temp_CGPoint = None
        (dirnm_out_CGPolygon, basenm_out_CGPolygon) = os.path.split(out_CGPolygon)
        if not basenm_out_CGPolygon.endswith(".shp"):
            temp_CGPoint = out_CGPolygon+"_label"
        else:
            temp_CGPoint = os.path.join(dirnm_out_CGPolygon, "{}_label.shp".format(basenm_out_CGPolygon[:-4]))

        if arcpy.Exists(temp_CGPoint) and out_CGPoint is not None and (temp_CGPoint) != out_CGPoint:
            if not arcpy.Exists(out_CGPoint):
                arcpy.CopyFeatures_management(temp_CGPoint, out_CGPoint)
                arcpy.Delete_management(temp_CGPoint)

        # Get latitude and longitude
        lat_arr = data_nc.variables[lat_var_name][:]
        lon_arr = data_nc.variables[lon_var_name][:]
        data_nc.close()

        '''Create weight table'''
        # Obtain the minimum X and minimum Y for the lower left pixel center of the ones raster
        minX = projpoint.firstPoint.X
        minY = projpoint.firstPoint.Y


        # Intersect the catchment polygons with the computation grid polygons
        arcpy.AddMessage("Intersecting computation grid polygons with catchment...")
        intersected = os.path.join(scratchWorkspace, "intersected")
        result3 = arcpy.Intersect_analysis([out_CGPolygon, in_catchment], intersected, "ALL", "#", "INPUT")
        intersected = result3.getOutput(0)

        # Calculate the geodesic area in square meters for each intersected polygon
        arcpy.AddMessage("Calculating geodesic areas...")
        arcpy.AddGeometryAttributes_management(intersected, "AREA_GEODESIC", "", "SQUARE_METERS", "")


        # Calculate the total geodesic area of each catchment based on the contributing areas of points
        fields = [streamID, "CENTROID_X", "CENTROID_Y", "AREA_GEO"]
        area_arr = arcpy.da.FeatureClassToNumPyArray(intersected, fields)

        arcpy.AddMessage("Writing the weight table...")
        # Get list of COMIDs in rapid connect file so only those area included in computations
        connectivity_table = self.csvToList(in_rapid_connect_file)
        streamID_unique_list = [int(row[0]) for row in connectivity_table]

        # Get some dummy data from the first row
        centroidX_dummy = area_arr["CENTROID_X"][0]
        centroidY_dummy = area_arr["CENTROID_Y"][0]
        indexX_dummy = long(round((centroidX_dummy - minX)/float(DX)))
        indexY_dummy = long(round((centroidY_dummy - minY)/float(DY)))
        lon_dummy = lon_arr[0, indexY_dummy, indexX_dummy]
        lat_dummy = lat_arr[0, indexY_dummy, indexX_dummy]

        with open(out_WeightTable, 'wb') as csvfile:
            connectwriter = csv.writer(csvfile, dialect = 'excel')
            #header
            connectwriter.writerow([streamID, "area_sqm", "west_east", "south_north", "npoints", "Lon", "Lat", "x", "y"])

            for streamID_unique in streamID_unique_list:
                ind_points = NUM.where(area_arr[streamID]==streamID_unique)[0]
                num_ind_points = len(ind_points)

                if num_ind_points <= 0:
                    # if point not in array, append dummy data for one point of data
                    # streamID, "area_sqm", "west_east", "south_north", "npoints", "Lon", "Lat", "x", "y"
                    row_dummy = [streamID_unique, 0, indexX_dummy, indexY_dummy, 1, lon_dummy, lat_dummy, centroidX_dummy, centroidY_dummy]
                    connectwriter.writerow(row_dummy)
                else:
                    for ind_point in ind_points:
                        area_geo_each = float(area_arr['AREA_GEO'][ind_point])
                        centroidX = area_arr["CENTROID_X"][ind_point]
                        centroidY = area_arr["CENTROID_Y"][ind_point]
                        indexX = long(round((centroidX - minX)/float(DX)))
                        indexY = long(round((centroidY - minY)/float(DY)))
                        lon = lon_arr[0, indexY, indexX]
                        lat = lat_arr[0, indexY, indexX]
                        row = [streamID_unique, area_geo_each, indexX, indexY, num_ind_points, lon, lat, centroidX, centroidY]
                        connectwriter.writerow(row)


        return