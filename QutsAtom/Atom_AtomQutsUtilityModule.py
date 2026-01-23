# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from QutsAtom.Atom_AtomUtilityModule import *

from QutsAtom import Atom_QutsClient
from QutsAtom import Atom_DiagService
from QutsAtom import Atom_LogSession
from QutsAtom import Atom_DeviceManager

import Common.ttypes

###QUTS related
def ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle, request, diagReturnConfig=None, timeout=500, sendAcync=False, asyncTimeout=10000, qutsIndex=0):
    if(diagReturnConfig==None):
        diagReturnConfig=ATOM_CREATE_DIAG_RETURN_CONFIG()
    qutsprefix = "QutsClient_{}".format(qutsIndex)
    if(sendAcync):
        responseAsync=[]
        ATOM_DEBUG(qutsprefix, "Send async command", request)
        transactionId = Atom_DiagService.sendRawRequestAsync(deviceHandle, request, qutsIndex)
        #Immediate Response
        response = Atom_DiagService.getResponseAsync(deviceHandle, transactionId, diagReturnConfig, timeout, qutsIndex)
        ATOM_DEBUG(qutsprefix, "Async immediate Response:", response)
        if(response.packetType == Common.ttypes.DiagPacketType.UNKNOWN_PACKET_TYPE or response.packetId == None):
            ATOM_WARNING(qutsprefix, "For Request:", ATOM_PARSE_HEX_BUFFER(request))
            ATOM_WARNING(qutsprefix, "NULL immediate response received")
            responseAsync.append(response)
            return responseAsync
        if(response.packetType == Common.ttypes.DiagPacketType.RESPONSE and response.packetId == "19"):
            ATOM_WARNING(qutsprefix, "For Request:", ATOM_PARSE_HEX_BUFFER(request))
            ATOM_WARNING(qutsprefix, "Invalid immediate response received")
            responseAsync.append(response)
            return responseAsync
        responseAsync.append(response)
        #time.sleep(2)
        #Delayed Response
        response = Atom_DiagService.getResponseAsync(deviceHandle, transactionId, diagReturnConfig, 10000, qutsIndex)
        ATOM_DEBUG(qutsprefix, "Async delayed Response:", response)
        if(response.packetType == Common.ttypes.DiagPacketType.UNKNOWN_PACKET_TYPE or response.packetId == None):
            ATOM_WARNING(qutsprefix, "For Request:", ATOM_PARSE_HEX_BUFFER(request))
            ATOM_WARNING(qutsprefix, "NULL delayed response received")
        if(response.packetType == Common.ttypes.DiagPacketType.RESPONSE and response.packetId == "19"):
            ATOM_WARNING(qutsprefix, "For Request:", ATOM_PARSE_HEX_BUFFER(request))
            ATOM_WARNING(qutsprefix, "Invalid delayed response received")
        responseAsync.append(response)
        return responseAsync
    else:
        ATOM_DEBUG(qutsprefix, "Send sync command", request)
        response = Atom_DiagService.sendRawRequest(deviceHandle, request, diagReturnConfig, timeout, qutsIndex)
        ATOM_DEBUG(qutsprefix, "Sync Response:", response)
        if(response.packetType == Common.ttypes.DiagPacketType.UNKNOWN_PACKET_TYPE or response.packetId == None):
            ATOM_WARNING(qutsprefix, "For Request:", ATOM_PARSE_HEX_BUFFER(request))
            ATOM_WARNING(qutsprefix, "NULL response received")
        if(response.packetType == Common.ttypes.DiagPacketType.RESPONSE and response.packetId == "19"):
            ATOM_WARNING(qutsprefix, "For Request:", ATOM_PARSE_HEX_BUFFER(request))
            ATOM_WARNING(qutsprefix, "Invalid command response received")
        return [response]

