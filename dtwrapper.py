# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file dtwrapper.py
This file is a wrapper that consolidates all functions that interface with the device tree.

This wrapper allows for:
 (0) a clearly-defined list of abilities of the backend (so that the backend may one day be swapped out more easily, if
     desired)
 (1) undo and redo functionality across the entire system (also changelogging)

Important notes:
* INPUTS ARE NOT VALIDATED! It is assumed that the data passed in is "good". Although there is basic error checking and
  handling when the library requires it, things like updating the value of a property assume that the new value is
  valid and will not do checking on it!
* Even though inputs are not validated, obvious errors (e.g. deleting a nonexistent node) WILL throw ValueErrors
  (usually; there may be other Exceptions thrown depending on the library in use). Thus, be sure to catch all exceptions
  stemming from operations that the user performs so that the appropriate feedback can be given to them.

This file is split up into various different classes. Please see the documentation for each class for more information.
"""

# fdt library we are using
from pyfdt import pyfdt

# configuration
from flags import flags as gf

# python libraries
from enum import Enum
import hashlib
import json
import traceback
import re
import dtlogger

"""
misc internal use "helper" functions that perform common tasks on the DeviceTree
"""


def _join_path(parent_path, name):
    """Join a parent path and name together into a complete path

    This function concatenates a parent path and a single item name in a manner that results in a valid path regardless
    of whether the parent path had a trailing slash or not.

    :param parent_path: Parent path, e.g. `/test`
    :param name: Item name, e.g. `property`
    :return: Joined path, e.g. `/test/property`
    """

    if name is not None:
        if parent_path[-1] == '/':
            parent_path += name
        else:
            parent_path += '/' + name

    return parent_path


def _get_path(fdt, parent_path, name=None, err_if_absent=True):
    """Get the item at a path in the Fdt

    This function gets an item from a given path in. It supports being given a parent path and a name and will call
    _join_path() on the two arguments if given that (if name is None, it assumes that the parent_path is the full and
    complete path).

    :param fdt: The *library* fdt to fetch from
    :param parent_path: The path to the parent of the item to fetch, or the entire path if name is None.
    :param name: Optionally the name of the item to fetch. Defaults to None, in which case the parent_path will be
                 treated as the entire path to the item.
    :param err_if_absent: Whether or not to raise a ValueError if the path was not found in the DeviceTree
    :return: The *library* item found at that path, or None if the path does not exist in the DeviceTree
    """

    # join the two paths if necessary
    fullpath = _join_path(parent_path, name)

    
    item = fdt.resolve_path(fullpath)
    if err_if_absent:
      if isinstance(item, type(None)):
        if gf['debug']:
            traceback.print_exc()
            raise ValueError('Item %s does not exist in DeviceTree!' % fullpath)
        else:
            raise ValueError('Item %s does not exist in DeviceTree!' % fullpath)
            return None

    return item


def _split_path(full_path):
    """Split an entire path into two parts, the parent and the name of the item itself

    :param full_path: The full path
    :return: An array of two items (first item is the parent path, and the second is the item name)
    """

    parent_name = full_path.rsplit('/', 1)
    if len(parent_name[0]) == 0:
        parent_name[0] = '/'

    return parent_name[0], parent_name[1]


def _dtb_hash(dtb):
    """Hash the DTB using SHA256

    :param dtb: Current DTB
    :return: string, in hexadecimal, representing the current SHA256 hash of the DTB
    """

    m = hashlib.sha256()
    m.update(dtb)
    return m.digest().hex()


def _add_node(fdt, parent_path, node_name, idx=-1):
    """Add a node to the Fdt

    Raises ValueErrors if invalid parameters are given.

    :param fdt: *library* Fdt
    :param parent_path: Path to the parent of this new node
    :param node_name: Name of the new node to be added
    :param idx: Index of the parent to add this node that. Defaults to -1, which means to add the node to the end.
    :return: the updated *library* Fdt
    """

    # step 1: get the parent node
    parent_node = fdt.resolve_path(parent_path)
    if not isinstance(parent_node, pyfdt.FdtNode):
        # something has gone wrong here
        raise ValueError('Given path %s does not point to a node!' % parent_path)

    # step 2: create the child node
    try:
        if len(node_name) == 0 or '/' in node_name:
            raise Exception()
        child_node = pyfdt.FdtNode(node_name)
        child_node.set_parent_node(parent_node)
    except Exception:
        if gf['debug']:
            traceback.print_exc()
        raise ValueError('Invalid node name %s given!' % node_name)

    # step 3: add the child node to the parent
    try:
        # add the child to the parent node
        if idx > 0:
            parent_node.insert(idx, child_node)
        else:
            parent_node.append(child_node)
    except Exception:
        if gf['debug']:
            traceback.print_exc()
        raise ValueError('Item named %s already in tree!' % node_name)

    return fdt

def _copy_node(fdt, parent_path, node_path, child_name, child_path):
    # parent_path : Path of parent to new node
    # node_path : Path of existing node to be copied
    # child_name : Name of new node
    # child_path : Path of new node
    # step 1: Checks
    #check that new node does not already exist
    child_node = fdt.resolve_path(child_path)
    if isinstance(child_node, pyfdt.FdtNode):
        # something has gone wrong here
        raise ValueError('Given path %s points to an existing node!' % child_path)
    #check if node to be copied exists
    existing_node = fdt.resolve_path(node_path)
    if not isinstance(existing_node, pyfdt.FdtNode):
        # something has gone wrong here
        raise ValueError('Node %s to be copied does not exist' % parent_path)

    # Step 2 : Create the parent path if needed
    parent_node = fdt.resolve_path(parent_path)
    current_path="/"
    if not isinstance(parent_node, pyfdt.FdtNode):
        nodes_list=parent_path.split("/")
        for i in nodes_list:
            if current_path[-1]=='/':
                current_path+=i
            else:
                current_path+='/'+i
            current_node = fdt.resolve_path(current_path)
            if not isinstance(current_node, pyfdt.FdtNode):
                current_parent_path=current_path.rsplit('/', 1)[0]
                current_child_name=current_path.rsplit('/', 1)[1]
                if current_parent_path=='':
                    current_parent_path='/'
                _add_node(fdt,current_parent_path,current_child_name)

    # step 3: Create the copy node
    _add_node(fdt,parent_path,child_name)

    # step 4 : Traverse fdt and copy nodes
    for (path, node) in fdt.resolve_path(node_path).walk():
        # If path is the same as child path, we must break the walk in order to prevent infinite loop
        if path==child_path:
            break
        # postfix_node_path = path.rsplit('/', 1)[1]
        remove_prefix_path = path.removeprefix(node_path)
        copy_node_path = remove_prefix_path.rsplit('/', 1)[0]
        copy_node_name = remove_prefix_path.rsplit('/', 1)[1]
        copy_parent_path=''
        if parent_path=='/':
            copy_parent_path = parent_path + child_name + copy_node_path
        else:
            copy_parent_path = parent_path + '/' + child_name + copy_node_path

        # Based on existing node, add accordingly
        if isinstance(node, pyfdt.FdtNode):
            _add_node(fdt,copy_parent_path,copy_node_name)
        elif isinstance(node, pyfdt.FdtPropertyWords):
            _add_property(fdt,copy_parent_path,copy_node_name,FdtPropertyType.WORDS,node.words)
        elif isinstance(node, pyfdt.FdtPropertyBytes):
            _add_property(fdt,copy_parent_path,copy_node_name,FdtPropertyType.BYTES,node.bytes)
        elif isinstance(node, pyfdt.FdtPropertyStrings):
            _add_property(fdt,copy_parent_path,copy_node_name,FdtPropertyType.STRINGS,node.strings)
        elif isinstance(node, pyfdt.FdtProperty):
            _add_property(fdt,copy_parent_path,copy_node_name)
    return fdt


def _add_property(fdt, parent_path, prop_name, prop_type=None, prop_value=None, idx=-1):
    """Add a property to the DeviceTree

    :param fdt: *library* Fdt
    :param parent_path: Path to the parent of this new property
    :param prop_name: Name of the new property to be added
    :param prop_type: The FdtPropertyType of this property. Defaults to None, which will create an EMPTY type property.
    :param prop_value: The value of the new property. Defaults to None, which will only be valid for EMPTY type props.
    :param idx: Index of the parent to add this node that. Defaults to -1, which means to add the node to the end.
    :return: the updated *library* Fdt
    """

    # step 1: get the parent node
    parent_node = fdt.resolve_path(parent_path)
    if not isinstance(parent_node, pyfdt.FdtNode):
        # something has gone wrong here
        raise ValueError('Given path %s does not point to a node!' % parent_path)

    # step 2: create the child node
    try:
        if len(prop_name) == 0 or '/' in prop_name:
            raise ValueError('Bad property name')  # will be passed up to the wrapping try/catch
        if not prop_type or prop_type == FdtPropertyType.EMPTY:
            child_prop = pyfdt.FdtProperty(prop_name)
        elif prop_type == FdtPropertyType.BYTES:
            child_prop = pyfdt.FdtPropertyBytes(prop_name, prop_value)
        elif prop_type == FdtPropertyType.WORDS:
            child_prop = pyfdt.FdtPropertyWords(prop_name, prop_value)
        elif prop_type == FdtPropertyType.STRINGS:
            child_prop = pyfdt.FdtPropertyStrings(prop_name, prop_value)
        else:
            raise ValueError('Bad property type')  # unrecognized property type
    except Exception:
        if gf['debug']:
            traceback.print_exc()
        raise ValueError('Invalid property name %s or value %s given!' % (prop_name, prop_value))

    # step 3: add the child node to the parent
    try:
        # add the child to the parent node
        if idx >= 0:
            parent_node.insert(idx, child_prop)
        else:
            parent_node.append(child_prop)
    except Exception:
        if gf['debug']:
            traceback.print_exc()
        raise ValueError('Item named %s already in tree!' % prop_name)

    return fdt


def _delete_item(fdt, parent_path, item_name):
    """Delete any item (node or property both supported) from the DeviceTree

    :param fdt: *library* Fdt
    :param parent_path: The path to the parent of the item to be deleted
    :param item_name: The name of the item to be deleted
    :return: the updated *library* Fdt
    """

    # step 1: get the parent node
    parent_node = fdt.resolve_path(parent_path)
    if not isinstance(parent_node, pyfdt.FdtNode):
        # something has gone wrong here
        raise ValueError('Given path %s does not point to a node!' % parent_path)

    # step 2: remove the item from the parent node
    try:
        parent_node.remove(item_name)
    except ValueError:
        if gf['debug']:
            traceback.print_exc()
        raise ValueError('Node %s has no child named %s!' % item_name)

    return fdt


class DTOperationType(Enum):
    """Enum to describe the type of a DTOperation"""

    # all of the possible operations
    NULL = 0
    LOAD = 1  # arg1 = "filename" = path to file. cannot be undone properly.
    EDIT_PROPERTY_VALUE = 2  # arg1 = "path" = path to property, arg2 = "value" = new value
    ADD_NODE = 4  # arg1 = "path" = path to parent, arg2 = "name" = new node's name
    ADD_PROPERTY = 5  # arg1 = "path" = path to parent, arg2 = "name" = new name, arg3 = "type" = property type, ...
    # ... arg4 = "value" = value of new property (optional)
    DELETE_NODE = 6  # arg1 = "path" = path to parent, arg2 = "name" = node name
    DELETE_PROPERTY = 7  # arg1 = "path" = path to parent, arg2 = "name" = property name
    RENAME_PROPERTY = 8  # arg1 = "to" = new name, arg1 = "path" = path to parent, arg2 = "from" = old name ...
    # ... (optional, if not specified, it will attempt to take the last part of arg1 and use that as the old name)
    # internal operations
    COPY_NODE = 9
    SAVE_DTB = 998  # arg1 = "filename" = file name to save to
    BIDRECTIONAL_MSGBOX = 999  # arg1 = "message" = error to throw


    def to_pretty(self):
        pretty = self.name.lower()
        return ' '.join(word[0].upper() + word[1:] for word in pretty.split('_'))


class UnknownDTOperationError(Exception):
    """
    Exception raised when an unknown DTOperationType is given to DTOperation.make()
    """

    pass


class UndoRedoExhaustedError(Exception):
    """
    Exception raised when there are no more items to undo or redo
    """

    pass


class HashMismatchError(Exception):
    """
    Exception raised when redoing an operation but the new hash of the DTB does not match the expected hash previously
    stored in the DTOperation metadata.
    """

    pass


class DTOperation:
    """Main DeviceTree operation base class.

    All other DTOperations are subclasses of this main class. This class contains
    the code to handle reporting/serialization for all DTOperations, as well as the inverse (creating a DTOperation from
    a report). It also contains shared code to store and check the hash of a DTB, and a stub for checking the path
    that was modified by an operation (if a subclass does not override this stub, it defaults to '/', i.e. entire
    DeviceTree has changed).
    """

    def __init__(self, optype):
        self.optype = optype
        self._hash = None
        # not all keys will be reported
        self._reportkeys = [('optype', 'operation'), ('_hash', 'hash')]
        if hasattr(self, '_arkeys'):
            self._reportkeys.extend(self._arkeys)
        else:
            dtlogger.info('Warning: {} has no attr _arkeys!'.format(type(self)))

    def apply(self, fdt):
        # apply the operation to the given fdt and return the new fdt
        return fdt

    def undo(self, fdt):
        # apply the operation to the given fdt and return the new fdt
        return fdt

    def __str__(self):
        ret = self.optype.name + ':\t'
        if not hasattr(self, '_arkeys'):
            return ret

        for rk in self._arkeys:
            if type(rk) is tuple and len(rk) == 2:
                ret += rk[1] + '(%s)  ' % getattr(self, rk[0])
            else:
                ret += rk + '(%s)  ' % getattr(self, rk)
        return ret

    def report(self):
        # generate a dict representation of this change (which will later be turned to JSON)
        repobj = {}

        for key in self._reportkeys:
            if type(key) is tuple and len(key) == 2:
                # tuple of (key, obj_key) where key = key in the object, and obj_key = destination key
                key, obj_key = key
            else:
                obj_key = key
            if hasattr(self, key) and getattr(self, key):
                obj_key = obj_key.replace('?', '')
                repobj[obj_key] = getattr(self, key)

                # tweak to make DTOperationType work
                repobj[obj_key] = getattr(repobj[obj_key], 'name', repobj[obj_key])

        return repobj

    @staticmethod
    def make_from_dict(d, nbr=-1):
        """Create a new DTOperation from a Python dict.

        This function creates a new DTOperation from a Python dict. It is called to create DTOperations from the change
        report JSON. It effectively undoes the report() function.

        :param d: The dictionary to use
        :param nbr: The number of the dictionary in the file. Used to display a more helpful error message to the user
                    if something goes wrong (i.e. it will tell the user which object number failed to parse).
        :return: The new DTOperation created based on the dictionary given
        """

        # mapping of the different DTOperationTypes to the corresponding classes in the code
        typemap = {
            DTOperationType.NULL: DTOperation,
            DTOperationType.LOAD: DTOperationLoad,
            DTOperationType.EDIT_PROPERTY_VALUE: DTOperationEditPropVal,
            DTOperationType.ADD_NODE: DTOperationAddNode,
            DTOperationType.ADD_PROPERTY: DTOperationAddProperty,
            DTOperationType.DELETE_NODE: DTOperationDeleteNode,
            DTOperationType.DELETE_PROPERTY: DTOperationDeleteProperty,
            DTOperationType.RENAME_PROPERTY: DTOperationRenameProperty,
            DTOperationType.SAVE_DTB: DTOperationSaveDtb,
            DTOperationType.BIDRECTIONAL_MSGBOX: DTOperationShowMessageBox,

        }

        # step 1 is to fetch the correct class that we should be using for this operation
        if 'operation' not in d or not isinstance(d['operation'], str):
            raise ValueError('Could not find the operation key in a JSON object!')
        if not hasattr(DTOperationType, d['operation']):
            raise ValueError('Unknown operation type %s in report!' % d['operation'])
        ot = DTOperationType[d['operation']]
        make_cls = typemap[ot]

        # next, we fetch the keys that this operation expects
        keys = make_cls._arkeys
        keys_trans = {}

        for key in keys:
            if type(key) is tuple and len(key) == 2:
                # tuple of (key, obj_key) where key = key in the object, and obj_key = destination key
                cls_key, key = key
            else:
                # just the key in the object is the same as the variable name in the object
                cls_key = key

            if '?' in key:
                # if there is a ? in the key, that means it is optional, so we don't necessarily have to have it.
                # if not present, it will default to None
                key = key.replace('?', '')
                if key in d:
                    # store the key in the translated
                    keys_trans[cls_key] = d[key]
                else:
                    # key is optional
                    keys_trans[cls_key] = None
            else:
                if key not in d:
                    raise ValueError('Object%s of type %d (%s) is missing key %s!' %
                                     ((' number %d' % nbr) if nbr >= 0 else '', ot.value, ot.name, key))

                # store the key in the translated
                keys_trans[cls_key] = d[key]

        # call the appropriate constructor to make a new DTOperation with the given kwargs
        cls = make_cls(ot, **keys_trans)

        if 'hash' in d:
            # store the hash, if present
            cls.store_hash(d['hash'])

        # done
        return cls

    def store_hash(self, postOpHash):
        # store the hash after the operation
        self._hash = postOpHash

    def hash_equals(self, cmpHash):
        # check if the given hash equals the one that we are expecting
        return self._hash == cmpHash if (self._hash is not None and len(self._hash) > 0) else True

    def get_modified_path(self):
        # default is to return everything was modified
        _ = self
        return '/'

    @staticmethod
    def make(optype, *args):
        """Create a new DTOperation based on the given specifications

        This function calls the corresponding DTOperation constructor for a given DTOperationType, passing it the
        arguments it was given.

        :param optype: Operation type (DTOperationType instance)
        :param args: The arguments to pass to the corresponding DTOperation class constructor. See comments in
                     DTOperationType for information on what arguments are needed and which order to pass them in.
        :return: The new DTOperation, if successful
        :raises UnknownDTOperationError: Invalid DTOperationType given, or input optype is not a DTOperationType
        :raises ValueError: Error occurred with the creation process itself (e.g. invalid arguments). Not currently
                            explicitly raised in the code.
        """

        makemap = {
            DTOperationType.NULL: DTOperation,
            DTOperationType.LOAD: DTOperationLoad,
            DTOperationType.EDIT_PROPERTY_VALUE: DTOperationEditPropVal,
            DTOperationType.ADD_NODE: DTOperationAddNode,
            DTOperationType.ADD_PROPERTY: DTOperationAddProperty,
            DTOperationType.DELETE_NODE: DTOperationDeleteNode,
            DTOperationType.DELETE_PROPERTY: DTOperationDeleteProperty,
            DTOperationType.RENAME_PROPERTY: DTOperationRenameProperty,
            DTOperationType.SAVE_DTB: DTOperationSaveDtb,
            DTOperationType.BIDRECTIONAL_MSGBOX: DTOperationShowMessageBox,
            DTOperationType.COPY_NODE: DTOperationCopyNode,
        }

        if optype in makemap:
            return makemap[optype](optype, *args)
        else:
            raise UnknownDTOperationError("Unrecognized DTOperation %s" % optype)


class DTOperationLoad(DTOperation):
    """DTOperation representing a load of a new DTB file into the application

    After this operation is applied, the undo stack is usually cleared, since it is not possible to properly undo this
    operation.
    """

    # additional keys we want to include in the report function
    _arkeys = ['filename']

    def __init__(self, optype, filename):
        super().__init__(optype)
        self.filename = filename

    def apply(self, fdt):
        # apply the operation to the given fdt and return the new fdt
        with open(self.filename, 'rb') as infile:
            try:
                dtb = pyfdt.FdtBlobParse(infile)
                fdt = dtb.to_fdt()
            except Exception as ex:
                if gf['debug']:
                    traceback.print_exc()
                raise ValueError('Failed to open file: %s ' % ex)

        return fdt

    def undo(self, fdt):
        # apply the operation to the given fdt and return the new fdt
        return None


class DTOperationEditPropVal(DTOperation):
    """DTOperation representing an edit of an existing property's value"""

    # additional keys we want to include in the report function
    _arkeys = [('prop_path', 'path'), ('val_new', 'value')]

    val_old = None

    def __init__(self, optype, prop_path, val_new):
        super().__init__(optype)
        self.prop_path = prop_path
        self.val_new = val_new

    def apply(self, fdt):
        prop = _get_path(fdt, self.prop_path)
        vals = []
        if isinstance(prop, pyfdt.FdtPropertyWords):
            self.val_old = prop.words
            for val in self.val_new:
                #dtlogger.debug(type(val))
                if isinstance(val,type('')):
                   vals.append(int(val))
                else:
                   vals.append(val)
            #dtlogger.debug("new list is %s"%vals)
            prop.words = vals
        elif isinstance(prop, pyfdt.FdtPropertyBytes):
            self.val_old = prop.bytes
            prop.bytes = self.val_new
        elif isinstance(prop, pyfdt.FdtPropertyStrings):
            self.val_old = prop.strings
            prop.strings = self.val_new
        else:
            self.val_old = b''

        return fdt

    def undo(self, fdt):
        if self.val_old is None:
            raise ValueError('Cannot undo operation before doing it!')

        prop = _get_path(fdt, self.prop_path)
        if isinstance(prop, pyfdt.FdtPropertyWords):
            prop.words = self.val_old
        elif isinstance(prop, pyfdt.FdtPropertyBytes):
            prop.bytes = self.val_old
        elif isinstance(prop, pyfdt.FdtPropertyStrings):
            prop.strings = self.val_old

        self.val_old = None

        return fdt

    def get_modified_path(self):
        return self.prop_path


