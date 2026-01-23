# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import sys
import time
import logging
import ctypes
import os
import random
import re
import traceback
from flags import global_info
from datetime import datetime
import platform
QUTS_path = ''
if platform.system().startswith("Windows"):
    if os.path.exists(r"C:\Program Files (x86)\Qualcomm\QUTS\Support\python"):
        sys.path.append(r"C:\Program Files (x86)\Qualcomm\QUTS\Support\python")
        QUTS_path = r"C:\Program Files (x86)\Qualcomm\QUTS\Support\python"
    else:
        sys.path.append(r"C:\Program Files\Qualcomm\QUTS\Support\python")
        QUTS_path = r"C:\Program Files\Qualcomm\QUTS\Support\python"
elif platform.system().startswith("Linux"):
    sys.path.append(r"/opt/qcom/QUTS/Support/python")
    QUTS_path = r"/opt/qcom/QUTS/Support/python"
elif platform.system().startswith("Darwin"):
    sys.path.append(r"/Applications/Qualcomm/QUTS/QUTS.app/Contents/Support/python")
    QUTS_path = r"/Applications/Qualcomm/QUTS/QUTS.app/Contents/Support/python"
    pass
else:
    pass

if os.path.exists(QUTS_path):
  import Common.ttypes
  import LogSession.ttypes

class ATOM_PRINT_TYPE(object):
    ERROR=-1
    INFO=0
    WARNING=1
    DEBUG=2

os.makedirs(global_info["log"], mode=0o777, exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)
logging.Formatter.converter = time.gmtime
fh = logging.FileHandler(os.path.join(global_info["log"],'output.txt'), mode='w')
formatter=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
formatter.converter=time.gmtime
fh.setFormatter(formatter)
fh.setLevel(logging.NOTSET)
#co = logging.StreamHandler()
logger.addHandler(fh)
#logger.addHandler(co)


DEBUG_ENABLED=False
def ATOM_ENABLE_DEBUG(enabled=True):
    global DEBUG_ENABLED
    DEBUG_ENABLED=enabled
def ATOM_LOG(*logs):
    ATOM_PRINT(ATOM_PRINT_TYPE.INFO, *logs)
def ATOM_WARNING(*logs):
    ATOM_PRINT(ATOM_PRINT_TYPE.WARNING, *logs)
def ATOM_ERROR(*logs):
    ATOM_PRINT(ATOM_PRINT_TYPE.ERROR, *logs)
def ATOM_DEBUG(*logs):
    ATOM_PRINT(ATOM_PRINT_TYPE.DEBUG, *logs)

def ATOM_PRINT(logtype, *logs):
    global DEBUG_ENABLED
    try:
        i=0
        line=""
        for log in logs:
            if(i!=0):
                line+=" "
            line+="{}".format(log)
            i+=1
        
        if(logtype==ATOM_PRINT_TYPE.ERROR):
            logger.error(line)
        elif(logtype==ATOM_PRINT_TYPE.WARNING):
            logger.warning(line)
        elif(logtype==ATOM_PRINT_TYPE.DEBUG):
            if(DEBUG_ENABLED):
                logger.debug(line)
                
        else:
            logger.info(line)
    except Exception as e:
        logger.error("Exception at ATOM_RPINT")
        logger.error(traceback.format_exc())

def ATOM_GET_PARAMETER(paramName, defaultVal, paramlist):
    try:
        paramVal = type(defaultVal)((paramlist[paramName.lower()]))
    except Exception as e:
        ATOM_WARNING(e)
        ATOM_WARNING("Use default value:", defaultVal)
        paramVal=defaultVal
    finally:
        return paramVal

def ATOM_IS_ADMIN():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ATOM_RUN_ELVATED(cmd, param):
    ATOM_DEBUG("Run shell command")
    verbopen="open"
    verbrunas="runas"
    processname= cmd
    processparam= param

    if(sys.version_info[0]!=3):
        verbopen=unicode(verbopen)
        verbrunas=unicode(verbrunas)
        processname=unicode(processname)
        processparam=unicode(processparam)

    ATOM_DEBUG("CMD:", sys.executable)
    ATOM_DEBUG("ARG:", processparam)
    
    try:
        exechandle=ctypes.windll.shell32.ShellExecuteW(None, verbrunas, processname, processparam, None, 2)
        return exechandle>0
    except Exception as e:
        ATOM_ERROR(traceback.format_exc())
        return False

def ATOM_REMOVE_FILE(path, requestAdmin=False, timeoutInSec=5):
    if(requestAdmin and ATOM_IS_ADMIN()==False):
        ATOM_RUN_ELVATED("rm", path)
        waittime=0
        while waittime<timeoutInSec:
            if(os.path.exists(path)):
                ATOM_DEBUG("Remove Ongoing")
                time.sleep(1)
                waittime+=1
            else:
                ATOM_DEBUG("Remove Finished")
                return                
        ATOM_ERROR("Remove Timeout")
    else:
        os.remove(path)

#Utility
#convert bytes to hex string
def ATOM_PARSE_HEX_BUFFER(hexbuff, spliter=" ", digitOnly=True):
    if(sys.version_info.major==3):
        if(digitOnly):
            hexin=['%02X' % ord(chr(n)) for n in hexbuff]
        else:
            hexin=['0x%02X' % ord(chr(n)) for n in hexbuff]
    else:
        if(digitOnly):
            hexin=['%02X' % ord(n) for n in hexbuff]
        else:
            hexin=['0x%02X' % ord(n) for n in hexbuff]
    hexstring = spliter.join(hexin)
    return hexstring

