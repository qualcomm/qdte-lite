# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
import sys
import threading
import platform

from QutsAtom.Atom_AtomUtilityModule import *

import QutsClient
from QutsAtom.Atom_CallbackServer import QutsClientCallbackObject

import ClientCallback.ClientCallback
import ClientCallback.constants
import DeviceManager.DeviceManager
import DeviceManager.constants
import LogSession.LogSession
import LogSession.constants
import AdbService.AdbService
import AdbService.constants
import DeviceConfigService.DeviceConfigService
import DeviceConfigService.constants
import DiagService.DiagService
import DiagService.constants
import GpsService.GpsService
import GpsService.constants
import ImageManagementService.ImageManagementService
import ImageManagementService.constants
#import QdssService.QdssService
#import QdssService.constants
import QmiService.QmiService
import QmiService.constants

class QutsClientObject:
    clientName=""
    client=None
    LogSessionObj=None
    DeviceManagerObj=None
    UtilityServiceObject=None
    clientCallback=None
    logSessionPath=None

    def __init__(self, hostName, multithreaded, qidx):
        self.multiService={}
        self.clientName="Atom QUTS Test {}".format(qidx)
        ATOM_LOG("Create", self.clientName)
        host = "127.0.0.1" if hostName=="" else hostName
        ATOM_LOG("Initialize on", host)
        self.client=QutsClient.QutsClient(clientName="Atom QUTS Test {}".format(qidx), hostname=host, multithreadedClient=multithreaded)
        self.clientCallback=QutsClientCallbackObject(self.client)

    def getFirstQmiProtocol(self, deviceHandle):
        ATOM_DEBUG("Check Protocol Number")
        protocols=self.getDeviceManager().getProtocolList(deviceHandle)
        firstProtocol=0
        for protocol in protocols:
            if(protocol.protocolType == Common.ttypes.ProtocolType.PROT_QMI):
                if(ATOM_GET_REMOTE_OPSYS()):
                    if(ATOM_GET_REMOTE_OPSYS()=="Linux"):
                        if(protocol.description.find("usb0_0") != -1):
                            firstProtocol=protocol.protocolHandle
                            ATOM_LOG("Found usb0_0, only initialize on protocol handle", protocol.protocolHandle, "Description", protocol.description)
                        elif(firstProtocol==0):
                            firstProtocol=protocol.protocolHandle
                            ATOM_LOG("Found first QMI protocol, store on protocol handle", protocol.protocolHandle, "Description", protocol.description)
                        else:
                            ATOM_WARNING("Multiply protocol found, only initialize on first protocol handle", protocol.protocolHandle, "Description", protocol.description)
                    else:
                        raise OSError("Invalid OS:"+ATOM_GET_REMOTE_OPSYS())
                else:
                    if(platform.system().startswith("Windows")):
                        if(firstProtocol==0):
                            firstProtocol=protocol.protocolHandle
                        else:
                            ATOM_WARNING("Multiply protocol found, only initialize on first protocol, ignore handle:", protocol.protocolHandle, "Description", protocol.description)
                    elif(platform.system().startswith("Linux")):
                        if(protocol.description.find("usb0_0") != -1):
                            firstProtocol=protocol.protocolHandle
                            ATOM_LOG("Found usb0_0, only initialize on protocol handle", protocol.protocolHandle, "Description", protocol.description)
                        elif(firstProtocol==0):
                            firstProtocol=protocol.protocolHandle
                            ATOM_LOG("Found first QMI protocol, store on protocol handle", protocol.protocolHandle, "Description", protocol.description)
                        else:
                            ATOM_WARNING("Multiply protocol found, only initialize on first protocol handle", protocol.protocolHandle, "Description", protocol.description)
                    else:
                        raise OSError("Invalid OS:"+platform.system())
        return firstProtocol

    def getMdmDiag(self, deviceHandle):
        ATOM_DEBUG("Check Protocol Number")
        protocols=self.getDeviceManager().getProtocolList(deviceHandle)
        mdmProtocol=0
        for protocol in protocols:
            if(protocol.protocolType == Common.ttypes.ProtocolType.PROT_DIAG and protocol.description.find("MSM") == -1):
                mdmProtocol=protocol.protocolHandle
                return mdmProtocol
        return mdmProtocol
        
    def createMultiService(self, serviceName, deviceHandle):
        ATOM_LOG("Create", serviceName, "from", self.clientName)
        serv=None

        if(serviceName==AdbService.constants.ADB_SERVICE_NAME):
            serv=AdbService.AdbService.Client(self.client.createService(serviceName, deviceHandle))
        elif(serviceName==DeviceConfigService.constants.DEVICE_CONFIG_SERVICE_NAME):
            serv=DeviceConfigService.DeviceConfigService.Client(self.client.createService(serviceName, deviceHandle))
            firstProtocol=self.getMdmDiag(deviceHandle)
            qmiProtocol=self.getFirstQmiProtocol(deviceHandle)
            if (serv == None or 0 != serv.initializeServiceByProtocol(firstProtocol, qmiProtocol)):
                ATOM_ERROR(self.clientName, serviceName, "init failed")
                return None
            return serv
        elif(serviceName==DiagService.constants.DIAG_SERVICE_NAME):
            serv=DiagService.DiagService.Client(self.client.createService(serviceName, deviceHandle))
            firstProtocol=self.getMdmDiag(deviceHandle)
            if (serv == None or 0 != serv.initializeServiceByProtocol(firstProtocol)):
                ATOM_ERROR(self.clientName, serviceName, "init failed")
                return None
            return serv

        elif(serviceName==GpsService.constants.GPS_SERVICE_NAME):
            serv=GpsService.GpsService.Client(self.client.createService(serviceName, deviceHandle))
        elif(serviceName==ImageManagementService.constants.IMAGE_MANAGEMENT_SERVICE_NAME):
            serv=ImageManagementService.ImageManagementService.Client(self.client.createService(serviceName, deviceHandle))
        #elif(serviceName==QdssService.constants.QDSS_SERVICE_NAME):
        #    serv=QdssService.QdssService.Client(self.client.createService(serviceName, deviceHandle))
        elif(serviceName==QmiService.constants.QMI_SERVICE_NAME):
            serv=QmiService.QmiService.Client(self.client.createService(serviceName, deviceHandle))
        else:
            ATOM_LOG("Create", serviceName, "from", self.clientName, "is invalid")
        
        if (serv == None or 0 != serv.initializeService()):
            ATOM_ERROR(self.clientName, serviceName, "init failed")
            return None
        return serv

    def createService(self, serviceName, deviceHandle):
        serv=None
        if(self.multiService):
            if(serviceName in self.multiService):
                #Service type exist
                if(self.multiService[serviceName]):
                    #Service type not empty
                    if(deviceHandle in self.multiService[serviceName]):
                        #service exist
                        ATOM_DEBUG(self.clientName, "Find existing", serviceName)
                        serv=self.multiService.get(serviceName).get(deviceHandle)
                    else:
                        #service not exist
                        serv=self.createMultiService(serviceName, deviceHandle)
                else:
                    #Service type empty
                    serv=self.createMultiService(serviceName, deviceHandle)
                    if(serv!=None):
                        self.multiService.get(deviceHandle)[deviceHandle]=serv
            else:
                #Service type not exist
                servType={}
                serv=self.createMultiService(serviceName, deviceHandle)
                if(serv!=None):
                    servType[deviceHandle]=serv
                    self.multiService[serviceName]=servType
        else:
            #Service List empty
            servType={}
            serv=self.createMultiService(serviceName, deviceHandle)
            if(serv!=None):
                servType[deviceHandle]=serv
                self.multiService[serviceName]=servType
        return serv

    def deleteService(self, serviceName, deviceHandle):
        serv=None
        if(self.multiService):
            if(serviceName in self.multiService):
                #Service type exist
                if(self.multiService[serviceName]):
                    #Service type not empty
                    if(deviceHandle in self.multiService[serviceName]):
                        #service exist
                        ATOM_LOG(self.clientName, "delete existing", serviceName, "for", deviceHandle)
                        serv=self.multiService.get(serviceName).get(deviceHandle)
                        self.multiService.get(serviceName).pop(deviceHandle)
                    else:
                        #service not exist
                        ATOM_ERROR(self.clientName, serviceName, "not initialized for", deviceHandle)
                else:
                    #Service type empty
                    ATOM_ERROR(self.clientName, serviceName, "not initialized for", deviceHandle)
            else:
                #Service type not exist
                ATOM_ERROR(self.clientName, serviceName, "not initialized for", deviceHandle)
        else:
            #Service List empty
            ATOM_ERROR(self.clientName, serviceName, "not initialized for", deviceHandle)
        return serv

    def getDeviceManager(self):
        if(self.DeviceManagerObj==None):
            ATOM_LOG("Create DeviceManager from", self.clientName)
            self.DeviceManagerObj=self.client.getDeviceManager()
        else:
            ATOM_DEBUG(self.clientName, "Find existing DeviceManager")
        return self.DeviceManagerObj

    def openLogSession(self, files):
        if(self.LogSessionObj==None):
            ATOM_LOG("Create LogSession from", self.clientName)
        else:
            ATOM_DEBUG(self.clientName, "Find existing LogSession")

        self.LogSessionObj=self.client.openLogSession(files)
        logSessionPath=files
        return self.LogSessionObj

    def getLogSession(self):
        if(self.LogSessionObj==None):
            ATOM_ERROR(self.clientName, "LogSession it not initialized")
        else:
            ATOM_DEBUG(self.clientName, "Get existing LogSession")
        return self.LogSessionObj

    def deleteLogSession(self):
        if(self.LogSessionObj==None):
            ATOM_ERROR(self.clientName, "LogSession it not initialized")
            return None
        else:
            ATOM_LOG(self.clientName, "delete existing LogSession")
            serv = self.LogSessionObj
            self.LogSessionObj=None
            return serv

    def getUtilityService(self):
        if(self.UtilityServiceObject==None):
            ATOM_LOG("Create UtilityService from", self.clientName)
            self.UtilityServiceObject=self.client.getUtilityService()
        else:
            ATOM_DEBUG(self.clientName, "Find existing UtilityService")
        return self.UtilityServiceObject

    def getClientCallback(self):
        return self.clientCallback

    def ResetDataViewUpdateDoneEvent(self):
        self.clientCallback.dataViewUpdateDoneEvent.clear()
        return self.clientCallback.dataViewUpdateDoneEvent