class DTOperationAddNode(DTOperation):
    """DTOperation representing an addition of a new node to the DeviceTree"""

    # additional keys we want to include in the report function
    _arkeys = [('parent_path', 'path'), ('node_name', 'name')]

    def __init__(self, optype, parent_path, node_name):
        super().__init__(optype)
        self.parent_path = parent_path
        self.node_name = node_name

    def apply(self, fdt):
        return _add_node(fdt, self.parent_path, self.node_name)

    def undo(self, fdt):
        return _delete_item(fdt, self.parent_path, self.node_name)

    def get_modified_path(self):
        return _join_path(self.parent_path, self.node_name)

class DTOperationCopyNode(DTOperation):
    """DTOperation representing an addition of a new node to the DeviceTree"""

    # additional keys we want to include in the report function
    _arkeys = [('parent_path', 'path'), ('node_path', 'path'), ('node_name', 'name'),('child_path', 'path')]

    def __init__(self, optype, parent_path, node_path, node_name, child_path):
        super().__init__(optype)
        self.parent_path = parent_path
        self.node_path = node_path
        self.node_name = node_name
        self.child_path = child_path

    def apply(self, fdt):
        return _copy_node(fdt, self.parent_path, self.node_path, self.node_name, self.child_path)

    def undo(self, fdt):
        return _delete_item(fdt, self.parent_path, self.node_name)

    def get_modified_path(self):
        return _join_path(self.parent_path, self.node_name)

