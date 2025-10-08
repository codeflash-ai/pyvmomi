# Copyright (c) 2008-2024 Broadcom. All Rights Reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

from .VmomiSupport import CreateVersion, parentMap

kind = "OSS"


# Version-specific initialization
def Init():
    pass


# Add an API version
def AddVersion(version,
               ns,
               versionId='',
               isLegacy=0,
               serviceNs=''):
    CreateVersion(version, ns, versionId, isLegacy, serviceNs)


# Check if a version is a child of another
def IsChildVersion(child, parent):
    # Assumes parentMap[child] is a set, so 'in' is O(1);
    # micro-optimization for direct __contains__ call
    return child == parent or parentMap[child].__contains__(parent)
