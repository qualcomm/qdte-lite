# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from QutsAtom.Atom_AtomUtilityModule import *
from QutsAtom.Atom_DeviceManager_init import DeviceManagerList
from QutsAtom.Atom_QutsClient_init import QutsClientList

def getDeviceManager(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ServiceObject=QutsClientList.getDeviceManager(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(ServiceObject), ServiceObject)
    return ServiceObject!=0

def stopTcpServer(port, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-port:", type(port), port)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.stopTcpServer(port)

def getServicesList(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getServicesList()

def getDeviceImageInfoByProtocol(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDeviceImageInfoByProtocol(protocolHandle)

def setOperatingMode(deviceHandle, protocolHandle, mode, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-mode:", type(mode), mode)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.setOperatingMode(deviceHandle, protocolHandle, mode)

def getDeviceHandleFromProtocol(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDeviceHandleFromProtocol(protocolHandle)

def getDeviceList(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDeviceList()

def getLastError(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getLastError()

def getServicesForDevice(deviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getServicesForDevice(deviceHandle)

def enableProtocolDataMonitoring(protocolHandleList, enable, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandleList:", type(protocolHandleList), protocolHandleList)
    ATOM_DEBUG(qutsIndex, "argument-enable:", type(enable), enable)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.enableProtocolDataMonitoring(protocolHandleList, enable)

def getDevicesForService(serviceName, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-serviceName:", type(serviceName), serviceName)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDevicesForService(serviceName)

def resetPhone(deviceHandle, resetTimeout, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-resetTimeout:", type(resetTimeout), resetTimeout)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.resetPhone(deviceHandle, resetTimeout)

def createService(serviceName, deviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-serviceName:", type(serviceName), serviceName)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.createService(serviceName, deviceHandle)

def saveLogFilesWithFilenames(logNameConfig, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-logNameConfig:", type(logNameConfig), logNameConfig)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.saveLogFilesWithFilenames(logNameConfig)

def mergeDevice(sourceDeviceHandle, destinationDeviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-sourceDeviceHandle:", type(sourceDeviceHandle), sourceDeviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-destinationDeviceHandle:", type(destinationDeviceHandle), destinationDeviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.mergeDevice(sourceDeviceHandle, destinationDeviceHandle)

def enableDeviceDataMonitoring(deviceHandleList, enable, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandleList:", type(deviceHandleList), deviceHandleList)
    ATOM_DEBUG(qutsIndex, "argument-enable:", type(enable), enable)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.enableDeviceDataMonitoring(deviceHandleList, enable)

def getDeviceBuildId(deviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDeviceBuildId(deviceHandle)

def getChipName(deviceHandle, protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getChipName(deviceHandle, protocolHandle)

def getDeviceMode(deviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDeviceMode(deviceHandle)

def addTcpConnectionWithOptions(host, port, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-host:", type(host), host)
    ATOM_DEBUG(qutsIndex, "argument-port:", type(port), port)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.addTcpConnectionWithOptions(host, port, options)

def overrideUnknownProtocol(protocolHandle, newType, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-newType:", type(newType), newType)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.overrideUnknownProtocol(protocolHandle, newType)

def getProtocolList(deviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getProtocolList(deviceHandle)

def addTcpConnection(deviceHandle, protocolType, bIsClient, description, host, port, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolType:", type(protocolType), protocolType)
    ATOM_DEBUG(qutsIndex, "argument-bIsClient:", type(bIsClient), bIsClient)
    ATOM_DEBUG(qutsIndex, "argument-description:", type(description), description)
    ATOM_DEBUG(qutsIndex, "argument-host:", type(host), host)
    ATOM_DEBUG(qutsIndex, "argument-port:", type(port), port)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.addTcpConnection(deviceHandle, protocolType, bIsClient, description, host, port)

def getActiveLogSession(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getActiveLogSession()

def getProtocolLockStatus(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getProtocolLockStatus(protocolHandle)

def removeTcpConnection(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.removeTcpConnection(protocolHandle)

def setImei(deviceHandle, protocolHandle, imei, subscriptionId, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-imei:", type(imei), imei)
    ATOM_DEBUG(qutsIndex, "argument-subscriptionId:", type(subscriptionId), subscriptionId)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.setImei(deviceHandle, protocolHandle, imei, subscriptionId)

def startTcpServer(protocolType, port, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolType:", type(protocolType), protocolType)
    ATOM_DEBUG(qutsIndex, "argument-port:", type(port), port)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.startTcpServer(protocolType, port)

def startTcpServerWithOptions(port, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-port:", type(port), port)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.startTcpServerWithOptions(port, options)

def openLogSession(logFiles, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-logFiles:", type(logFiles), logFiles)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.openLogSession(logFiles)

def getTcpServerList(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getTcpServerList()

def enableProtocolLog(protocolHandle, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.enableProtocolLog(protocolHandle, options)

def startLogging(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.startLogging()

def resetLogFiles(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.resetLogFiles()

def saveLogFiles(saveFolder, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-saveFolder:", type(saveFolder), saveFolder)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.saveLogFiles(saveFolder)

def getProtocolConfiguration(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getProtocolConfiguration(protocolHandle)

def getCurrentLogFileSize(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getCurrentLogFileSize(protocolHandle)

def setEsn(deviceHandle, protocolHandle, esn, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-esn:", type(esn), esn)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.setEsn(deviceHandle, protocolHandle, esn)

def attachToLogSession(clientId, logSession, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-clientId:", type(clientId), clientId)
    ATOM_DEBUG(qutsIndex, "argument-logSession:", type(logSession), logSession)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.attachToLogSession(clientId, logSession)

def logAnnotation(annotation, messageId, protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-annotation:", type(annotation), annotation)
    ATOM_DEBUG(qutsIndex, "argument-messageId:", type(messageId), messageId)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.logAnnotation(annotation, messageId, protocolHandle)

def resetPhoneByProtocol(deviceHandle, protocolHandle, resetTimeout, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-resetTimeout:", type(resetTimeout), resetTimeout)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.resetPhoneByProtocol(deviceHandle, protocolHandle, resetTimeout)

def configureProtocol(protocolConfiguration, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolConfiguration:", type(protocolConfiguration), protocolConfiguration)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.configureProtocol(protocolConfiguration)

def getImei(deviceHandle, protocolHandle, subscriptionId, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-subscriptionId:", type(subscriptionId), subscriptionId)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getImei(deviceHandle, protocolHandle, subscriptionId)

def restartQmiReadyScan(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.restartQmiReadyScan(protocolHandle)

def getThroughputStatistics(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getThroughputStatistics(protocolHandle)

def getEsn(deviceHandle, protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getEsn(deviceHandle, protocolHandle)

def getMeid(deviceHandle, protocolHandle, subscriptionId, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-subscriptionId:", type(subscriptionId), subscriptionId)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getMeid(deviceHandle, protocolHandle, subscriptionId)

def setMeid(deviceHandle, protocolHandle, meid, subscriptionId, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-meid:", type(meid), meid)
    ATOM_DEBUG(qutsIndex, "argument-subscriptionId:", type(subscriptionId), subscriptionId)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.setMeid(deviceHandle, protocolHandle, meid, subscriptionId)

def checkSpc(deviceHandle, protocolHandle, spc, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    ATOM_DEBUG(qutsIndex, "argument-spc:", type(spc), spc)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.checkSpc(deviceHandle, protocolHandle, spc)

def getOperatingMode(deviceHandle, protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getOperatingMode(deviceHandle, protocolHandle)

def transferImageBhi(programmerPath, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-programmerPath:", type(programmerPath), programmerPath)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.transferImageBhi(programmerPath)

def getDeviceUsageIndicators(deviceHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.getDeviceUsageIndicators(deviceHandle)

def enableFunctionLog(deviceHandle, areas, options, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-areas:", type(areas), areas)
    ATOM_DEBUG(qutsIndex, "argument-options:", type(options), options)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.enableFunctionLog(deviceHandle, areas, options)

def disableFunctionLog(deviceHandle, areas, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-deviceHandle:", type(deviceHandle), deviceHandle)
    ATOM_DEBUG(qutsIndex, "argument-areas:", type(areas), areas)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.disableFunctionLog(deviceHandle, areas)

def disableProtocolLog(protocolHandle, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-protocolHandle:", type(protocolHandle), protocolHandle)
    DeviceManagerObject=DeviceManagerList.GetDeviceManagerObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(DeviceManagerObject), DeviceManagerObject)
    return DeviceManagerObject.disableProtocolLog(protocolHandle)