class DTOperationAddProperty(DTOperation):
    """DTOperation representing the addition of a new property to the DeviceTree"""

    # additional keys we want to include in the report function
    _arkeys = [('parent_path', 'path'), ('prop_name', 'name'), ('prop_type', 'type'), ('prop_value', 'value?')]

    def __init__(self, optype, parent_path, prop_name, prop_type=None, prop_value=None):
        super().__init__(optype)
        self.parent_path = parent_path
        self.prop_name = prop_name
        if isinstance(prop_type, str):
            self.prop_type = FdtPropertyType[prop_type]
        else:
            self.prop_type = prop_type
        self.prop_value = prop_value

    def apply(self, fdt):
        return _add_property(fdt, self.parent_path, self.prop_name, self.prop_type, self.prop_value)

    def undo(self, fdt):
        return _delete_item(fdt, self.parent_path, self.prop_name)

    def get_modified_path(self):
        return _join_path(self.parent_path, self.prop_name)


class DTOperationDeleteNode(DTOperation):
    """DTOperation representing the deletion of a node from the DeviceTree

    A separate operation is needed between deleting a node and a property because of the data that is stored in order to
    undo the operation; nodes store their old children, but properties store their old values.
    """

    # additional keys we want to include in the report function
    _arkeys = [('parent_path', 'path'), ('node_name', 'name')]

    children = None
    idx = -1

    def __init__(self, optype, parent_path, node_name=None):
        super().__init__(optype)
        if node_name is None:
            self.parent_path, self.node_name = _split_path(parent_path)
        else:
            self.parent_path = parent_path
            self.node_name = node_name

    def apply(self, fdt):
        self.children = _get_path(fdt, self.parent_path, self.node_name).subdata
        self.idx = _get_path(fdt, self.parent_path).index(self.node_name)
        return _delete_item(fdt, self.parent_path, self.node_name)

    def undo(self, fdt):
        if self.children is None:
            raise ValueError('Cannot undo operation before doing it!')

        fdt = _add_node(fdt, self.parent_path, self.node_name, self.idx)
        child_node = _get_path(fdt, self.parent_path, self.node_name)
        child_node.subdata = self.children

        return fdt

    def get_modified_path(self):
        return _join_path(self.parent_path, self.node_name)


