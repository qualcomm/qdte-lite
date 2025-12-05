# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
from QutsAtom.Atom_QutsClient_init import QutsClientList
from ImageManagementService.constants import *

class ImageManagementServiceList:
    @staticmethod
    def GetImageManagementServiceObject(qidx, handle):
        return QutsClientList.createService(qidx, IMAGE_MANAGEMENT_SERVICE_NAME, handle)
    @staticmethod
    def DeleteImageManagementServiceObject(qidx, handle):
        return QutsClientList.deleteService(qidx, IMAGE_MANAGEMENT_SERVICE_NAME, handle)
