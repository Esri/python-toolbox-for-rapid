'''-------------------------------------------------------------------------------
 Tool Name:   PublishDischargeMap
 Source Name: PublishDischargeMap.py
 Version:     ArcGIS 10.3
 Author:      Environmental Systems Research Institute Inc.
 Updated by:  Environmental Systems Research Institute Inc.
 Description: Create a dischage map document.
 History:     Initial coding - 06/26/2015, version 1.0
 Updated:     07/31/2015, Added an optional input parameter Overwrite an existing service
-------------------------------------------------------------------------------'''
import os
import arcpy
import xml.dom.minidom as DOM


class PublishDischargeMap(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Publish Discharge Map"
        self.description = "Publish a discharge map document for stream flow visualization \
                            to an ArcGIS server"
        self.errorMessages = ["Incorrect map document"]
        self.canRunInBackground = False
        self.category = "Utilities"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name = "in_discharge_map",
                                 displayName = "Input Discharge Map",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEMapDocument"
                                 )

        param1 = arcpy.Parameter(name = "in_connection",
                                 displayName = "Input ArcGIS for Server Connection",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "DEServerConnection"
                                 )

        param2 = arcpy.Parameter(name = "in_service_name",
                                 displayName = "Input Service Name",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPString")

        param3 = arcpy.Parameter(name = "in_service_summary",
                                 displayName = "Input Service Summary",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "GPString")

        param4 = arcpy.Parameter(name = "in_service_tags",
                                 displayName = "Input Service Tags",
                                 direction = "Input",
                                 parameterType = "Optional",
                                 datatype = "GPString")

        param5 = arcpy.Parameter(name = "in_overwrite",
                                 displayName = "Overwrite an existing service",
                                 direction = "Input",
                                 parameterType = "Required",
                                 datatype = "GPBoolean")
        param5.value = False

        params = [param0, param1, param2, param3, param4, param5]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        '''Check if .mxd is the suffix of the input map document name'''
        if parameters[0].altered:
            (dirnm, basenm) = os.path.split(parameters[0].valueAsText)
            if not basenm.endswith(".mxd"):
                parameters[0].setErrorMessage(self.errorMessages[0])
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.env.overwriteOutput = True
        wrkspc = arcpy.env.scratchWorkspace
        if wrkspc is None:
            wrkspc = arcpy.env.scratchFolder
        else:
            if wrkspc.endswith('.gdb') or wrkspc.endswith('.sde') or wrkspc.endswith('.mdb'):
                wrkspc = arcpy.env.scratchFolder

        in_map_document = parameters[0].valueAsText
        in_connection = parameters[1].valueAsText
        in_service_name = parameters[2].valueAsText
        in_service_summary = parameters[3].valueAsText
        in_service_tags = parameters[4].valueAsText
        in_overwrite = parameters[5].value

        # Provide other service details
        sddraft = os.path.join(wrkspc, in_service_name + '.sddraft')
        sd = os.path.join(wrkspc, in_service_name + '.sd')


        # Create service definition draft
        arcpy.mapping.CreateMapSDDraft(in_map_document, sddraft, in_service_name,
                                      'ARCGIS_SERVER', in_connection, True, None, in_service_summary, in_service_tags)



        # Properties that will be changed in the sddraft xml
        soe = 'WMSServer'
        # Read the sddraft xml.
        doc = DOM.parse(sddraft)
        # Find all elements named TypeName. This is where the server object extension (SOE) names are defined.
        typeNames = doc.getElementsByTagName("TypeName")

        for typeName in typeNames:
            if typeName.firstChild.data == soe:
                typeName.parentNode.getElementsByTagName('Enabled')[0].firstChild.data = 'true'

        if in_overwrite == True:
            newType = 'esriServiceDefinitionType_Replacement'
            descriptions = doc.getElementsByTagName("Type")
            for desc in descriptions:
                if desc.parentNode.tagName == "SVCManifest":
                    if desc.hasChildNodes():
                        desc.firstChild.data = newType

        # Delete the old sddraft
        if os.path.isfile(sddraft):
            os.remove(sddraft)
        # Output the new sddraft
        f = open(sddraft, 'w')
        doc.writexml(f)
        f.close()


        # Analyze the service definition draft
        analysis = arcpy.mapping.AnalyzeForSD(sddraft)

        # Print errors, warnings, and messages returned from the analysis
        arcpy.AddMessage("The following information was returned during analysis of the MXD:")
        for key in ('messages', 'warnings', 'errors'):
          arcpy.AddMessage('----' + key.upper() + '---')
          vars = analysis[key]
          for ((message, code), layerlist) in vars.iteritems():
            arcpy.AddMessage('    {0} (CODE {1})'.format(message, code))
            arcpy.AddMessage('       applies to:')
            for layer in layerlist:
                arcpy.AddMessage(layer.name)

        # Stage and upload the service if the sddraft analysis did not contain errors
        if analysis['errors'] == {}:
            # Execute StageService. This creates the service definition.
            arcpy.StageService_server(sddraft, sd)

            # Execute UploadServiceDefinition. This uploads the service definition and publishes the service.
            arcpy.UploadServiceDefinition_server(sd, in_connection)
            arcpy.AddMessage("Service successfully published")
        else:
            arcpy.AddMessage("Service could not be published because errors were found during analysis.")

        arcpy.AddMessage(arcpy.GetMessages())

##        arcpy.AddMessage("Cleaning sd")
##        if os.path.isfile(sd):
##            os.remove(sd)
##        arcpy.AddMessage("Cleaning sddraft")
##        if os.path.isfile(sddraft):
##            os.remove(sddraft)

        return

##def main():
##    tool = CreateMapDocument()
##    tool.execute(tool.getParameterInfo(), None)
##
##if __name__ == '__main__':
##    main()


