# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from QutsAtom.Atom_AtomUtilityModule import *
from QutsAtom.Atom_ImageManagementService_init import ImageManagementServiceList

def downloadBuild(atomMultiHandle, buildPath, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-buildPath:", type(buildPath), buildPath)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.downloadBuild(buildPath, options)

def setDdrStorePath(atomMultiHandle, ddrStorePath, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-ddrStorePath:", type(ddrStorePath), ddrStorePath)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.setDdrStorePath(ddrStorePath)

def getDeviceImageMode(atomMultiHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.getDeviceImageMode()

def getLastError(atomMultiHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.getLastError()

def initializeService(atomMultiHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle, )
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject!=0

def transferImages(atomMultiHandle, imageList, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-imageList:", type(imageList), imageList)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.transferImages(imageList)

def destroyService(atomMultiHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ImageManagementServiceObject=ImageManagementServiceList.DeleteImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "remove-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.destroyService()

def collectMemoryDump(atomMultiHandle, pathName, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-pathName:", type(pathName), pathName)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.collectMemoryDump(pathName)

def getCommandResults(atomMultiHandle, commandResults, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-commandResults:", type(commandResults), commandResults)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.getCommandResults(commandResults)

def collectMemoryDumpWithOptions(atomMultiHandle, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.collectMemoryDumpWithOptions(options)

def startRemoteEfsSync(atomMultiHandle, pathName, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-pathName:", type(pathName), pathName)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.startRemoteEfsSync(pathName)

def stopRemoteEfsSync(atomMultiHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.stopRemoteEfsSync()

def resetDevice(atomMultiHandle, timeout, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-timeout:", type(timeout), timeout)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.resetDevice(timeout)

def switchToEdl(atomMultiHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.switchToEdl()

def erasePartition(atomMultiHandle, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.erasePartition(options)

def getFlashInfo(atomMultiHandle, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.getFlashInfo(options)

def initPartitionTable(atomMultiHandle, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.initPartitionTable(options)

def readPartitionData(atomMultiHandle, dataChunks, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-dataChunks:", type(dataChunks), dataChunks)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.readPartitionData(dataChunks)

def writePartitionData(atomMultiHandle, dataChunks, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-dataChunks:", type(dataChunks), dataChunks)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.writePartitionData(dataChunks)

def erasePartitionData(atomMultiHandle, dataChunks, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-atomMultiHandle:", type(atomMultiHandle), atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "argument-dataChunks:", type(dataChunks), dataChunks)
    ImageManagementServiceObject=ImageManagementServiceList.GetImageManagementServiceObject(qutsIndex, atomMultiHandle)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ImageManagementServiceObject), ImageManagementServiceObject)
    return ImageManagementServiceObject.erasePartitionData(dataChunks)