#convert hex string to bytes
def ATOM_CONVER_HEX_BUFFER(hexstring):
    if(sys.version_info.major==3):
        return bytes.fromhex(hexstring)
    else:
        return hexstring.decode('hex')

#convert number to bytes
def ATOM_CONVER_NUMBER_TO_BYTES(value, length, reversed=False):
    result = []
    for i in range(0, length):
        result.append(value >> (i * 8) & 0xff)
    if(reversed):
        result.reverse()
    result_bytes=bytes(result)
    return result_bytes


#return config
def ATOM_CREATE_DIAG_RETURN_CONFIG(flags=None):
    diagReturnConfig = Common.ttypes.DiagReturnConfig()
    if(flags==None or flags==''):
        diagReturnConfig.flags = Common.ttypes.DiagReturnFlags.BINARY_PAYLOAD |Common.ttypes.DiagReturnFlags.PARSED_TEXT | Common.ttypes.DiagReturnFlags.PACKET_NAME | Common.ttypes.DiagReturnFlags.PACKET_ID | Common.ttypes.DiagReturnFlags.PACKET_TYPE | Common.ttypes.DiagReturnFlags.TIME_STAMP_STRING | Common.ttypes.DiagReturnFlags.RECEIVE_TIME_STRING | Common.ttypes.DiagReturnFlags.SUMMARY_TEXT
    else:
        diagReturnConfig.flags = flags
    return diagReturnConfig

def ATOM_CREATE_ADB_RETURN_CONFIG(flags=None):
    adbReturnConfig = Common.ttypes.AdbReturnConfig()
    if(flags==None or flags==''):
        adbReturnConfig.flags = Common.ttypes.AdbReturnFlags.RECEIVE_TIME_STRING | Common.ttypes.AdbReturnFlags.PACKET_TEXT
    else:
        adbReturnConfig.flags = flags
    return adbReturnConfig

def ATOM_CREATE_DATA_RETURN_CONFIG_FOR_PROTOCOL_TYPES(protocolTypes,
    diagConfig=ATOM_CREATE_DIAG_RETURN_CONFIG(),
    qmiConfig=None,
    adbConfig=None,
    saharaConfig=None,
    fastbootConfig=None,
    nmeaConfig=None,
    qdssConfig=None,
    adplConfig=None):
    dataReturnConfig=LogSession.ttypes.PacketReturnConfig()
    for protocolType in protocolTypes:
        if(protocolType==Common.ttypes.ProtocolType.PROT_DIAG and dataReturnConfig.diagConfig==None):
            dataReturnConfig.diagConfig=diagConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_QMI and dataReturnConfig.qmiConfig==None):
            dataReturnConfig.qmiConfig=qmiConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_ADB and dataReturnConfig.adbConfig==None):
            dataReturnConfig.adbConfig=adbConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_SAHARA and dataReturnConfig.saharaConfig==None):
            dataReturnConfig.saharaConfig=saharaConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_FASTBOOT and dataReturnConfig.fastbootConfig==None):
            dataReturnConfig.fastbootConfig=fastbootConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_NMEA and dataReturnConfig.nmeaConfig==None):
            dataReturnConfig.nmeaConfig=nmeaConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_QDSS and dataReturnConfig.qdssConfig==None):
            dataReturnConfig.qdssConfig=qdssConfig
        if(protocolType==Common.ttypes.ProtocolType.PROT_ADPL and dataReturnConfig.adplConfig==None):
            dataReturnConfig.adplConfig=adplConfig
    return dataReturnConfig
    
def ATOM_CREATE_DATA_RETURN_CONFIG_FOR_PROTOCOLS(protocols,
    diagConfig=ATOM_CREATE_DIAG_RETURN_CONFIG(),
    qmiConfig=None,
    adbConfig=None,
    saharaConfig=None,
    fastbootConfig=None,
    nmeaConfig=None,
    qdssConfig=None,
    adplConfig=None):
    dataReturnConfig=LogSession.ttypes.PacketReturnConfig()
    for protocol in protocols:
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_DIAG and dataReturnConfig.diagConfig==None):
            dataReturnConfig.diagConfig=diagConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_QMI and dataReturnConfig.qmiConfig==None):
            dataReturnConfig.qmiConfig=qmiConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_ADB and dataReturnConfig.adbConfig==None):
            dataReturnConfig.adbConfig=adbConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_SAHARA and dataReturnConfig.saharaConfig==None):
            dataReturnConfig.saharaConfig=saharaConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_FASTBOOT and dataReturnConfig.fastbootConfig==None):
            dataReturnConfig.fastbootConfig=fastbootConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_NMEA and dataReturnConfig.nmeaConfig==None):
            dataReturnConfig.nmeaConfig=nmeaConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_QDSS and dataReturnConfig.qdssConfig==None):
            dataReturnConfig.qdssConfig=qdssConfig
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_ADPL and dataReturnConfig.adplConfig==None):
            dataReturnConfig.adplConfig=adplConfig
    return dataReturnConfig


#devic\protocol handles
def ATOM_CREATE_PROTOCOLS_HANDLE_LIST_FOR_PROTOCOLS(protocols):
    protocolHandles=[]
    for protocol in protocols:
        protocolHandles.append(protocol.protocolHandle)
    return protocolHandles

def ATOM_CREATE_PROTOCOL_TYPE_LIST_FROM_FILTER(dataPacketFilter):
    protocolTypes=[]
    if(dataPacketFilter.diagFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_DIAG)
    if(dataPacketFilter.qmiFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_QMI)
    if(dataPacketFilter.adbFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_ADB)
    if(dataPacketFilter.saharaFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_SAHARA)
    if(dataPacketFilter.fastbootFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_FASTBOOT)
    if(dataPacketFilter.nmeaFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_NMEA)
    if(dataPacketFilter.qdssFilter!=None):
        protocolTypes.append(Common.ttypes.ProtocolType.PROT_QDSS)
    return protocolTypes

