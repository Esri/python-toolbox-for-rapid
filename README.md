# RAPID Tools

This repository houses a python toolbox of tools for preprocessing inputs and postprocessing outputs of the RAPID (Routing Application for Parallel computation of Discharge) model. To know more information about RAPID, please visit its [website] (http://rapid-hub.org/).

## Getting Started

1. Install [ArcGIS for Desktop 10.4](http://desktop.arcgis.com/en/arcmap/) 
2. If your ArcGIS for Desktop is previous to 10.2, you must install [netCDF4 python package] (https://pypi.python.org/pypi/netCDF4). An executable file for installing netCDF4-1.0.8 with python 2.7 is available [here] (http://downloads.esri.com/archydro/archydro/Setup/10.2.x/rapid/).
3. Download the toolbox and place it in a folder. Access the folder from Catalog in ArcMap. You will see the following:
![alt tag](/toolbox_screenshot.png)

## Issues

Find a bug or want to request a new feature?  Please let us know by [submitting an issue](https://github.com/ArcGIS/RAPID_Tools/issues).

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Tools

### Preprocessing tools

* #### Create Connectivity File
  This tool creates the stream network connectivity file based on two fields in the input drainage line feature class: HydroID, and     NextDownID. It does the following:

  1. find the HydroID of each stream
  2. count the total number of its upstreams
  3. write the stream HydroID, the total number of its upstreams, and the HydroID(s) of all upstream(s) into the output file. The    sequence of the records follows the ascending order of the stream HydroID.

* #### Create Subset File

  This tool writes the HydroID of a subset of the stream features. The subset is created by selecting the stream features in the input   layer.

* #### Create Muskingum Parameters File

  This tool writes the values of the Muskingum parameter fields (Musk_kfac, Musk_k, and Musk_x) into individual parameter files. The    three fields can be calculated using the Calculate Muskingum Parameters tool in the RAPID_parameters.tbx. The order of the records    in all files follows the ascending order of the stream HydroID.

* #### Create Weight Table From ECMWF/WRF-Hydro Runoff

  This tool creates a table that represents the runoff contribution of the ECMWF computational grid to the catchment. It does the     following:

  For ECMWF,

  1. create computational grid point feature class based on the latitude and longitude in the ECMWF runoff file
  2. create Thiessen polygons from the computational grid points. The Thiessen polygons represent computational grids

  For WRF-Hydro,

  1. creates a raster based on the spatial resolution, extent, and projection information in the WRF geogrid file
  2. creates fishnet polygons and points based on the raster. The polygons and points represent the computational grids and points

  Then for both,

  3. intersect the computational polygons with the input catchments
  4. calculate the geodesic area for each intersected polygon
  5. calculate the area ratio of each intersected polygon to its corresponding catchment, which is defined as the weight representing   the contribution of the computational grid to the catchment (drainage line segment)
  6. write the stream ID, the coordinates of the contributing computational grid, the contributing area, and the weight, etc., into   the weight table

  The order of the records in the weight table follows the ascending order of the stream ID.

* #### Update Weight Table

  This tool updates the weight table specifically for the scenario in which the drainage line and the catchment features are not    one-to-one relationship. It does the following to the weight table:
  
  1. remove the rows with stream IDs that don’t have a match in drainage lines
  2. add rows with stream IDs that are in drainage lines but not in catchments. In these newly added rows, the contributing area and  the weight are given values of 0. And the npoints that representing the total number of computational grids contributing to the same catchment is given the value of 1. 

* #### Create Inflow File From ECMWF/WRF-Hydro Runoff

  This tool creates the RAPID inflow file from ECMWF / WRF-Hydro runoff data. It does the following:
  
  1. obtain a list of stream IDs based on the input drainage line feature class
  2. for each stream feature, obtain the information of all contributing computational grids from the weight table
  3. calculate the runoff to each stream feature based on the computational-grid-specific runoff rates from the ECMWF / WRF-Hydro runoff data file and the contributing areas from the weight table
  4. if the stream ID does not have any corresponding record in the weight table, its runoff is specified as 0
  5. write the runoff data into the inflow file in netCDF format

### Postprocessing tools

* #### Create Discharge Table

  This tool creates a discharge table converted from the RAPID discharge file. In the discharge table, each row contains the   information of COMID, time, and the discharge of the stream at the time step. Time is calculated as date/time format based on the start date and time input by the user and the time dimension of the stream flow variable in the RAPID discharge file. Attribute indexes are added respectively for COMID, and the time fields in the table. The discharge table is saved in a SQL Server geodatabase or a file geodatabase.

* #### Create Discharge Map

  This tool creates a discharge map document with time-enabled stream flow layer(s). Stream flow can be animated in the discharge map. The tool does the following:

  1. if the layer information is not specified, all stream features that have records in the discharge table will be copied into the  same geodatabase where the discharge table is; if the layer information is specified, based on the information of minimum stream order for each layer, stream features are selected using the query definition of stream order >= the minimum, and then the selected stream features are copied into the same geodatabase where the discharge table is
  2. create a map document and add all the copied stream feature classes into the map
  3. for each layer, add join with the discharge table based on COMID as the join field
  4. for each layer, define the minScale and maxScale based on the user-specified information
  5. apply symbology on each layer based on the same template layer file (layers of the data in SQL Server geodatabase and file geodatabase have different templates)
  6. update the time properties for each layer based on the time-enabled template.
 
* #### Update Discharge Map

  This tool updates the existing map document by applying symbology from a template layer file on the layer(s) in the map document. The tool is run only if the discharge table has been updated.

### Utilities Tools

* #### Flowline to Point

  This tool writes the centroid coordinates of flowlines into a CSV file.

* #### Copy Data To Server

  This tool copies the discharge table and/or the drainage line features to the ArcGIS server machine from the author/publisher machine.

* #### Publish Discharge Map

  This tool publishes a discharge map service of stream flow visualization to an ArcGIS server.

## Licensing
Copyright 2014 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [License.txt](/LICENSE) file.
