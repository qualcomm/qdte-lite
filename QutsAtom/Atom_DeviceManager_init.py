# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from QutsAtom.Atom_QutsClient import QutsClientList

class DeviceManagerList:
    @staticmethod
    def GetDeviceManagerObject(qidx):
        return QutsClientList.getDeviceManager(qidx)
    @staticmethod
    def DeleteDeviceManagerObject(qidx):
        return QutsClientList.deleteDeviceManager(qidx)