###DO NOT USE IT FOR MULTIPLY FILES NOW
def ATOM_LOAD_DATA_FROM_FILE(path, protocols, dataReturnConfig=None, ViewName=None, qutsIndex=0):
    qutsprefix = "QutsClient_{}".format(qutsIndex)
    if (Atom_LogSession.openLogSession([path], qutsIndex)):
        if(dataReturnConfig==None):
            dataReturnConfig=ATOM_CREATE_DATA_RETURN_CONFIG_FOR_PROTOCOLS(protocols)
        if(ViewName==None):
            ViewName="DefaultView_{}".format(qutsIndex)
        protocolHandles=ATOM_CREATE_PROTOCOLS_HANDLE_LIST_FOR_PROTOCOLS(protocols)
        evt=Atom_QutsClient.resetDataViewUpdateDoneEvent(qutsIndex)
        Atom_LogSession.createDefaultDataView(ViewName, protocolHandles, dataReturnConfig, qutsIndex)
        #wait for load done here
        ATOM_LOG(qutsprefix, "Wait for load done...")
        evt.wait()
        ATOM_LOG(qutsprefix, "Load finished...")
        packetRange = LogSession.ttypes.PacketRange()
        packetRange.beginIndex = 0
        packetRange.endIndex = Atom_LogSession.getDataViewItemCount(ViewName, qutsIndex) - 1
        ATOM_LOG(qutsprefix, packetRange)
        dataResult = Atom_LogSession.getDataViewItems(ViewName, packetRange, qutsIndex);
        Atom_LogSession.destroyLogSession(qutsIndex)
        return dataResult
    else:
        ATOM_ERROR(qutsprefix, "Fail to initialize log session")
        return None

def ATOM_LOAD_FILTERED_DATA_FROM_FILE(path, dataPacketFilter, dataReturnConfig=None, ViewName=None, qutsIndex=0):
    qutsprefix = "QutsClient_{}".format(qutsIndex)
    if (Atom_LogSession.openLogSession([path], qutsIndex)):
        if(dataReturnConfig==None):
            protocolTypes=ATOM_CREATE_PROTOCOL_TYPE_LIST_FROM_FILTER(dataPacketFilter)
            dataReturnConfig=ATOM_CREATE_DATA_RETURN_CONFIG_FOR_PROTOCOL_TYPES(protocolTypes)
        if(ViewName==None):
            ViewName="DataView_{}".format(qutsIndex)
        evt=Atom_QutsClient.resetDataViewUpdateDoneEvent(qutsIndex)
        Atom_LogSession.createDataView(ViewName, dataPacketFilter, dataReturnConfig, qutsIndex)
        ATOM_LOG(qutsprefix, "Wait for load done...")
        evt.wait()
        ATOM_LOG(qutsprefix, "Load finished...")
        packetRange = LogSession.ttypes.PacketRange()
        packetRange.beginIndex = 0
        packetRange.endIndex = Atom_LogSession.getDataViewItemCount(ViewName, qutsIndex)
        ATOM_LOG(qutsprefix, packetRange)
        dataResult = Atom_LogSession.getDataViewItems(ViewName, packetRange, qutsIndex);
        Atom_LogSession.destroyLogSession(qutsIndex)
        return dataResult
    else:
        ATOM_ERROR(qutsprefix, "Fail to initialize log session")
        return None

def ATOM_GET_ALL_DATA_FROM_DATA_QUEUE(deviceHandle, dataqueueName, packetPerRead=20, timeout=500, qutsIndex=0):
    diagPackets=[]
    qutsprefix = "QutsClient_{}".format(qutsIndex)

    while(True):
        resultPackets = Atom_DiagService.getDataQueueItems(deviceHandle, dataqueueName, packetPerRead, timeout, qutsIndex)
        ATOM_DEBUG(qutsprefix, len(resultPackets), " packet(s) received")
        for i in range(len(resultPackets)):
            ATOM_DEBUG(qutsprefix, Common.ttypes.DiagPacketType._VALUES_TO_NAMES[resultPackets[i].packetType], resultPackets[i].packetId, resultPackets[i].receiveTimeString , resultPackets[i].packetName)
        diagPackets.extend(resultPackets)
        if(len(resultPackets)<packetPerRead):
            ATOM_DEBUG(qutsprefix, "Read all")
            break
    return diagPackets