class DTOperationDeleteProperty(DTOperation):
    """DTOperation representing the deletion of a property from the DeviceTree

    A separate operation is needed between deleting a node and a property because of the data that is stored in order to
    undo the operation; nodes store their old children, but properties store their old values.
    """

    # additional keys we want to include in the report function
    _arkeys = [('parent_path', 'path'), ('prop_name', 'name')]

    prop_type = None
    prop_value = None
    idx = -1

    def __init__(self, optype, parent_path, prop_name=None):
        super().__init__(optype)

        if prop_name is None:
            self.parent_path, self.prop_name = _split_path(parent_path)
        else:
            self.parent_path = parent_path
            self.prop_name = prop_name

    def apply(self, fdt):
        prop = FdtProperty(_get_path(fdt, self.parent_path, self.prop_name))
        self.prop_type = prop.get_type()
        self.prop_value = prop.get_value()
        self.idx = _get_path(fdt, self.parent_path).index(self.prop_name)
        return _delete_item(fdt, self.parent_path, self.prop_name)

    def undo(self, fdt):
        if self.prop_type is None or self.prop_value is None:
            raise ValueError('Cannot undo operation before doing it!')

        fdt = _add_property(fdt, self.parent_path, self.prop_name, self.prop_type, self.prop_value, self.idx)
        return fdt

    def get_modified_path(self):
        return _join_path(self.parent_path, self.prop_name)