#data filters
def ATOM_APPEND_A_DIAG_FILTER_BY_REGEX(regexStrings, packetType, diagPacketFilterOrg=None):
    if(not diagPacketFilterOrg):
        diagPacketFilter=Common.ttypes.DiagPacketFilter()
    else:
        diagPacketFilter=diagPacketFilterOrg
    if(diagPacketFilter.idOrNameMask==None):
        diagPacketFilter.idOrNameMask={}

    for regexString in regexStrings:
        diagFilterItem = Common.ttypes.DiagIdFilterItem(regexFilter=regexString)
        if(not diagPacketFilter.idOrNameMask):
            diagPacketFilter.idOrNameMask[packetType]=[diagFilterItem]
            continue
        if(packetType not in diagPacketFilter.idOrNameMask):
            diagPacketFilter.idOrNameMask[packetType]=[diagFilterItem]
            continue
        if(diagFilterItem not in diagPacketFilter.idOrNameMask[packetType]):
            diagPacketFilter.idOrNameMask[packetType].append(diagFilterItem)
    return diagPacketFilter

def ATOM_APPEND_A_DIAG_FILTER_BY_ID_OR_NAME(packetIdOrNames, packetType, diagPacketFilterOrg):
    if(not diagPacketFilterOrg):
        diagPacketFilter=Common.ttypes.DiagPacketFilter()
    else:
        diagPacketFilter=diagPacketFilterOrg
    if(diagPacketFilter.idOrNameMask==None):
        diagPacketFilter.idOrNameMask={}

    for packetIdOrName in packetIdOrNames:
        diagFilterItem = Common.ttypes.DiagIdFilterItem(idOrName=packetIdOrName)
        
        if(not diagPacketFilter.idOrNameMask):
            diagPacketFilter.idOrNameMask[packetType]=[diagFilterItem]
            continue
        if(packetType not in diagPacketFilter.idOrNameMask):
            diagPacketFilter.idOrNameMask[packetType]=[diagFilterItem]
            continue
        if(diagFilterItem not in diagPacketFilter.idOrNameMask[packetType]):
            diagPacketFilter.idOrNameMask[packetType].append(diagFilterItem)
    return diagPacketFilter

def ATOM_CREATE_DIAG_FILTER(allFilters={}):
    if(not allFilters):
        #allFilters[Common.ttypes.DiagPacketType.RESPONSE] = ["125","124"]
        #allFilters[Common.ttypes.DiagPacketType.SUBSYS_REQUEST] =  ["50/6"]
        #allFilters[Common.ttypes.DiagPacketType.SUBSYS_RESPONSE] =  [ "75/9483"]
        ##QXDM and the saved Log files show 33/64005.
        #allFilters[Common.ttypes.DiagPacketType.SUBSYS_RESPONSE] =  ["18/2058", "11/37","18/93","75/9483"]
        allFilters[Common.ttypes.DiagPacketType.EVENT] = ["2803","2804"]
        allFilters[Common.ttypes.DiagPacketType.DEBUG_MSG] = ["0005/0002"]
        allFilters[Common.ttypes.DiagPacketType.RESPONSE] =  ["0", "1"]
        allFilters[Common.ttypes.DiagPacketType.SUBSYS_RESPONSE] =  ["50/3", "87/14"]
        allFilters[Common.ttypes.DiagPacketType.SUBSYSV2_IMMEDIATE_RESPONSE] =  ["33/60004"]
        allFilters[Common.ttypes.DiagPacketType.SUBSYSV2_DELAYED_RESPONSE] =  ["33/60004"]
    
    diagPacketFilter = None
    for packetType in allFilters:
        diagPacketFilter=ATOM_APPEND_A_DIAG_FILTER_BY_ID_OR_NAME(allFilters[packetType], packetType, diagPacketFilter)
    return diagPacketFilter

def ATOM_IS_DIAG_PACKET_IN_FILTER(diagPacket, diagPacketFilter):
    resu = False
    if(isinstance(diagPacket, Common.ttypes.DiagPacket)):
        if(not diagPacketFilter):
            return resu
        if(diagPacket.packetType in diagPacketFilter.idOrNameMask):
            j=0
            for singleDiagFilter in diagPacketFilter.idOrNameMask[diagPacket.packetType]:
                try:
                    j=0 #match index
                    if(diagPacket.packetId == singleDiagFilter.idOrName):
                        resu = True
                    j=1
                    if(diagPacket.packetName == singleDiagFilter.idOrName):
                        resu = True
                    j=2
                    if(diagPacket.parsedText!=None and singleDiagFilter.regexFilter!=None and re.search(singleDiagFilter.regexFilter, diagPacket.parsedText, flags=0)):
                        resu = True
                    j=3
                    if(diagPacket.summaryText!=None and singleDiagFilter.summaryRegexFilter!=None and re.search(singleDiagFilter.summaryRegexFilter, diagPacket.summaryText, flags=0)):
                        resu = True
                except Exception as e:
                    if(j==0):
                        ATOM_ERROR("Searching Error:\r\n", Common.ttypes.DiagPacketType._VALUES_TO_NAMES[diagPacket.packetType], "\r\n", diagPacket.packetId, "\r\nmatch exception with idOrName filter:\r\n", singleDiagFilter.idOrName)
                    elif(j==1):
                        ATOM_ERROR("Searching Error:\r\n", Common.ttypes.DiagPacketType._VALUES_TO_NAMES[diagPacket.packetType], "\r\n", diagPacket.packetName, "\r\nmatch exception with idOrName filter:\r\n", singleDiagFilter.idOrName)
                    elif(j==2):
                        ATOM_ERROR("Searching Error:\r\n", Common.ttypes.DiagPacketType._VALUES_TO_NAMES[diagPacket.packetType], "\r\n", diagPacket.parsedText, "\r\nmatch exception with regex filter:\r\n", singleDiagFilter.regexFilter)
                    elif(j==3):
                        ATOM_ERROR("Searching Error:\r\n", Common.ttypes.DiagPacketType._VALUES_TO_NAMES[diagPacket.packetType], "\r\n", diagPacket.summaryText, "\r\nmatch exception with summaryRegex filter:\r\n", singleDiagFilter.summaryRegexFilter)
                    ATOM_ERROR("RE Exception:", repr(e))
    return resu

