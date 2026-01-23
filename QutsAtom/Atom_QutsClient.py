# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from QutsAtom.Atom_AtomUtilityModule import *
from QutsAtom.Atom_QutsClient_init import QutsClientList
def qutsClientEnableMultiThreaded():
    ATOM_DEBUG("===", "Step into", sys._getframe().f_code.co_name)
    QutsClientList.enableQutsClientMultiThreaded()
    pass

def qutsClientEnableRemoteMachine(host):
    ATOM_DEBUG("===", "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(host, "argument-host:", type(host), host)
    QutsClientList.enableRemoteMachine(host)
    pass

def getQutsClient(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    clientObject=QutsClientList.getQutsClientObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(clientObject), clientObject)
    return clientObject!=None

def resetDataViewUpdateDoneEvent(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    evt=QutsClientList.ResetDataViewUpdateDoneEvent(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-evt:",  type(evt), evt)
    return evt


def signalHandler(sig, frame, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-sig:", type(sig), sig)
    ATOM_DEBUG(qutsIndex, "argument-frame:", type(frame), frame)
    QutsClientObject=QutsClientList.getQutsClientObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientObject), QutsClientObject)
    QutsClientObject.signalHandler(sig, frame)
    pass

def setOnDecryptionKeyStatusUpdateCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onDecryptionKeyStatusUpdateCallback=callback
    pass

def stop(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    QutsClientObject=QutsClientList.getQutsClientObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientObject), QutsClientObject)
    QutsClientObject.stop()
    pass

def clearCallbacks(qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    QutsClientObject=QutsClientList.getQutsClientObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientObject), QutsClientObject)
    QutsClientObject.clearCallbacks()
    pass

def setOnMessageCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onMessageCallback=callback
    pass

def setOnDeviceConnectedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onDeviceConnectedCallback=callback
    pass

def setOnDeviceDisconnectedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onDeviceDisconnectedCallback=callback
    pass

def setOnDeviceModeChangeCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onDeviceModeChangeCallback=callback
    pass

def setOnProtocolAddedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onProtocolAddedCallback=callback
    pass

def setOnProtocolRemovedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onProtocolRemovedCallback=callback
    pass

def setOnProtocolStateChangeCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onProtocolStateChangeCallback=callback
    pass

def setOnProtocolFlowControlStatusChangeCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onProtocolFlowControlStatusChangeCallback=callback
    pass

def setOnProtocolLockStatusChangeCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onProtocolLockStatusChangeCallback=callback
    pass

def setOnProtocolMbnDownloadStatusChangeCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onProtocolMbnDownloadStatusChangeCallback=callback
    pass

def setOnClientCloseRequestCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onClientCloseRequestCallback=callback
    pass

def setOnMissingQShrinkHashFileCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onMissingQShrinkHashFileCallback=callback
    pass

def setOnLogSessionMissingQShrinkHashFileCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onLogSessionMissingQShrinkHashFileCallback=callback
    pass

def setOnAsyncResponseCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onAsyncResponseCallback=callback
    pass

def setOnDataQueueUpdatedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onDataQueueUpdatedCallback=callback
    pass

def setOnDataViewUpdatedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onDataViewUpdatedCallback=callback
    pass

def setOnServiceAvailableCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onServiceAvailableCallback=callback
    pass

def setOnServiceEndedCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onServiceEndedCallback=callback
    pass

def setOnServiceEventCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onServiceEventCallback=callback
    pass

def setOnQShrinkStateUpdated(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onQShrinkStateUpdated=callback
    pass

def setOnLogSessionDecryptionKeyStatusUpdateCallback(callback, qutsIndex=0):
    ATOM_DEBUG("===", qutsIndex, "Step into", sys._getframe().f_code.co_name)
    ATOM_DEBUG(qutsIndex, "argument-callback:", type(callback), callback)
    QutsClientCallbackObject=QutsClientList.getQutsClientCallbackObject(qutsIndex)
    ATOM_DEBUG(qutsIndex, "output-obj:",  type(QutsClientCallbackObject), QutsClientCallbackObject)
    QutsClientCallbackObject.onLogSessionDecryptionKeyStatusUpdateCallback=callback
    pass

