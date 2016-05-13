import os
import sys

scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.append(scripts_dir)
# Do not compile .pyc files for the tool modules.
sys.dont_write_bytecode = True

from CreateNetworkConnectivityFile import CreateNetworkConnectivityFile
from CreateMuskingumParameterFiles import CreateMuskingumParameterFiles
from CreateSubsetFile import CreateSubsetFile
from CreateWeightTableFromWRFGeogrid import CreateWeightTableFromWRFGeogrid
from CreateInflowFileFromWRFHydroRunoff import CreateInflowFileFromWRFHydroRunoff
from CreateWeightTableFromECMWFRunoff import CreateWeightTableFromECMWFRunoff
from CreateInflowFileFromECMWFRunoff import CreateInflowFileFromECMWFRunoff
from UpdateWeightTable import UpdateWeightTable
from CreateDischargeTable import CreateDischargeTable
from CreateDischargeMap import CreateDischargeMap
from CopyDataToServer import CopyDataToServer
from UpdateDischargeMap import UpdateDischargeMap
from PublishDischargeMap import PublishDischargeMap
from FlowlineToPoint import FlowlineToPoint
from CreateWaterLevelTable import CreateWaterLevelTable
from CreateHANDMosaicDataset import CreateHANDMosaicDataset
from CatchmentToRaster import CatchmentToRaster



class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "RAPIDTools"
        self.alias = "RAPID Tools"

        # List of tool classes associated with this toolbox
        self.tools = [CreateNetworkConnectivityFile,
 		      CreateMuskingumParameterFiles,
		      CreateSubsetFile,
              CreateWeightTableFromWRFGeogrid,
              CreateInflowFileFromWRFHydroRunoff,
              CreateWeightTableFromECMWFRunoff,
              CreateInflowFileFromECMWFRunoff,
              UpdateWeightTable,
              CreateDischargeTable,
              CreateDischargeMap,
              CopyDataToServer,
              UpdateDischargeMap,
              PublishDischargeMap,
              FlowlineToPoint,
              CreateWaterLevelTable,
	      CreateHANDMosaicDataset,
	      CatchmentToRaster]