def ATOM_FILTER_DIAG_PACKETS(diagPackets, diagPacketFilter):
    diagPacketsFiltered=[]
    for diagPacket in diagPackets:
        if(isinstance(diagPacket, Common.ttypes.DiagPacket)):
            if(ATOM_IS_DIAG_PACKET_IN_FILTER(diagPacket, diagPacketFilter)):
                diagPacketsFiltered.append(diagPacket)
    return diagPacketsFiltered

class ATOM_DIAG_FILTER_OPTION(object):
    ID=1
    NAME=2
    REGEX=4
    SUMMARYREGEX=8
    ALL=15

class TemplateDiagFilter(object):
    def __init__(self, filtertype, filterstring):
        self.filterType=filtertype
        self.filterString=filterstring

    def __hash__(self):
        return 0
    
    def __eq__(self, other):
        if(isinstance(other, TemplateLEM)):
            if(other.filterType != self.filterType):
                return False
            if(other.filterString != self.filterString):
                return False
            return True
        else:
            return NotImplemented

def ATOM_CREATE_RANDOM_DIAG_FILTER_FROM_PACKETS(packets, maxcount=0, option=ATOM_DIAG_FILTER_OPTION.ALL):
    diagPacketFilter=Common.ttypes.DiagPacketFilter()
    #Get all the different packet in packets
    dataPacketsGroupByIdOrName={}
    dataPacketsGroupByRegex={}
    for datapacket in packets:
        packet=ATOM_PARSE_PACKET(datapacket)
        if(isinstance(packet, Common.ttypes.DiagPacket)):
            if(option&ATOM_DIAG_FILTER_OPTION.ID!=0):
                if(packet.packetType!=None and packet.packetId!=None):
                    if(packet.packetType not in dataPacketsGroupByIdOrName):
                        dataPacketsGroupByIdOrName[packet.packetType]=[]
                        dataPacketsGroupByIdOrName[packet.packetType].append(packet.packetId)
                    elif(packet.packetId not in dataPacketsGroupByIdOrName[packet.packetType]):
                        dataPacketsGroupByIdOrName[packet.packetType].append(packet.packetId)

            if(option&ATOM_DIAG_FILTER_OPTION.NAME!=0):
                if(packet.packetType!=None and packet.packetName!=None):
                    if(packet.packetType not in dataPacketsGroupByIdOrName):
                        dataPacketsGroupByIdOrName[packet.packetType]=[]
                        dataPacketsGroupByIdOrName[packet.packetType].append(packet.packetName)
                    elif(packet.packetName not in dataPacketsGroupByIdOrName[packet.packetType]):
                        dataPacketsGroupByIdOrName[packet.packetType].append(packet.packetName)
            
            if(option&ATOM_DIAG_FILTER_OPTION.REGEX!=0):
                if(packet.packetType!=None and packet.parsedText!=None):
                    randomstart=random.randint(0,len(packet.parsedText)-1)
                    randomend=random.randint(randomstart+1,len(packet.parsedText))
                    randomRegex=packet.parsedText[randomstart:randomend]
                    randomRegex=".*"+randomRegex+"?"
                    try:
                        re.compile(randomRegex)
                        if(packet.packetType not in dataPacketsGroupByRegex):
                            dataPacketsGroupByRegex[packet.packetType]=[]
                            dataPacketsGroupByRegex[packet.packetType].append(randomRegex)
                        elif(packet.packetName not in dataPacketsGroupByRegex[packet.packetType]):
                            dataPacketsGroupByRegex[packet.packetType].append(randomRegex)
                    except Exception as e:
                        ATOM_DEBUG("Ignore Invalid Regex:{}".format(randomRegex))

    if(dataPacketsGroupByIdOrName):
        for idx in range(0, maxcount):
            assignType=random.choice(list(dataPacketsGroupByIdOrName.keys()))
            if(len(dataPacketsGroupByIdOrName[assignType])>0):
                packetId=random.choice(dataPacketsGroupByIdOrName[assignType])
                diagPacketFilter=ATOM_APPEND_A_DIAG_FILTER_BY_ID_OR_NAME([packetId], assignType, diagPacketFilter)
                dataPacketsGroupByIdOrName[assignType].remove(packetId)
            else:
                ATOM_ERROR("A unknown error")#never comes here
            if(len(dataPacketsGroupByIdOrName[assignType])==0):
                del dataPacketsGroupByIdOrName[assignType]
    
    if(dataPacketsGroupByRegex):
        for idx in range(0, maxcount):
            assignType=random.choice(list(dataPacketsGroupByRegex.keys()))
            if(len(dataPacketsGroupByRegex[assignType])>0):
                packetRegex=random.choice(dataPacketsGroupByRegex[assignType])
                diagPacketFilter=ATOM_APPEND_A_DIAG_FILTER_BY_REGEX([packetRegex], assignType, diagPacketFilter)
                dataPacketsGroupByRegex[assignType].remove(packetRegex)
            else:
                ATOM_ERROR("A unknown error")#never comes here
            if(len(dataPacketsGroupByRegex[assignType])==0):
                del dataPacketsGroupByRegex[assignType]

    return diagPacketFilter