def ATOM_GET_PROTOCOLS_FOR_DEVICES(devicesHandles, protocolTypes, qutsIndex=0):
    protocolHandles=[]
    qutsprefix = "QutsClient_{}".format(qutsIndex)
    deviceList = Atom_DeviceManager.getDeviceList(qutsIndex)
    i=0
    for device in deviceList:
        ATOM_DEBUG(qutsprefix, "Device {}".format(i), device.description)
        if(device.deviceHandle in devicesHandles):
            ATOM_DEBUG(qutsprefix, "Device Found")
            ATOM_DEBUG (qutsprefix, device.serialNumber)
            ATOM_DEBUG (qutsprefix, device.adbSerialNumber)
            buildId=Atom_DeviceManager.getDeviceBuildId(device.deviceHandle, qutsIndex)
            ATOM_DEBUG(buildId)
            j=0
            for protocol in device.protocols:
                ATOM_DEBUG(qutsprefix, "Protocol {}".format(j), protocol.description, protocol.protocolType)
                if(protocol.protocolType in protocolTypes):
                    protocolHandles.append(protocol)
            j+=1
        i+=i
    return protocolHandles

def ATOM_CREATE_DATA_RETURN_CONFIG_FOR_DEVICES(devicesHandles,
    diagConfig=ATOM_CREATE_DIAG_RETURN_CONFIG(),
    qmiConfig=None,
    adbConfig=None,
    saharaConfig=None,
    fastbootConfig=None,
    nmeaConfig=None,
    qdssConfig=None,
    adplConfig=None,
    qutsIndex=0):
    protocolHandles=ATOM_GET_PROTOCOLS_FOR_DEVICES(devicesHandles, qutsIndex)
    return ATOM_CREATE_DATA_RETURN_CONFIG_FOR_PROTOCOLS(protocolHandles,diagConfig,qmiConfig,adbConfig,saharaConfig,fastbootConfig,nmeaConfig,qdssConfig,adplConfig)

def ATOM_CREATE_DATA_FILTER_FOR_DEVICES(devicesHandles,
    protocolRange,
    diagFilter=ATOM_CREATE_DIAG_FILTER(),
    qmiFilter=None,
    adbFilter=None,
    saharaFilter=None,
    fastbootFilter=None,
    nmeaFilter=None,
    qdssFilter=None,
    annotationsFilter=None,
    qutsIndex=0):
    protocolHandles=ATOM_GET_PROTOCOLS_FOR_DEVICES(devicesHandles,qutsIndex)
    return ATOM_CREATE_DATA_FILTER_FOR_PROTOCOLS(protocolHandles,protocolRange,diagFilter,qmiFilter,adbFilter,saharaFilter,fastbootFilter,nmeaFilter,qdssFilter,annotationsFilter)

LAST_LEM_TEMPLATE={}
def ATOM_GET_LAST_LEM_TEMPLATE_FILE(deviceHandle, qutsIndex=0):
    keyname = "{}_{}".format(qutsIndex, deviceHandle)
    if(keyname in LAST_LEM_TEMPLATE):
        return LAST_LEM_TEMPLATE[keyname]
    return None