class DTOperationRenameProperty(DTOperation):
    """DTOperation representing a rename of a property

    Only property renaming is currently supported since node renaming is more complicated (if nodes have children, they
    need to be renamed, too).
    """

    # additional keys we want to include in the report function
    _arkeys = [('parent_path', 'path'), ('old_name', 'from'), ('new_name', 'to')]

    def __init__(self, optype, new_name, parent_path, old_name=None):
        super().__init__(optype)

        self.new_name = new_name

        if old_name is None:
            self.parent_path, self.old_name = _split_path(parent_path)
        else:
            self.parent_path = parent_path
            self.old_name = old_name

    def apply(self, fdt):
        ensure = _get_path(fdt, self.parent_path, self.new_name, err_if_absent=False)
        if ensure:
            raise ValueError('Item with same name already exists in DeviceTree!')
        prop = _get_path(fdt, self.parent_path, self.old_name)
        prop.name = self.new_name
        return fdt

    def undo(self, fdt):
        ensure = _get_path(fdt, self.parent_path, self.old_name, err_if_absent=False)
        if ensure:
            raise ValueError('Item with same name already exists in DeviceTree!')
        prop = _get_path(fdt, self.parent_path, self.new_name)
        prop.name = self.old_name
        return fdt

    def get_modified_path(self):
        return [_join_path(self.parent_path, self.old_name), _join_path(self.parent_path, self.new_name)]