def ATOM_CREATE_DATA_FILTER_FOR_PROTOCOLS(protocols, 
    protocolRange,
    diagFilter=ATOM_CREATE_DIAG_FILTER(),
    qmiFilter=None,
    adbFilter=None,
    saharaFilter=None,
    fastbootFilter=None,
    nmeaFilter=None,
    qdssFilter=None,
    annotationsFilter=None):
    dataPacketFilter = LogSession.ttypes.DataPacketFilter()
    protocolHandles=ATOM_CREATE_PROTOCOLS_HANDLE_LIST_FOR_PROTOCOLS(protocols)
    for protocol in protocols:
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_DIAG and dataPacketFilter.diagFilter==None):
            dataPacketFilter.diagFilter=diagFilter
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_QMI and dataPacketFilter.qmiFilter==None):
            dataPacketFilter.qmiFilter=qmiFilter
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_ADB and dataPacketFilter.adbFilter==None):
            dataPacketFilter.adbFilter=adbFilter
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_SAHARA and dataPacketFilter.saharaFilter==None):
            dataPacketFilter.saharaFilter=saharaFilter
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_FASTBOOT and dataPacketFilter.fastbootFilter==None):
            dataPacketFilter.fastbootFilter=fastbootFilter
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_NMEA and dataPacketFilter.nmeaFilter==None):
            dataPacketFilter.nmeaFilter=nmeaFilter
        if(protocol.protocolType==Common.ttypes.ProtocolType.PROT_QDSS and dataPacketFilter.qdssFilter==None):
            dataPacketFilter.qdssFilter=qdssFilter
    if(annotationsFilter):
        dataPacketFilter.annotationsFilter=annotationsFilter
    
    dataPacketFilter.protocolHandleList=protocolHandles
    
    if(protocolRange or protocolRange==None):
        dataPacketFilter.protocolRange=protocolRange
    return dataPacketFilter

def ATOM_IS_DATA_PACKET_IN_FILTER(dataPacket, dataPacketFilter):
    if(isinstance(ATOM_PARSE_PACKET(dataPacket), Common.ttypes.DiagPacket)):
        return ATOM_IS_DIAG_PACKET_IN_FILTER(ATOM_PARSE_PACKET(dataPacket), dataPacketFilter.diagFilter)
    ATOM_ERROR("Not implemented")
    return False

#diag template
#log\message\event template
class TemplateLEM(object):
    def __init__(self, packetType, packetId):
        self.PacketType=packetType
        self.PacketId=packetId
    
    def __hash__(self):
        return 0
    
    def __eq__(self, other):
        if(isinstance(other, TemplateLEM)):
            if(other.PacketType != self.PacketType):
                return False
            if(other.PacketId != self.PacketId):
                return False
            return True
        else:
            return NotImplemented

def ATOM_GET_RANDOM_LEM_TEMPLATE(tryCount, lemTemplate):
    if(not lemTemplate):
        ATOM_ERROR("Invalid LEM template")
        return None

    lemTypeNum=3
    lemCount={} #0-log;1-event;2-message
    lemType=[]
    lemType.append(Common.ttypes.DiagPacketType.LOG_PACKET)
    lemType.append(Common.ttypes.DiagPacketType.EVENT)
    lemType.append(Common.ttypes.DiagPacketType.DEBUG_MSG)
    totalCount=0
    for j in range(0,lemTypeNum):
        if(lemType[j] in lemTemplate):
            count=len(lemTemplate[lemType[j]])
            lemCount[lemType[j]]=count
            totalCount+=count

    if(tryCount>totalCount):
        ATOM_ERROR("Request exceeded maximum number of LEM template")
        return None

    lemIndexArray={}
    for j in lemCount:
        lemIndexArray[j]={}
        for i in range(0, lemCount[j]):
            lemIndexArray[j][i]=lemTemplate[j][i]

    lemRandomTemplate=[]
    for idx in range(0,tryCount):
        assignType=random.choice(list(lemIndexArray.keys()))
        if(len(lemIndexArray[assignType])>0):
            rnd=random.choice(list(lemIndexArray[assignType].keys()))
            lemRandomTemplate.append(TemplateLEM(assignType, lemIndexArray[assignType][rnd]))
            del lemIndexArray[assignType][rnd]
        else:
            ATOM_ERROR("A unknown error")#never comes here
        if(len(lemIndexArray[assignType])==0):
            del lemIndexArray[assignType]

    return lemRandomTemplate

class TemplateRawDiagRequest(object):
    def __init__(self, request, isAsync):
        self.RawRequest=request
        self.IsAsync=isAsync