def ATOM_ENABLE_ALL_LEM(deviceHandle, enable, timeout, qutsIndex=0):
    binaryRetCfg=ATOM_CREATE_DIAG_RETURN_CONFIG(Common.ttypes.DiagReturnFlags.BINARY_PAYLOAD | Common.ttypes.DiagReturnFlags.PACKET_NAME | Common.ttypes.DiagReturnFlags.PACKET_ID | Common.ttypes.DiagReturnFlags.PACKET_TYPE | Common.ttypes.DiagReturnFlags.TIME_STAMP_STRING | Common.ttypes.DiagReturnFlags.RECEIVE_TIME_STRING)
    if(enable):
        #logging
        #'''
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, diagReturnConfig=binaryRetCfg, request=bytes(b'\x73\x00\x00\x00\x01\x00\x00\x00'), timeout=timeout, qutsIndex=qutsIndex)
        binary=response[0].binaryPayload[12:]
        if(len(binary)!=4*16):
            ATOM_ERROR("Invalid response for retrieve loggin ID")
        for i in range(0, 16):
            b=binary[(i*4):(i*4+4)]
            n=int.from_bytes(b,byteorder='little',signed=False)
            if(n!=0):
                numberMask=(n+7)//8
                hexstring="7300000003000000{I}{N1}{d:f<{N2}x}".format(I=ATOM_PARSE_HEX_BUFFER(ATOM_CONVER_NUMBER_TO_BYTES(i,4),""), N1=ATOM_PARSE_HEX_BUFFER(ATOM_CONVER_NUMBER_TO_BYTES(n,4),""), d=15, N2=(numberMask*2))
                binaryMask=ATOM_CONVER_HEX_BUFFER(hexstring)
                response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=binaryMask, timeout=timeout, qutsIndex=qutsIndex)
        #'''
        #event
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, diagReturnConfig=binaryRetCfg, request=bytes(b'\x81\x00\x00\x00'), timeout=timeout, qutsIndex=qutsIndex)
        b=response[0].binaryPayload[4:6]
        n=int.from_bytes(b,byteorder='little',signed=False)
        numberMask=n//8+1
        hexstring="82000000{N1}{d:f<{N2}x}".format(N1=ATOM_PARSE_HEX_BUFFER(ATOM_CONVER_NUMBER_TO_BYTES(n, 2),""), d=15, N2=(numberMask*2))
        binaryMask=ATOM_CONVER_HEX_BUFFER(hexstring)
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=binaryMask, timeout=timeout, qutsIndex=qutsIndex)

        #message
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=bytes(b'\x7D\x05\x00\x00\xff\xff\xff\xff'), timeout=timeout, qutsIndex=qutsIndex)
    else:
        #logging
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=bytes(b'\x73\x00\x00\x00\x00\x00\x00\x00'), timeout=timeout, qutsIndex=qutsIndex)
        #event
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, diagReturnConfig=binaryRetCfg, request=bytes(b'\x81\x00\x00\x00'), timeout=timeout, qutsIndex=qutsIndex)
        b=response[0].binaryPayload[4:6]
        n=int.from_bytes(b,byteorder='little',signed=False)
        numberMask=n//8+1
        hexstring="82000000{N1}{d:0<{N2}x}".format(N1=ATOM_PARSE_HEX_BUFFER(ATOM_CONVER_NUMBER_TO_BYTES(n,2),""), d=0, N2=(numberMask*2))
        binaryMask=ATOM_CONVER_HEX_BUFFER(hexstring)
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=binaryMask, timeout=timeout, qutsIndex=qutsIndex)
        #message
        response=ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=bytes(b'\x7D\x05\x00\x00\x00\x00\x00\x00'), timeout=timeout, qutsIndex=qutsIndex)