class DTOperationSaveDtb(DTOperation):
    """DTOperation representing a save of a DTB

    NB: This operation is not created in normal use of the program.
    """

    _arkeys = ['filename']

    def __init__(self, optype, filename):
        super().__init__(optype)
        self.filename = filename

    def apply(self, fdt):
        if gf['dryRun']:
            # don't write if we're doing a dry run
            return fdt

        with open(self.filename, 'wb') as f:
            f.write(fdt.to_dtb())
        return fdt

    def undo(self, fdt):
        raise ValueError('Cannot undo save operation')


class DTOperationShowMessageBox(DTOperation):
    """DTOperation that throws an error with a user-defined message

    This DTOperation will throw a customizable error message when it is applied. Since errors will result in a dialog
    box appearing, this behaviour can be leveraged to show a custom message in a dialog box.

    NB: This operation is not created in normal use of the program.
    """

    # additional keys we want to include in the report function
    _arkeys = ['message']

    def __init__(self, optype, message):
        super().__init__(optype)
        self.message = message
        self.has_raised = False

    def apply(self, fdt):
        if not self.has_raised:
            self.has_raised = True
            raise Exception(self.message)
        else:
            return fdt

    def undo(self, fdt):
        if not self.has_raised:
            self.has_raised = True
            raise Exception(self.message)
        else:
            return fdt

    def hash_equals(self, cmp_hash):
        return True