def ATOM_GET_RANDOM_RAW_DIAG_REQUEST_FROM_TEMPLATE(tryCount=1, addTemplate=False, requestTemplate={}):
    if(not requestTemplate):
        ATOM_DEBUG("Use default template")
        #Version
        #requestTemplate[bytes(b'\x00')]=False
        #ESN
        requestTemplate[bytes(b'\x01')]=False
        #WCDMA polling
        requestTemplate[bytes(b'\x4B\x04\x0E\x00')]=False
        #GSM polling
        #requestTemplate[bytes(b'\x4B\x08\x02\x00')]=False
        #TDS polling
        #requestTemplate[bytes(b'\x4B\x57\x0E\x00')]=False
        #DIAG polling
        #requestTemplate[bytes(b'\x4B\x32\x03\x00')]=False
        #UIMDIAG_SIMLOCK_GET_STATUS_CMD command
        #requestTemplate[bytes(b'\x80\x21\x64\xEA')]=True
        #UIMDIAG_SIMLOCK_GET_CATEGORY_DATA_CMD command
        #requestTemplate[bytes(b'\x80\x21\x65\xea\x01\x00')]=True

    ATOM_DEBUG("Generate Random Data Sequence")
    randomRequest=[]

    if(addTemplate):
        #send each command in template
        for templ in requestTemplate:
            randomRequest.append(TemplateRawDiagRequest(templ, requestTemplate[templ]))

    for i in range(tryCount):
        rnd=random.choice(list(requestTemplate.keys()))
        randomRequest.append(TemplateRawDiagRequest(rnd, requestTemplate[rnd]))
    return randomRequest

#packet parser
def ATOM_PARSE_PACKET(packet):
    if(isinstance(packet, LogSession.ttypes.DataPacket)):
        if(packet.diagPacket != None):
            return packet.diagPacket
        elif(packet.qmiPacket != None):
            return packet.qmiPacket
        elif(packet.adbPacket != None):
            return packet.adbPacket
        elif(packet.saharaPacket != None):
            return packet.saharaPacket
        elif(packet.fastbootPacket != None):
            return packet.fastbootPacket
        elif(packet.adplPacket != None):
            return packet.adplPacket
        elif(packet.nmeaPacket != None):
            return packet.nmeaPacket
        elif(packet.annotationPacket != None):
            return packet.annotationPacket
        elif(packet.qdssPacket != None):
            return packet.qdssPacket
    return packet

def ATOM_GET_DIFF_PACKET_HEADER(org1, org2, timediff):
    packet1=ATOM_PARSE_PACKET(org1)
    packet2=ATOM_PARSE_PACKET(org2)
    #packet 1 always comes earlier
    if(type(packet1)!=type(packet2)):
        return True

    if(isinstance(packet1, Common.ttypes.DiagPacket)):
        if(packet1.packetId != packet2.packetId):
            return True
        if(timediff>=0):
            t1=ATOM_CONVERT_TIMESTAMP(packet1.receiveTimeString)
            t2=ATOM_CONVERT_TIMESTAMP(packet2.receiveTimeString)
            td=abs(t1-t2)
            if(td>timediff):
                return True
        #if comes here means id & time is match, then check if that is the same request response pair
        #then must be a time difference or packet id mismatch to distinguish
        for i in range(0,2):
            if(i==0):
                packChk=packet1
                packCmp=packet2
            else:
                packChk=packet2
                packCmp=packet1

            if(packChk.packetType==Common.ttypes.DiagPacketType.REQUEST and packCmp.packetType==Common.ttypes.DiagPacketType.RESPONSE):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYS_REQUEST and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYS_RESPONSE):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_REQUEST and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_IMMEDIATE_RESPONSE):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_REQUEST and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_DELAYED_RESPONSE):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_IMMEDIATE_RESPONSE and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_REQUEST):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_IMMEDIATE_RESPONSE and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_DELAYED_RESPONSE):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_DELAYED_RESPONSE and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_REQUEST):
                return False
            if(packChk.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_DELAYED_RESPONSE and packCmp.packetType==Common.ttypes.DiagPacketType.SUBSYSV2_IMMEDIATE_RESPONSE):
                return False
        return True
    elif(isinstance(packet1, Common.ttypes.AnnotationPacket)):
        if(packet1.parsedText != packet2.parsedText):
            return True
        if(packet1.messageId != packet2.messageId):
            return True
        if(timediff>=0):
            t1=ATOM_CONVERT_TIMESTAMP(packet1.receiveTimeString)
            t2=ATOM_CONVERT_TIMESTAMP(packet2.receiveTimeString)
            td=abs(t1-t2)
            if(td>timediff):
                return True
        return False
    else:
        return False

def ATOM_DIFF_PACKET(org1, org2, timediff):
    packet1=ATOM_PARSE_PACKET(org1)
    packet2=ATOM_PARSE_PACKET(org2)
    if(type(packet1)!=type(packet2)):
        return True

    if(isinstance(packet1, Common.ttypes.DiagPacket)):
        if(packet1.packetType!=packet2.packetType):
            return False
        if(packet1.packetId != packet2.packetId):
            return False
        if(timediff>=0):
            t1=ATOM_CONVERT_TIMESTAMP(packet1.receiveTimeString)
            t2=ATOM_CONVERT_TIMESTAMP(packet2.receiveTimeString)
            td=abs(t1-t2)
            ATOM_DEBUG("Time difference", td)
            if(td>timediff):
                ATOM_DEBUG("Time difference above range")
                return False
        return True
    elif(isinstance(packet1, Common.ttypes.AnnotationPacket)):
        if(packet1.parsedText != packet2.parsedText):
            return False
        if(packet1.messageId != packet2.messageId):
            return False
        if(timediff>=0):
            t1=ATOM_CONVERT_TIMESTAMP(packet1.receiveTimeString)
            t2=ATOM_CONVERT_TIMESTAMP(packet2.receiveTimeString)
            td=abs(t1-t2)
            if(td>timediff):
                return False
        return True
    else:
        return False

