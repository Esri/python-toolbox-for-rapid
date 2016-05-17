# RAPID Tools

This repository houses a Python toolbox of tools for preprocessing inputs and postprocessing outputs of the RAPID (Routing Application for Parallel computation of Discharge) model. To find out more about RAPID, please visit http://rapid-hub.org/.

## Getting Started

* Ensure you have [ArcGIS for Desktop](http://desktop.arcgis.com/en/arcmap/) installed. 
* If your version of ArcGIS for Desktop is previous to 10.2, you must install the [netCDF4 Python package] (https://pypi.python.org/pypi/netCDF4). An executable for installing netCDF4-1.0.8 with Python 2.7 is available [here] (http://downloads.esri.com/archydro/archydro/Setup/10.2.x/rapid/).
* Download the toolbox and place it in an appropriate folder on your machine. Navigate to the folder in Catalog. If you expand all the toolsets, you will see the following: 

![alt tag](/toolbox_screenshot.png)

* In order to use the Preprocessing tools, you will need to have the following inputs available:

   * Drainage Line and Catchment feature classes for the watersheds of interests. To learn about how to create them, please refer to the workflow of Basic Dendritic Terrain Processing with [ArcHydro](http://resources.arcgis.com/en/communities/hydro/01vn0000000s000000.htm) tools.
   * For [WRF-Hydro](https://www.ral.ucar.edu/projects/wrf_hydro), you will need both its geogrid file and runoff file; for [ECMWF](http://www.ecmwf.int/), you will need only the runoff file.

## Issues

Find a bug or want to request a new feature?  Please let us know by [submitting an issue](https://github.com/ArcGIS/RAPID_Tools/issues).

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Tools

The tools are organized into four toolsets. One for preprocessing and preparing the input datasets for RAPID. The second is for generating calibrated values for the Muksingum Paremeters. The third is for doing some postprocessing especially for visualizing the RAPID output of stream flow. The fourth toolset has some utilities to assist you with the workflow and sharing the visualization as web map service.

### Preprocessing tools

* #### Create Connectivity File

  This tool creates the stream network connectivity file based on two fields in the input Drainage Line feature class: HydroID, and     NextDownID. It does the following:

  1. Finds the HydroID of each stream.
  2. Counts the total number of its upstreams.
  3. Writes the stream HydroID, the total number of its upstreams, and the HydroID(s) of all upstream(s) into the output file. The    records are sorted in the ascending order based on the stream HydroID.

* #### Create Subset File

  This tool writes the HydroID of a subset of the stream features. The subset is created by selecting stream features in the input   layer.

* #### Create Muskingum Parameters File

  This tool writes the values of the Muskingum parameter fields (Musk_kfac, Musk_k, and Musk_x) into individual parameter files. The    three fields can be calculated using the Calculate Muskingum Parameters tool in the [ArcHydro toolbox](http://resources.arcgis.com/en/communities/hydro/01vn0000000s000000.htm). The records in all files are sorted in the ascending order based on the stream HydroID.

* #### Create Weight Table From ECMWF/WRF-Hydro Runoff

  This tool creates a table that represents the runoff contribution of the ECMWF/WRF-Hydro computational grid to the catchment. It requires that the input Catchment feature class has a drainage line ID field that corresponds to the HydroID of the Drainage Line feature class. If your input Catchment feature class does not have that field, you can use the Add DrainLnID to Catchment tool in the [ArcHydro toolbox](http://resources.arcgis.com/en/communities/hydro/01vn0000000s000000.htm). This tool does the following:

  For ECMWF,

  1. Creates computational grid point feature class based on the latitude and longitude in the ECMWF runoff file.
  2. Creates Thiessen polygons from the computational grid points. The Thiessen polygons represent computational grids.

  For WRF-Hydro,

  1. Creates a raster based on the spatial resolution, extent, and projection information in the WRF geogrid file.
  2. Creates fishnet polygons and points based on the raster. The polygons and points represent the computational grids and points.

  Then for both,

  3. Intersects the computational polygons with the input catchments.
  4. Calculates the geodesic area for each intersected polygon.
  5. Calculates the area ratio of each intersected polygon to its corresponding catchment, which is defined as the weight representing   the contribution of the computational grid to the catchment (drainage line segment).
  6. Writes the stream ID, the coordinates of the contributing computational grid, the contributing area, and the weight, etcetera, into the weight table.

 The records in the weight table are sorted in the ascending order based on the stream ID.

* #### Update Weight Table

  This tool updates the weight table specifically for the scenario in which the Drainage Line and the Catchment features are not    one-to-one relationship. It does the following to the weight table:
  
  1. Removes the rows with stream IDs that don’t have a match in the Drainage Line feature class.
  2. Adds rows with stream IDs that are in the Drainage Line but not in the Catchment feature class. In these newly added rows, the contributing area and  the weight are given values of 0. And the "npoints" (number of points) column that represents the total number of computational grids contributing to the same catchment is given the value of 1. 

* #### Create Inflow File From ECMWF/WRF-Hydro Runoff

  This tool creates the RAPID inflow file from ECMWF / WRF-Hydro runoff data. It does the following:
  
  1. Obtains a list of stream IDs based on the input drainage line feature class.
  2. For each stream feature, obtains the information of all contributing computational grids from the weight table.
  3. Calculates the runoff to each stream feature based on the computational-grid-specific runoff rates from the ECMWF / WRF-Hydro runoff data file and the contributing areas from the weight table.
  4. If a stream ID does not have a corresponding record in the weight table, specifies its runoff as 0.
  5. Writes the runoff data into the inflow file in netCDF format.

### Calibration tools

* #### Create Muksingum Kfac File

  This tool is used to generate values of Kfac based on the flow wave celerity (Co) for the basin as well as length and slope of each stream reach.
  
  There are three options:

  1. River Length/Co
  2. Eta*River Length/Sqrt(River Slope)
  3. Eta*River Length/Sqrt(River Slope) [0.05, 0.95] - this option filters out slopes outside the 5th and 95th percentiles.

  Note: Eta = Average(River Length/Co of all rivers) / Average(River Length/Sqrt(River Slope) of all rivers)

* #### Create Muksingum K File

  Using lambda, this tool modifies each of the Kfac values by multiplying by lambda and generates the calibrated Muskgingum K file (e.g. k.csv). 
  The value for lambda is obtained by running the calibration routine in RAPID for your simulation. 

### Postprocessing tools

* #### Create Discharge Table

  This tool creates a discharge table converted from the RAPID discharge file. In the discharge table, each row contains the   information of COMID (an ID field of the [NHDPlus](http://www.horizon-systems.com/nhdplus/NHDPlusV2_home.php) dataset), time, and the discharge of the stream at the time step. Time in date/time format is calculated based on the start date and time input by the user and the time dimension of the stream flow variable in the RAPID discharge file. Attribute indexes are added respectively for COMID, and the time fields in the table. The discharge table is saved in a SQL Server geodatabase or a file geodatabase.

* #### Create Discharge Map

  This tool creates a map document with time-enabled stream flow layer(s) showing stream- and time-specific discharge amounts. Stream flow can be animated in the discharge map. The tool does the following:

  1. If the layer information is not specified, all stream features that have records in the discharge table will be copied into the  same geodatabase where the discharge table is. If the layer information is specified, based on the information of minimum stream order for each layer, stream features are selected using the query definition of stream order >= the minimum, then the selected stream features are copied into the same geodatabase where the discharge table is.
  2. Creates a map document and add all the copied stream feature classes into the map.
  3. For each layer, adds a join to the discharge table based on COMID as the join field.
  4. For each layer, defines the minScale and maxScale based on the user-specified information.
  5. Applies symbology to each layer based on the same template layer file. Note that the layers of data in SQL Server geodatabase and file geodatabase have different templates.
  6. Updates the time properties for each layer based on the time-enabled template.
 
* #### Update Discharge Map

  This tool updates the existing map document by applying symbology from a template layer file to the layer(s) in the map document. The tool is run only if the discharge table has been updated.

### Utilities Tools

* #### Flowline to Point

  This tool writes the centroid coordinates of flowlines into a CSV file.

* #### Copy Data To Server

  This tool copies the discharge table, the drainage line features, or both to the ArcGIS server machine from the author/publisher machine.

* #### Publish Discharge Map

  This tool publishes a discharge map service of stream flow visualization to an ArcGIS server.

## Licensing
Copyright 2016 Esri

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

[](Esri Tags: ArcGIS Python Toolbox of Preprocessing and Postprocessing for a River Routing Model RAPID)
[](Esri Language: Python)​