class FdtPropertyType(Enum):
    """Enum representing the type of a property"""

    EMPTY = 0
    STRINGS = 1
    WORDS = 2
    BYTES = 3

    def __str__(self):
        return self.name


class FdtItem:
    """An FdtItem is any item that can appear in a DeviceTree; it can either be a node or property"""

    def is_node(self):
        return isinstance(self, FdtNode)

    def is_property(self):
        return isinstance(self, FdtProperty)

    @staticmethod
    def make(lib_item):
        if lib_item is None:
            return None
        elif isinstance(lib_item, pyfdt.FdtNode):
            return FdtNode(lib_item)
        else:
            return FdtProperty(lib_item)


class FdtProperty(FdtItem):
    """Custom wrapper around every property that is in a DeviceTree

    This class is a wrapper around the whatever type(s) the backing library may have to represent properties in the
    DeviceTree.
    """

    def __init__(self, lib_prop):
        self._libProp = lib_prop

    def __str__(self):
        return self.to_pretty()

    def to_pretty(self):
        if isinstance(self._libProp, pyfdt.FdtPropertyStrings):
            return '\'' + '\' \''.join(self._libProp.strings) + '\''
        elif isinstance(self._libProp, pyfdt.FdtPropertyWords):
            if gf['viewAsHex']:
                return ' '.join(hex(word) for word in self._libProp.words)
            else:
                return ' '.join([str(word) for word in self._libProp.words])
        elif isinstance(self._libProp, pyfdt.FdtPropertyBytes):
            if gf['viewAsHex']:
                return ' '.join(hex(byte) for byte in self._libProp.bytes)
            else:
                return ' '.join([str(word) for word in self._libProp.bytes])
        else:
            return ''

    def to_raw(self):
        return self._libProp.to_raw()

    def get_type(self):
        if isinstance(self._libProp, pyfdt.FdtPropertyStrings):
            return FdtPropertyType.STRINGS
        elif isinstance(self._libProp, pyfdt.FdtPropertyWords):
            return FdtPropertyType.WORDS
        elif isinstance(self._libProp, pyfdt.FdtPropertyBytes):
            return FdtPropertyType.BYTES
        else:
            return FdtPropertyType.EMPTY

    def get_value(self):
        if isinstance(self._libProp, pyfdt.FdtPropertyStrings):
            return self._libProp.strings
        elif isinstance(self._libProp, pyfdt.FdtPropertyWords):
            return self._libProp.words
        elif isinstance(self._libProp, pyfdt.FdtPropertyBytes):
            return list(self._libProp.bytes)
        else:
            return ''


class FdtNode(FdtItem):
    """Custom wrapper around every node that is in a DeviceTree

    This class is a wrapper around the whatever type(s) the backing library may have to represent nodes in the
    DeviceTree. It also defines a walk() function to return a generator that yields all of the children of the node,
    represented in dtwrapper classes.
    """

    def __init__(self, lib_node):
        self._libNode = lib_node

    def __str__(self):
        return str(self._libNode)

    def to_raw(self):
        return self._libNode.to_raw()

    def walk(self):
        for path, item in self._libNode.walk():
            yield path, FdtItem.make(item)


