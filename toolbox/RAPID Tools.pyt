import os
import sys

scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.append(scripts_dir)
# Do not compile .pyc files for the tool modules.
sys.dont_write_bytecode = True

from AddSPTFields import AddSPTFields
from AutomaticRAPIDfileGenerator import AutomaticRAPIDfileGenerator
from CopyDataToServer import CopyDataToServer
from CreateNetworkConnectivityFile import CreateNetworkConnectivityFile
from CreateNetworkConnectivityFileNHDPlus import CreateNetworkConnectivityFileNHDPlus
from CreateMuskingumParameterFiles import CreateMuskingumParameterFiles
from CreateMuskingumKFile import CreateMuskingumKFile
from CreateMuskingumKfacFile import CreateMuskingumKfacFile
from CreateRivIDGageFile import CreateRivIDGageFile
from CreateSubsetFile import CreateSubsetFile
from CreateWeightTableFromWRFGeogrid import CreateWeightTableFromWRFGeogrid
from CreateInflowFileFromWRFHydroRunoff import CreateInflowFileFromWRFHydroRunoff
from CreateWeightTableFromECMWFRunoff import CreateWeightTableFromECMWFRunoff
from CreateInflowFileFromECMWFRunoff import CreateInflowFileFromECMWFRunoff
from CreateWeightTableFromLDASRunoff import CreateWeightTableFromLDASRunoff
from CreateWeightTableFromLISRunoff import CreateWeightTableFromLISRunoff
from CreateDischargeTable import CreateDischargeTable
from CreateDischargeMap import CreateDischargeMap
from FlowlineToPoint import FlowlineToPoint
from HydroSHEDStoStreamNetwork import HydroSHEDStoStreamNetwork
from CreateMuskingumXFile import CreateMuskingumXFile
from PublishDischargeMap import PublishDischargeMap
from StreamNetworktoRAPID import StreamNetworktoRAPID
from StreamNetworktoSPT import StreamNetworktoSPT
from UpdateWeightTable import UpdateWeightTable
from UpdateDischargeMap import UpdateDischargeMap

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "RAPID Tools"
        self.alias = "RAPIDTools"

        # List of tool classes associated with this toolbox
        self.tools = [AddSPTFields,
                      AutomaticRAPIDfileGenerator, 
                      CopyDataToServer,
                      CreateNetworkConnectivityFile,
                      CreateNetworkConnectivityFileNHDPlus,
                      CreateMuskingumParameterFiles,
                      CreateMuskingumKFile,
                      CreateMuskingumKfacFile,
                      CreateMuskingumXFile, 
                      CreateRivIDGageFile, 
                      CreateSubsetFile,
                      CreateWeightTableFromWRFGeogrid,
                      CreateInflowFileFromWRFHydroRunoff,
                      CreateWeightTableFromECMWFRunoff,
                      CreateInflowFileFromECMWFRunoff,
                      CreateWeightTableFromLDASRunoff,
                      CreateWeightTableFromLISRunoff,
                      CreateDischargeTable,
                      CreateDischargeMap,
                      FlowlineToPoint,
                      HydroSHEDStoStreamNetwork,
                      PublishDischargeMap,
                      StreamNetworktoRAPID,
                      StreamNetworktoSPT,
                      UpdateWeightTable,
                      UpdateDischargeMap,
                      ]

