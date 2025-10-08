# Copyright (c) 2008-2025 Broadcom. All Rights Reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# Diff any two objects

import logging

from .five import PY3
from pyVmomi.VmomiSupport import F_LINK, F_OPTIONAL, GetWsdlName, Type, types

if not PY3:
    from .five import zip

from .VmomiSupport import F_LINK, F_OPTIONAL, GetWsdlName, Type, types

__Log__ = logging.getLogger('ObjDiffer')


def LogIf(condition, message):
    """Log a message if the condition is met"""
    if condition:
        __Log__.debug(message)

_primitive_types = (types.bool, types.byte, types.short, types.double, types.float,
                    types.PropertyPath, types.ManagedMethod,
                    types.datetime, types.URI, types.binary, type)

_primitive_types += (int, str) if PY3 else (int, long, basestring)

def IsPrimitiveType(obj):
    """See if the passed in type is a Primitive Type"""
    return isinstance(obj, _primitive_types)

class Differ:
    """Class for comparing two Objects"""
    def __init__(self, looseMatch=False, ignoreArrayOrder=True):
        self._looseMatch = looseMatch
        self._ignoreArrayOrder = ignoreArrayOrder

    def DiffAnyObjects(self, oldObj, newObj, isObjLink=False):
        """Diff any two Objects"""
        if oldObj == newObj:
            return True
        if not oldObj or not newObj:
            __Log__.debug('DiffAnyObjects: One of the objects is unset.')
            return self._looseMatch

        # Avoid repeated isinstance/list checks and rebinding
        oldObjIsList = isinstance(oldObj, list)
        newObjIsList = isinstance(newObj, list)
        oldObjInstance = oldObj[0] if oldObjIsList else oldObj
        newObjInstance = newObj[0] if newObjIsList else newObj

        # Primitive type check first
        if (IsPrimitiveType(oldObj) and IsPrimitiveType(newObj)
                and oldObj.__class__.__name__ == newObj.__class__.__name__):
            if oldObj == newObj:
                return True
            elif oldObj is None or newObj is None:
                __Log__.debug('DiffAnyObjects: One of the objects in None')
            return False

        # Fast local
        oldType = Type(oldObjInstance)
        newType = Type(newObjInstance)
        if oldType != newType:
            __Log__.debug('DiffAnyObjects: Types do not match %s != %s',
                          repr(GetWsdlName(oldObjInstance.__class__)),
                          repr(GetWsdlName(newObjInstance.__class__)))
            return False

        if oldObjIsList:
            return self.DiffArrayObjects(oldObj, newObj, isObjLink)

        if isinstance(oldObjInstance, types.ManagedObject):
            # If both are unset, True; if both set, compare _moId;
            # no need to check both unset with "not oldObj and not newObj" because
            # initial check (not oldObj or not newObj) handled above.
            return (not oldObj and not newObj) or (oldObj and newObj
                                        and oldObj._moId == newObj._moId)

        if isinstance(oldObjInstance, types.DataObject):
            if isObjLink:
                bMatch = oldObj.GetKey() == newObj.GetKey()
                if not bMatch:
                    __Log__.debug(
                        'DiffAnyObjects: Keys do not match %s != %s',
                        oldObj.GetKey(), newObj.GetKey())
                return bMatch
            return self.DiffDataObjects(oldObj, newObj)

        raise TypeError("Unknown type: " +
                        repr(GetWsdlName(oldObj.__class__)))

    def DiffDoArrays(self, oldObj, newObj, isElementLinks):
        """Diff two DataObject arrays"""
        if len(oldObj) != len(newObj):
            __Log__.debug('DiffDoArrays: Array lengths do not match %d != %d',
                          len(oldObj), len(newObj))
            return False
        for i, j in zip(oldObj, newObj):
            if isElementLinks:
                if i.GetKey() != j.GetKey():
                    __Log__.debug('DiffDoArrays: Keys do not match %s != %s',
                                  i.GetKey(), j.GetKey())
                    return False
            else:
                if not self.DiffDataObjects(i, j):
                    __Log__.debug(
                        'DiffDoArrays: one of the elements do not match')
                    return False
        return True

    def DiffAnyArrays(self, oldObj, newObj, isElementLinks):
        """Diff two arrays which contain Any objects"""
        if len(oldObj) != len(newObj):
            __Log__.debug(
                'DiffAnyArrays: Array lengths do not match. %d != %d',
                len(oldObj), len(newObj))
            return False
        for i, j in zip(oldObj, newObj):
            if not self.DiffAnyObjects(i, j, isElementLinks):
                __Log__.debug(
                    'DiffAnyArrays: One of the elements do not match.')
                return False
        return True

    def DiffPrimitiveArrays(self, oldObj, newObj):
        """Diff two primitive arrays"""
        if len(oldObj) != len(newObj):
            __Log__.debug('DiffDoArrays: Array lengths do not match %d != %d',
                          len(oldObj), len(newObj))
            return False
        match = True
        if self._ignoreArrayOrder:
            oldSet = oldObj and frozenset(oldObj) or frozenset()
            newSet = newObj and frozenset(newObj) or frozenset()
            match = (oldSet == newSet)
        else:
            for i, j in zip(oldObj, newObj):
                if i != j:
                    match = False
                    break
        if not match:
            __Log__.debug(
                'DiffPrimitiveArrays: One of the elements do not match.')
            return False
        return True

    def DiffArrayObjects(self, oldObj, newObj, isElementLinks=False):
        """Method which deligates the diffing of arrays based on the type"""
        if oldObj == newObj:
            return True
        if not oldObj or not newObj:
            return False
        oldLen = len(oldObj)
        if oldLen != len(newObj):
            __Log__.debug(
                'DiffArrayObjects: Array lengths do not match %d != %d',
                oldLen, len(newObj))
            return False

        firstObj = oldObj[0]
        if IsPrimitiveType(firstObj):
            return self.DiffPrimitiveArrays(oldObj, newObj)
        elif isinstance(firstObj, types.ManagedObject):
            return self.DiffAnyArrays(oldObj, newObj, isElementLinks)
        elif isinstance(firstObj, types.DataObject):
            return self.DiffDoArrays(oldObj, newObj, isElementLinks)
        else:
            raise TypeError("Unknown type: {0}".format(oldObj.__class__))

    def DiffDataObjects(self, oldObj, newObj):
        """Diff Data Objects"""
        if oldObj == newObj:
            return True
        if not oldObj or not newObj:
            __Log__.debug('DiffDataObjects: One of the objects in None')
            return False
        oldType = Type(oldObj)
        newType = Type(newObj)
        if oldType != newType:
            __Log__.debug(
                'DiffDataObjects: Types do not match for dataobjects. '
                '%s != %s', oldObj._wsdlName, newObj._wsdlName)
            return False

        get_prop_list = oldObj._GetPropertyList
        get_prop_info = oldObj._GetPropertyInfo

        for prop in get_prop_list():
            prop_name = prop.name
            oldProp = getattr(oldObj, prop_name)
            newProp = getattr(newObj, prop_name)
            propType = get_prop_info(prop_name).type
            propFlags = prop.flags

            if not oldProp and not newProp:
                continue
            elif ((propFlags & F_OPTIONAL) and self._looseMatch
                  and (not newProp or not oldProp)):
                continue
            elif not oldProp or not newProp:
                __Log__.debug(
                    'DiffDataObjects: One of the objects has '
                    'the property %s unset', prop_name)
                return False

            if IsPrimitiveType(oldProp):
                bMatch = oldProp == newProp
            elif isinstance(oldProp, types.ManagedObject):
                bMatch = self.DiffAnyObjects(oldProp, newProp, propFlags & F_LINK)
            elif isinstance(oldProp, types.DataObject):
                if propFlags & F_LINK:
                    bMatch = oldObj.GetKey() == newObj.GetKey()
                    if not bMatch:
                        __Log__.debug(
                            'DiffDataObjects: Key match failed %s != %s',
                            oldObj.GetKey(), newObj.GetKey())
                else:
                    bMatch = self.DiffAnyObjects(oldProp, newProp, propFlags & F_LINK)
            elif isinstance(oldProp, list):
                bMatch = self.DiffArrayObjects(oldProp, newProp,
                                               propFlags & F_LINK)
            else:
                raise TypeError("Unknown type: " + repr(propType))

            if not bMatch:
                __Log__.debug('DiffDataObjects: Objects differ in property %s',
                              prop_name)
                return False
        return True


def DiffAnys(obj1, obj2, looseMatch=False, ignoreArrayOrder=True):
    """Diff any two objects. Objects can either be primitive type
    or DataObjects
    """
    differ = Differ(looseMatch=looseMatch, ignoreArrayOrder=ignoreArrayOrder)
    return differ.DiffAnyObjects(obj1, obj2)