def ATOM_CREATE_LEM_TEMPLATE_FOR_DEVICES(deviceHandle, interval, sampleThreshold, timeout=10000, qutsIndex=0):
    qutsprefix = "QutsClient_{}".format(qutsIndex)
    ATOM_LOG(qutsprefix, "Disable all sub system")
    Atom_DeviceManager.getDeviceBuildId(deviceHandle, qutsIndex)
    #ATOM_SEND_RAW_DIAG_REQUEST(deviceHandle=deviceHandle, request=bytes(b'\x0c'), qutsIndex=qutsIndex)
    #time.sleep(2)#sleep 2s for message stop
    ATOM_LOG(qutsprefix, "Disable all sub system")
    ATOM_ENABLE_ALL_LEM(deviceHandle, False, timeout, qutsIndex)

    time.sleep(5)#sleep 10s for message stop

    ATOM_LOG(qutsprefix, "Start Logging")
    Atom_DeviceManager.startLogging(qutsIndex)

    ATOM_LOG(qutsprefix, "Enable all sub system")
    ATOM_ENABLE_ALL_LEM(deviceHandle, True, timeout, qutsIndex)

    time.sleep(interval)
    ATOM_LOG(qutsprefix, "Disable all sub system")
    ATOM_ENABLE_ALL_LEM(deviceHandle, False, timeout, qutsIndex)

    path=os.getcwd()
    ATOM_LOG(qutsprefix, "Save file to ", path)
    hdflist=[]
    hdflist=Atom_DeviceManager.saveLogFiles(path, qutsIndex)
    if(len(hdflist)==0):
        ATOM_ERROR(qutsprefix, "Save HDF file failed")
        return None
    ATOM_LOG(qutsprefix, "HDF path:", hdflist)
    global LAST_LEM_TEMPLATE
    LAST_LEM_TEMPLATE["{}_{}".format(qutsIndex, deviceHandle)]=hdflist

    lemTemplatePackets=[]
    for hdf in hdflist:
        if(os.path.exists(hdf)==False):
            ATOM_ERROR(qutsprefix, "HDF file not saved")
            return None
        else:
            ATOM_LOG(qutsprefix, "Get data from HDF Start")
            protocolHandles=ATOM_GET_PROTOCOLS_FOR_DEVICES([deviceHandle], [Common.ttypes.ProtocolType.PROT_DIAG], qutsIndex)
            mainResult = ATOM_LOAD_DATA_FROM_FILE(hdf, protocolHandles, qutsIndex=qutsIndex)
            ATOM_LOG(qutsprefix, "Get data from HDF Done")
            if(mainResult):
                lemFilters={}
                lemCategoryResult={}
                for i in range(len(mainResult)):
                    packet=ATOM_PARSE_PACKET(mainResult[i])
                    if(isinstance(packet, Common.ttypes.DiagPacket)):
                        ATOM_DEBUG(qutsprefix, "Diag Packet", i, Common.ttypes.DiagPacketType._VALUES_TO_NAMES[packet.packetType], packet.packetId, packet.receiveTimeString, packet.packetName)
                        if(packet.packetType==Common.ttypes.DiagPacketType.DEBUG_MSG or
                        packet.packetType==Common.ttypes.DiagPacketType.LOG_PACKET or
                        packet.packetType==Common.ttypes.DiagPacketType.EVENT):
                            lemtemp=TemplateLEM(packet.packetType, packet.packetId)
                            if(lemtemp in lemCategoryResult):
                                lemCategoryResult[lemtemp]+=1
                            else:
                                lemCategoryResult[lemtemp]=1
                    elif(isinstance(packet, Common.ttypes.AnnotationPacket)):
                        ATOM_DEBUG(qutsprefix, "Annotation Packet", i, packet)
                for lemtemp in lemCategoryResult:
                    if(lemCategoryResult[lemtemp]>=sampleThreshold):
                        ATOM_LOG(qutsprefix, "Find a valid LEM:", Common.ttypes.DiagPacketType._VALUES_TO_NAMES[lemtemp.PacketType], lemtemp.PacketId)
                        if(lemtemp.PacketType not in lemFilters):
                            lemFilters[lemtemp.PacketType]=[]
                        lemFilters[lemtemp.PacketType].append(lemtemp.PacketId)
                
                if(lemFilters):
                    dataPacketFilter=ATOM_CREATE_DATA_FILTER_FOR_PROTOCOLS(protocolHandles, None, ATOM_CREATE_DIAG_FILTER(lemFilters))
                    ATOM_LOG(qutsprefix, "Load Filter Data From File")
                    lemTemplatePackets = ATOM_LOAD_FILTERED_DATA_FROM_FILE(hdf, dataPacketFilter, qutsIndex=qutsIndex)

    return lemTemplatePackets