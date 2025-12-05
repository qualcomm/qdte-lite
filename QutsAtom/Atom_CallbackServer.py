# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
import threading

class QutsClientCallbackObject:
    dataViewUpdateDoneEvent=threading.Event()
    onMessageCallback=None
    onDeviceConnectedCallback=None
    onDeviceDisconnectedCallback=None
    onDeviceModeChangeCallback=None
    onProtocolAddedCallback=None
    onProtocolRemovedCallback=None
    onProtocolStateChangeCallback=None
    onProtocolFlowControlStatusChangeCallback=None
    onProtocolLockStatusChangeCallback=None
    onProtocolMbnDownloadStatusChangeCallback=None
    onClientCloseRequestCallback=None
        
    onMissingQShrinkHashFileCallback=None
    onLogSessionMissingQShrinkHashFileCallback=None
    onAsyncResponseCallback=None
    onDataQueueUpdatedCallback=None
    onDataViewUpdatedCallback=None
    onServiceAvailableCallback=None
    onServiceEndedCallback=None
    onServiceEventCallback=None
    onQShrinkStateUpdatedCallback=None

    def __init__(self, client):
        client.setOnMessageCallback(self.onMessage)
        client.setOnDeviceConnectedCallback(self.onDeviceConnected)
        client.setOnDeviceDisconnectedCallback(self.onDeviceDisconnected)
        client.setOnDeviceModeChangeCallback(self.onDeviceModeChange)
        client.setOnProtocolAddedCallback(self.onProtocolAdded)
        client.setOnProtocolRemovedCallback(self.onProtocolRemoved)
        client.setOnProtocolStateChangeCallback(self.onProtocolStateChange)
        client.setOnProtocolFlowControlStatusChangeCallback(self.onProtocolFlowControlStatusChange)
        client.setOnProtocolLockStatusChangeCallback(self.onProtocolLockStatusChange)
        client.setOnProtocolMbnDownloadStatusChangeCallback(self.onProtocolMbnDownloadStatusChange)
        client.setOnClientCloseRequestCallback(self.onClientCloseRequest)
        
        client.setOnMissingQShrinkHashFileCallback(self.onMissingQShrinkHashFile)
        client.setOnLogSessionMissingQShrinkHashFileCallback(self.onLogSessionMissingQShrinkHashFile)
        client.setOnAsyncResponseCallback(self.onAsyncResponse)
        client.setOnDataQueueUpdatedCallback(self.onDataQueueUpdated)
        client.setOnDataViewUpdatedCallback(self.onDataViewUpdated)
        client.setOnServiceAvailableCallback(self.onServiceAvailable)
        client.setOnServiceEndedCallback(self.onServiceEnded)
        client.setOnServiceEventCallback(self.onServiceEvent)
        client.setOnQShrinkStateUpdated(self.onQShrinkStateUpdated)
        pass
    
    #on callback
    def onMessage(self, level, location, title, description):
        if(self.onMessageCallback):
            self.onMessageCallback(level, location, title, description)

    def onDeviceConnected(self, deviceInfo):
        if(self.onDeviceConnectedCallback):
            self.onDeviceConnectedCallback(deviceInfo)

    def onDeviceDisconnected(self, deviceInfo):
        if(self.onDeviceDisconnectedCallback):
            self.onDeviceDisconnectedCallback(deviceInfo)

    def onDeviceModeChange(self, deviceHandle, newMode):
        if(self.onDeviceModeChangeCallback):
            self.onDeviceModeChangeCallback(deviceHandle, newMode)

    def onProtocolAdded(self, deviceInfo, protocolInfo):
        if(self.onProtocolAddedCallback):
            self.onProtocolAddedCallback(deviceInfo, protocolInfo)

    def onProtocolRemoved(self, deviceInfo, protocolInfo):
        if(self.onProtocolRemovedCallback):
            self.onProtocolRemovedCallback(deviceInfo, protocolInfo)

    def onProtocolStateChange(self, protocolHandle, newState):
        if(self.onProtocolStateChangeCallback):
            self.onProtocolStateChangeCallback(protocolHandle, newState)
            
    def onProtocolFlowControlStatusChange(self, protocolHandle, dir, newStatus):
        if(self.onProtocolFlowControlStatusChangeCallback):
            self.onProtocolFlowControlStatusChangeCallback(protocolHandle, dir, newStatus)
    
    def onProtocolLockStatusChange(self, protocolHandle, newStatus):
    	if(self.onProtocolLockStatusChangeCallback):
            self.onProtocolLockStatusChangeCallback(protocolHandle, newStatus)
    
    def onProtocolMbnDownloadStatusChange(self, protocolHandle, newStatus):
        if(self.onProtocolMbnDownloadStatusChangeCallback):
            self.onProtocolMbnDownloadStatusChangeCallback(protocolHandle, newStatus)

    def onClientCloseRequest(self, closeReason):
        if(self.onClientCloseRequestCallback):
            self.onClientCloseRequestCallback(closeReason)
   	
    def onMissingQShrinkHashFile(self, protocolHandle, missingFileGuid):
        if(self.onMissingQShrinkHashFileCallback):
            self.onMissingQShrinkHashFileCallback(protocolHandle, missingFileGuid)
            
    def onLogSessionMissingQShrinkHashFile(self, logSessionInstance, protocolHandle, missingFileGuid):
        if(self.onLogSessionMissingQShrinkHashFileCallback):
            self.onLogSessionMissingQShrinkHashFileCallback(logSessionInstance, protocolHandle, missingFileGuid)

    def onAsyncResponse(self, protocolHandle, transactionId):
        if(self.onAsyncResponseCallback):
            self.onAsyncResponseCallback(protocolHandle, transactionId)

    def onDataQueueUpdated(self, queueName, queueSize):
        if(self.onDataQueueUpdatedCallback):
            self.onDataQueueUpdatedCallback(queueName, queueSize)

    def onDataViewUpdated(self, viewName, viewSize, finished):
        if(finished==True):
            self.dataViewUpdateDoneEvent.set()
        if(self.onDataViewUpdatedCallback):
            self.onDataViewUpdatedCallback(viewName, viewSize, finished)

    def onServiceAvailable(self, serviceName, deviceHandle):
        if(self.onServiceAvailableCallback):
            self.onServiceAvailableCallback(serviceName, deviceHandle)

    def onServiceEnded(self, serviceName, deviceHandle):
        if(self.onServiceEndedCallback):
            self.onServiceEndedCallback(serviceName, deviceHandle)

    def onServiceEvent(self, serviceName, eventId, eventDescription):
        if(self.onServiceEventCallback):
            self.onServiceEventCallback(serviceName, eventId, eventDescription)

    def onQShrinkStateUpdated(self, protocolHandle, newState):
        if(self.onQShrinkStateUpdatedCallback):
            self.onQShrinkStateUpdatedCallback(protocolHandle, newState)