class DTWrapper:
    """Main class that keeps track of state in interactions with the DeviceTree

    This class contains variables that keep track of the current DeviceTree being edited, the undo and redo stacks, and
    stores a copy of the current DeviceTree Blob, too. It also contains functions that get information about the current
    state of the system (e.g. number of items in the undo stack, list of changes made to the devicetree since the last
    load, and a method to get the FdtItem at a given path).

    In general, the DTGUIController (controller.py) interfaces with the functions in this class.
    """

    def __init__(self):
        self._fdt = None
        self.fdt_name = None
        self.dtb = None
        self.dtb_mappings = {}
        self._undoStack = []
        self._redoStack = []

    def _update_dtb(self):
        self.dtb_mappings = {}
        if self._fdt is not None:
            self.dtb = self._fdt.to_dtb(self.dtb_mappings)
        else:
            self.dtb = None

    def reset(self):
        # TODO: prevent code duplication with __init__() here... can we call __init__()?
        self._fdt = None
        self.fdt_name = None
        self.dtb = None
        self.dtb_mappings = {}
        self._undoStack = []
        self._redoStack = []

    def apply(self, op):  # apply an operation
        # apply the operation
        self._fdt = op.apply(self._fdt)

        # update the hash
        self._update_dtb()
        op.store_hash(_dtb_hash(self.dtb))

        # can no longer redo anything since the base has been modified
        self._redoStack.clear()

        # add to undo stack
        # if qdte run in command mode, don't clear the undo stack.
        # In order to recoder all the operations.
        if op.optype == DTOperationType.LOAD and gf['nogui'] == False:
            # clear the undo stack
            self._undoStack = [op]
            # set the filename
            self.fdt_name = op.filename
        else:
            self._undoStack.append(op)

        # return the path that was modified
        return op.get_modified_path()

    def undo(self):  # undo most recent
        if len(self._undoStack) == 0:
            raise UndoRedoExhaustedError('No more items left to undo')

        # pop off the most recently done operation
        op = self._undoStack.pop()

        # undo it
        self._fdt = op.undo(self._fdt)

        # update the hash
        self._update_dtb()
        if gf['verifyHash'] and len(self._undoStack) > 0:
            curr_hash = _dtb_hash(self.dtb)
            # the hash should match the hash of the top of the undo stack
            if not self._undoStack[-1].hash_equals(curr_hash):
                raise HashMismatchError('Hash of current DTB does not match expected hash %s' % curr_hash)

        # add it to the redo stack
        self._redoStack.append(op)

        # return the path that was modified
        return op.get_modified_path()

    def top_undo(self):
        return None if len(self._undoStack) == 0 else self._undoStack[-1]

    def redo(self):  # redo most recent operation
        if len(self._redoStack) == 0:
            raise UndoRedoExhaustedError('No more items left to redo')

        # pop off the top item of the redo stack
        op = self._redoStack.pop()

        # apply it
        self._fdt = op.apply(self._fdt)

        if op.optype == DTOperationType.LOAD:
            # set the filename
            self.fdt_name = op.filename

        # update the hash
        self._update_dtb()
        if gf['verifyHash']:
            curr_hash = _dtb_hash(self.dtb)
            if not op.hash_equals(curr_hash):
                raise HashMismatchError('Hash of current DTB does not match expected hash %s' % curr_hash)

        # add it to the undo stack
        self._undoStack.append(op)

        # return the path that was modified
        return op.get_modified_path()

    def top_redo(self):
        return None if len(self._redoStack) == 0 else self._redoStack[-1]

    def report(self, pyobj=False):  # generate JSON summary report of operations done
        reports = []
        for itm in self._undoStack:
            rep = itm.report()
            if rep:
                reports.append(rep)

        # indent the final JSON to make it more human-readable
        if pyobj:
            return reports
        else:
            return json.dumps(reports, indent=2)

    def import_report(self, report):  # import a report
        if isinstance(report, bytes) or isinstance(report, str):
            reports = json.loads(report)
        else:
            reports = report
        valid_reports = []

        for report in reports:
            r = DTOperation.make_from_dict(report)
            valid_reports.append(r)

        # want to reverse the order so we open the file first
        valid_reports.reverse()

        self._fdt = None
        self.dtb = None
        self.dtb_mappings = {}
        self._redoStack = valid_reports
        self._undoStack = []

    def to_dts(self):  # save the current FDT as a DTS
        return self._fdt.to_dts()

    def has_file(self):  # check if there is a file open
        return self._fdt is not None

    def resolve_path(self, path='/', want_parent_idx=False):  # resolve a path in the Fdt
        # turn the library-returned path into a custom one
        r = FdtItem.make(self._fdt.resolve_path(path))

        if want_parent_idx:
            # we also want to know the index of this item in its parent
            parent_path, child_name = _split_path(path)
            if child_name:
                idx = _get_path(self._fdt, parent_path).index(child_name)
            else:
                idx = 0
            return r, idx
        else:
            return r