def ATOM_VALIDATE_PACKETS(packet1, packet2, timediff=0):
    ATOM_DEBUG("#find timestamp of first packet")
    t1=0
    for i in range(len(packet1)):
        ATOM_DEBUG("#packet1 index", i)
        if(isinstance(ATOM_PARSE_PACKET(packet1[i]), Common.ttypes.DiagPacket) or \
            isinstance(ATOM_PARSE_PACKET(packet1[i]), Common.ttypes.AnnotationPacket)):
            t1=ATOM_CONVERT_TIMESTAMP(ATOM_PARSE_PACKET(packet1[i]).receiveTimeString)
            ATOM_LOG("#packet1 start time", ATOM_PARSE_PACKET(packet1[i]).receiveTimeString, t1)
            break
    t2=0
    for i in range(len(packet2)):
        ATOM_DEBUG("#packet2 index", i)
        if(isinstance(ATOM_PARSE_PACKET(packet2[i]), Common.ttypes.DiagPacket) or \
            isinstance(ATOM_PARSE_PACKET(packet1[i]), Common.ttypes.AnnotationPacket)):
            t2=ATOM_CONVERT_TIMESTAMP(ATOM_PARSE_PACKET(packet2[i]).receiveTimeString)
            ATOM_LOG("#packet2 start time", ATOM_PARSE_PACKET(packet2[i]).receiveTimeString, t2)
            break
    
    packSample=[]
    packComp=[]

    samplpStr=""
    compStr=""
    if(t1<t2):
        ATOM_LOG("#set packet1 as sample")
        packSample=packet1
        samplpStr="packSample-packet1"
        packComp=packet2
        compStr="packComp-packet2"
    elif(t1==t2):
        if(len(packet1)>=len(packet2)):
            ATOM_LOG("#set packet1 as sample")
            packSample=packet1
            samplpStr="packSample-packet1"
            packComp=packet2
            compStr="packComp-packet2"
        else:
            ATOM_LOG("#set packet1 as sample")
            packSample=packet1
            samplpStr="packSample-packet1"
            packComp=packet2
            compStr="packComp-packet2"
    else:
        ATOM_LOG("#set packet2 as sample")
        packSample=packet2
        samplpStr="packSample-packet2"
        packComp=packet1
        compStr="packComp-packet1"

    lastj=0
    chkj=0
    validj=0
    interval=0
    ATOM_DEBUG("#find the first 2 packets in compare sequence with different id or time stamp")
    for j in range(0, len(packComp)):
        if(isinstance(ATOM_PARSE_PACKET(packComp[j]), Common.ttypes.AnnotationPacket) and ATOM_PARSE_PACKET(packComp[j]).parsedText=='END_LOG_FILE'):
            ATOM_ERROR("Find a compare EOF while looking for find header {}[{}]".format(compStr, j))
            return False
        elif(isinstance(ATOM_PARSE_PACKET(packComp[j]), Common.ttypes.DiagPacket) or \
            isinstance(ATOM_PARSE_PACKET(packComp[j]), Common.ttypes.AnnotationPacket)):
            validj+=1
            if(lastj!=j):
                if(ATOM_GET_DIFF_PACKET_HEADER(ATOM_PARSE_PACKET(packComp[j]), ATOM_PARSE_PACKET(packComp[lastj]), timediff)):
                    chkj=j
                    break
            lastj=j
        else:
            ATOM_DEBUG("Find a compare non supported packet while looking for find header {}[{}]".format(compStr, j))

    if(chkj==0):
        ATOM_ERROR("Fail to find a compare header")
        return False
    else:
        interval=chkj-lastj
        ATOM_LOG("Found compare header packets: {}[{}] and {}[{}]".format(compStr, lastj, compStr, chkj))
        packet=ATOM_PARSE_PACKET(packComp[lastj])
        ATOM_LOG("{}[{}]".format(compStr, lastj), Common.ttypes.DiagPacketType._VALUES_TO_NAMES[packet.packetType], packet.packetId, packet.receiveTimeString, packet.packetName)
        packet=ATOM_PARSE_PACKET(packComp[chkj])
        ATOM_LOG("{}[{}]".format(compStr, chkj), Common.ttypes.DiagPacketType._VALUES_TO_NAMES[packet.packetType], packet.packetId, packet.receiveTimeString, packet.packetName)

    si=0
    found=False
    skipi=0
    for i in range(0, len(packSample)):
        if(isinstance(ATOM_PARSE_PACKET(packSample[i]), Common.ttypes.AnnotationPacket) and ATOM_PARSE_PACKET(packSample[i]).parsedText=='END_LOG_FILE'):
            ATOM_ERROR("Find a sample EOF while looking for find header {}[{}]".format(samplpStr, i))
            return False
        elif(isinstance(ATOM_PARSE_PACKET(packSample[i]), Common.ttypes.DiagPacket) or \
            isinstance(ATOM_PARSE_PACKET(packSample[i]), Common.ttypes.DiagPacket)):
            ATOM_DEBUG("Compare {}[{}] to 1st packet {}[{}]".format(samplpStr, i, compStr, lastj))
            if(ATOM_DIFF_PACKET(ATOM_PARSE_PACKET(packSample[i]), ATOM_PARSE_PACKET(packComp[lastj]), timediff)):
                #found first match packet
                #try to find the 2nd packet match
                intervalpassed=0
                for j in range(i+1, len(packSample)):
                    if(isinstance(ATOM_PARSE_PACKET(packSample[j]), Common.ttypes.AnnotationPacket) and ATOM_PARSE_PACKET(packSample[j]).parsedText=='END_LOG_FILE'):
                        ATOM_ERROR("Find a sample EOF while looking for find header {}[{}]".format(samplpStr, i))
                        return False
                    elif(isinstance(ATOM_PARSE_PACKET(packSample[j]), Common.ttypes.DiagPacket) or \
                        isinstance(ATOM_PARSE_PACKET(packSample[j]), Common.ttypes.AnnotationPacket)):
                        intervalpassed+=1
                        if(intervalpassed<interval):
                            continue
                        ATOM_DEBUG("Compare {}[{}] to 2nd packet {}[{}]".format(samplpStr, j, compStr, chkj))
                        if(ATOM_DIFF_PACKET(ATOM_PARSE_PACKET(packSample[j]), ATOM_PARSE_PACKET(packComp[chkj]), timediff)):
                            #found 2nd match packet
                            backj=validj
                            backno=0
                            ATOM_DEBUG("roll back {} packets".format(backj))
                            for si in reversed(range(0, j+1)):
                                if(isinstance(ATOM_PARSE_PACKET(packSample[si]), Common.ttypes.AnnotationPacket) and ATOM_PARSE_PACKET(packSample[si]).parsedText=='END_LOG_FILE'):
                                    ATOM_ERROR("Find a sample EOF while looking for find header {}[{}]".format(samplpStr, i))
                                    return False
                                elif(isinstance(ATOM_PARSE_PACKET(packSample[si]), Common.ttypes.DiagPacket) or \
                                    isinstance(ATOM_PARSE_PACKET(packSample[si]), Common.ttypes.AnnotationPacket)):
                                    ATOM_DEBUG("roll back {}[{}]".format(samplpStr, si))
                                    backno+=1
                                    if(backno==backj):
                                        ATOM_DEBUG("roll back done")
                                        found=True
                                        break
                                else:
                                    ATOM_DEBUG("Find a sample non supported packet while looking for find header", "{}[{}]".format(samplpStr, i))

                            if(not found):
                                ATOM_ERROR("Roll back failed")
                            else:
                                ATOM_LOG("Decide same start packets {}[{}] and {}[0]".format(samplpStr, si, compStr))
                            break
                        else:
                            ATOM_DEBUG("{}[{}] mismatch with 2nd packet {}[{}]".format(samplpStr, j, compStr, chkj))
                            break
                    else:
                        ATOM_DEBUG("Find a sample non supported packet {}[{}]".format(compStr, j))
            else:
                ATOM_DEBUG("Not same start {}[{}] and {}[{}]".format(samplpStr, i, compStr, lastj))

            if(found):
                break
        else:
            ATOM_DEBUG("Find a sample non supported packet {}[{}]".format(compStr, j))

    if(not found):
        ATOM_ERROR("Can not found compare start packets")
        return False

    ATOM_DEBUG("#Start Compare")
    ci=0
    for i in range(si, len(packSample)):
        if(isinstance(ATOM_PARSE_PACKET(packSample[i]), Common.ttypes.AnnotationPacket)):
            ATOM_DEBUG("Find a sample annotation {}[{}]".format(samplpStr, i))
            break
        elif(isinstance(ATOM_PARSE_PACKET(packSample[i]), Common.ttypes.DiagPacket)):
            for j in range(ci, len(packComp)):
                if(isinstance(ATOM_PARSE_PACKET(packComp[j]), Common.ttypes.AnnotationPacket)):
                    ATOM_DEBUG("Find a compare annotation {}[{}], stop compare".format(compStr, j))
                    return True
                elif(isinstance(ATOM_PARSE_PACKET(packSample[i]), Common.ttypes.DiagPacket)):
                    ATOM_DEBUG("Compare {}[{}] to {}[{}]".format(samplpStr, i, compStr, j))
                    if(ATOM_DIFF_PACKET(ATOM_PARSE_PACKET(packSample[i]), ATOM_PARSE_PACKET(packComp[j]), timediff)==False):
                        ATOM_ERROR("{}[{}] mismatch with {}[{}]".format(samplpStr, i, compStr, j))
                        packet=ATOM_PARSE_PACKET(packSample[i])
                        ATOM_ERROR("{}[{}]".format(samplpStr, i), Common.ttypes.DiagPacketType._VALUES_TO_NAMES[packet.packetType], packet.packetId, packet.receiveTimeString, packet.packetName)
                        packet=ATOM_PARSE_PACKET(packComp[j])
                        ATOM_ERROR("{}[{}]".format(compStr, j), Common.ttypes.DiagPacketType._VALUES_TO_NAMES[packet.packetType], packet.packetId, packet.receiveTimeString, packet.packetName)
                        return False
                    else:
                        ci=j+1
                        break

            if ci == len(packComp):
                break
    return True

