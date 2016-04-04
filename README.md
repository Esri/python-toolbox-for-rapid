# RAPID Tools

This repository houses a python toolbox of tools for preprocessing inputs and postprocessing outputs of the RAPID (Routing Application for Parallel computation of Discharge) model. To know more information about RAPID, please visit its [website] (http://rapid-hub.org/).

## Getting Started

1. Install [ArcGIS for Desktop 10.4](http://desktop.arcgis.com/en/arcmap/) 
2. If your ArcGIS for Desktop is previous to 10.2, you must install [netCDF4 python package] (https://pypi.python.org/pypi/netCDF4). An executable file for installing netCDF4-1.0.8 with python 2.7 is available [here] (http://downloads.esri.com/archydro/archydro/Setup/10.2.x/rapid/).
3. Download the toolbox and place it in a folder. Access the folder from Catalog in ArcMap. You will see the following:
![alt tag](/toolbox_screenshot.png)


## Issues

Find a bug or want to request a new feature?  Please let us know by [submitting an issue](https://github.com/Esri/raster-functions/issues).

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).


## Tools

### Preprocessing tools

* #### Create Connectivity File
This tool creates the stream network connectivity file based on two fields in the input drainage line feature class: HydroID, and   NextDownID. It does the following:
* Find the HydroID of each stream
* Count the total number of its upstreams
* Write the stream HydroID, the total number of its upstreams, and the HydroID(s) of all upstream(s) into the output file. The sequence of the records follows the ascending order of the stream HydroID.

* #### Create Subset File

* #### Create Muskingum Parameters File

* #### Create Weight Table From ECMWF/WRF-Hydro Runoff

* #### Update Weight Table

* #### Create Inflow File From ECMWF/WRF-Hydro Runoff


### Postprocessing tools

* #### Create Discharge Table

* #### Create Discharge Map

* #### Update Discharge Map


### Utilities Tools

* #### Flowline to Point

* #### Copy Data To Server

* #### Publish Discharge Map


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