class QutsClientList:
    multithreaded=False
    hostName=""
    clientObjects={}
    lock=threading.Lock()

    @staticmethod
    def GetQutsClientObjectInternal(qidx):
        if (qidx in QutsClientList.clientObjects):
            ATOM_DEBUG(qidx, "Find Existing QutsClientObject")
            client=QutsClientList.clientObjects[qidx]
            ATOM_DEBUG(qidx, type(client), client)
        else:
            ATOM_LOG("Enable Host", QutsClientList.hostName)
            client=QutsClientObject(QutsClientList.hostName, QutsClientList.multithreaded, qidx)
            ATOM_DEBUG(qidx, type(client), client)
            QutsClientList.clientObjects[qidx]=client
        return client

    @staticmethod
    def enableQutsClientMultiThreaded():
        QutsClientList.multithreaded=True
    
    @staticmethod
    def enableRemoteMachine(host):
        QutsClientList.hostName=host
        
    @staticmethod
    def getQutsClientObject(qidx):
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "getQutsClientObject Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx).client
        ATOM_DEBUG(qidx, "getQutsClientObject Release Lock")
        QutsClientList.lock.release()
        return client

    @staticmethod
    def getQutsClientCallbackObject(qidx):
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "getQutsClientCallbackObject Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        callback=client.getClientCallback()
        ATOM_DEBUG(qidx, "getQutsClientCallbackObject Release Lock")
        QutsClientList.lock.release()
        return callback

    @staticmethod
    def createService(qidx, serviceName, deviceHandle):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "createService Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.createService(serviceName, deviceHandle)
        ATOM_DEBUG(qidx, "createService Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def deleteService(qidx, serviceName, deviceHandle):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "deleteService Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.createService(serviceName, deviceHandle)
        ATOM_DEBUG(qidx, "deleteService Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def getDeviceManager(qidx):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "getDeviceManager Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.getDeviceManager()
        ATOM_DEBUG(qidx, "getDeviceManager Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def getLogSession(qidx):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "getLogSession Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.getLogSession()
        ATOM_DEBUG(qidx, "getLogSession Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def openLogSession(qidx, files):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "openLogSession Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.openLogSession(files)
        ATOM_DEBUG(qidx, "openLogSession Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def deleteLogSession(qidx):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "deleteLogSession Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.deleteLogSession()
        ATOM_DEBUG(qidx, "deleteLogSession Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def getUtilityService(qidx):
        serv=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "getUtilityService Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        serv=client.getUtilityService()
        ATOM_DEBUG(qidx, "getUtilityService Release Lock")
        QutsClientList.lock.release()
        return serv

    @staticmethod
    def ResetDataViewUpdateDoneEvent(qidx):
        doneEvent=None
        QutsClientList.lock.acquire()
        ATOM_DEBUG(qidx, "ResetDataViewUpdateDoneEvent Get Lock")
        client=QutsClientList.GetQutsClientObjectInternal(qidx)
        doneEvent=client.ResetDataViewUpdateDoneEvent()
        ATOM_DEBUG(qidx, "ResetDataViewUpdateDoneEvent Release Lock")
        QutsClientList.lock.release()
        return doneEvent