def ATOM_CONVERT_TIMESTAMP(packettimestring):
    timeStamp=0
    try:
        datetime_obj = datetime.strptime(packettimestring, "%Y/%m/%d %H:%M:%S.%f")
        timeStamp = int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
    except Exception as e:
        ATOM_ERROR(traceback.format_exc())
    return timeStamp
def ATOM_CONVERT_TIMESTRING(timestamp=0):
    endtime=timestamp
    if(timestamp==0):
        endtime=ATOM_GET_GMT_TIMESTAMP()
    dt = datetime.fromtimestamp(endtime / 1000, None)
    return dt.strftime("%Y/%m/%d %H:%M:%S.%f")
def ATOM_GET_GMT_TIMESTAMP():
    timeStamp = int(time.mktime(time.gmtime()) * 1000.0)
    return timeStamp

def ATOM_GET_DIAG_SUB_PACKETS(packetsOriginal, diagPacketFilter, starttime=0, endtime=None):
    packets=[]
    if(not packetsOriginal):
        return packets
    for packet in packetsOriginal:
        if(isinstance(ATOM_PARSE_PACKET(packet), Common.ttypes.DiagPacket)):
            timestamp=ATOM_CONVERT_TIMESTAMP(packet.receiveTimeString)
            if(timestamp>starttime and (endtime==None or timestamp<endtime)):
                if(ATOM_IS_DIAG_PACKET_IN_FILTER(packet, diagPacketFilter)):
                    packets.append(packet)
    return packets
