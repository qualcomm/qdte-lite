# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
@file editview.py
@description Initialize all of the GUI elements of the DeviceTree edit window

This file contains a number of helper functions that validate user input for the different kinds of properties as well
as two classes that share the usage of these helper functions, namely the EditDialog (which is a separate dialog window
that pops up and displays information about the path of a property, the type, and value in hex/decimal for WORDS and
BYTES, and the string list for STRINGS, as well as giving the user the ability to edit the path and value) and
DtbSmartEntry (which is an extension of the tkinter Entry widget that adds validation for user input based on what the
type of the property that is being edited is).

The EditDialog is one of the older components of the GUI and is launched by the DTGUI controller (controller.py) when
the user requests to edit a property (through their interactions with the TreeView). One feature of this dialog was that
there was validation on the user input that enforced maximum value of and allowed characters in property values for
WORDS and BYTES. These validation functions were originally EditDialog instance functions. However, when inline editing
was later envisioned, there was a need for an Entry-like component that would be able to validate user input in the same
way that the entries in the EditDialog already did (later dubbed the DtbSmartEntry). In order to prevent duplicate code,
the validation functions were taken out of the EditDialog class and made into top-level helper functions that both of
the classes could use. Unfortunately, there is still some code duplication (mostly coming from initialization functions
for the classes that unpack a property value into an editable form), but it did not seem practical to move some of this
logic into helper functions, so things remain as they are now.
"""

# python string library
import string

# tkinter library
import tkinter as tk
import tkinter.messagebox

# fdt interface
import dtwrapper as dt

# flags
from flags import flags as gf

import dtlogger
"""
helper functions
"""


def int_allow_blank(nbrstr, base=10):
    """Helper function to convert a string to an int, but allow blanks (blank = 0)

    This helper function is a simple wrapper around the int() call, but iwth the difference that, if the string is
    empty, it will simply return 0. It is used by the functions that split an string of space-separated values into an
    array of ints, in order to prevent raising errors for empty strings that might occur if the user is trying to type
    in a new value.

    :param nbrstr: The number string to parse
    :param base: The base that `nbrstr` is in. Defaults to base 10.
    :return: The integer value of nbrstr (blank = 0)
    """

    return 0 if len(nbrstr) == 0 else int(nbrstr, base)


def strarray_to_string(arr):
    """Convert an array of strings into a single single-quote space-delimited string

    This function converts a list of strings into a single string. To do so, it first escapes the string where necessary
    (the characters that are escaped are the backslash, single quote, and tab), and then encloses the escaped string in
    single quotes, and finally joins the entire string list with spaces such that each string is separated by a space.
    For example, given a user input list ["one'", "two"], the output will be the string "'one\'' 'two'".

    This function is the counterpart/does the opposite of string_to_strarray(), although string_to_strarray() is capable
    of parsing a wider range of inputs than this function produces (e.g. two spaces separating different strings is
    fine for string_to_strarray(), but this function will not do that).

    :param arr: list of strings
    :return: string representing the given `arr`
    """

    def escape_helper(mystr):
        """helper function to escape the characters that need escaping"""

        # things that need to be escaped (use this order so that we don't replace \t into \\\\t)
        mystr = mystr.replace('\\', '\\\\')
        mystr = mystr.replace('\'', '\\\'')
        mystr = mystr.replace('\t', '\\t')
        return mystr

    # escape each string and add the single quotes around it
    ret = ['\'' + escape_helper(elem) + '\'' for elem in arr]

    # the output of this function is a string in the format 'str\t1\'' 'str\n2' '\\str_3'
    return ' '.join(ret)


def string_to_strarray(mystr):
    """Parse a single string of single-quoted space-delimited values into an array of strings

    :param mystr: string of single-quoted space-delimited values
    :return: list of strings representing the unescaped and parsed value of `mystr`
    """

    # parser flags, etc.
    seek_string_start = True
    escape_next = False
    ret = []
    str_start_pos = 0

    # rudimentary parser to filter out the start and end of a string (quotes) while ignoring escape sequences
    for i in range(0, len(mystr)):
        if seek_string_start:
            # only three characters are allowed in here: ', (last one is a space)
            if mystr[i] == ',' or mystr[i] == ' ':
                continue
            elif mystr[i] == '\'':
                # found the start of a string, so store it, and switch to looking for the end of a string instead
                seek_string_start = False
                str_start_pos = i + 1
            else:
                # parse error
                raise ValueError('string_to_strarray() Parse error: expected double-quote, comma, or space, but got '
                                 '%s instead!' % mystr[i])
        else:
            if escape_next:
                # wanted to escape the last character, so we escape it and continue
                # note that we don't actually replace in the input string yet - we do this later
                escape_next = False
                continue
            if mystr[i] == '\\':
                # backslash = escaping the next character
                escape_next = True
            elif mystr[i] == '\'':
                # found the end of a string; it goes from str_start_pos to i (inclusive)
                str_dat = mystr[str_start_pos:i]

                # parse out the representation
                # again, order matters! otherwise we could accidentally introduce escape sequences
                str_dat = str_dat.replace('\\\\', '\\')
                str_dat = str_dat.replace('\\\'', '\'')
                str_dat = str_dat.replace('\\t', '\t')

                # all good
                ret.append(str_dat)
                seek_string_start = True
            elif mystr[i] not in string.printable or mystr[i] in ('\r', '\n'):
                # check that this character is valid
                raise ValueError('string_to_strarray() error: Illegal character at position %d: %s' % (i, mystr[i]))

    if escape_next or (not seek_string_start):
        # still looking to escape something or for the end of a string, so something has gone wrong
        raise ValueError('Unexpected end of input when parsing')

    if len(ret) == 0 or any([True for mystr in ret if len(mystr) == 0]):
        # one of the strings was empty
        raise ValueError('STRINGS values are not permitted to be empty!')

    # all good!
    return ret


def check_data_nbr(new_str, max_value, base=10):
    if len(new_str) == 0:
        return [0]
    if '-' in new_str:
        # do not allow negatives
        return None
    try:
        res = [int_allow_blank(val, base) for val in new_str.split(' ')]

        # validate max value is not exceeded
        for nbr in res:
            if nbr > max_value:
                return None
    except ValueError:
        # error parsing, return false
        return None

    # validation passed
    return res


def commit_result(updated_value, delayed_check, e1):
    if gf['readonly']:
        # don't save changes if we're readonly
        return None

    if delayed_check:
        updated_value = string_to_strarray(e1.get())

    return updated_value


class EditDialog(tk.Toplevel):
    e0 = None
    e1 = None
    e2 = None
    currentValue = None
    ignore_change = False

    def __init__(self, controller, parent, path, item):
        # create a new window
        super().__init__(parent)
        self.transient(parent)
        self.wait_visibility()
        self.grab_set()
        

        # set various variables
        self.controller = controller
        self.parent = parent
        self.result = None
        self.nameResult = None
        if isinstance(item, dt.FdtProperty):
            # given item is an existing item in the devicetree
            self.item = item
            self.itemType = item.get_type()
            self.initialValue = item.get_value()
            # set title
            self.title('Edit Property : ' + path)
        else:
            # given item is just a type
            self.item = None
            self.itemType = item
            self.initialValue = None
            # set title
            self.title('New Property at : ' + path)

        pathparts = path.rsplit('/', 1)
        pathparts[0] += '/'
        self.path = pathparts

        # initialize ui components
        self._init_ui(path)

        # focus self
        self.after(1, lambda: self.focus_force())

        # wait for this window (prevent editing other windows)
        self.wait_window(self)

    def _init_ui(self, path):
        # minimum size is 300 wide (height is ignored since we can't resize along that axis anyways)
        self.minsize(300, 10)
        # so we can resize
        self.resizable(True, False)
        # used to place buttons in the last row of the grid (hex view adds an extra row)
        last_row = 3

        # labels with information (left side)
        tk.Label(self, text='Property path : ', justify='left', width=20, borderwidth=2,
                 relief='groove').grid(row=0)
        tk.Label(self, text='Data Type     : ', justify='left', width=20, borderwidth=2,
                 relief='groove').grid(row=1)
        tk.Label(self, text='Value(s)      : ', justify='left', width=20, borderwidth=2,
                 relief='groove').grid(row=2)

        # information that is always present
        check_name = self.register(self.check_name)
        self.e0 = tk.Entry(self, justify='left', validate='all', font='TkFixedFont',
                           validatecommand=(check_name, '%P'))
        self.e0.insert(0, path)
        self.e0.grid(row=0, column=1, stick='nesw')
        tk.Label(self, text=self.itemType, justify='left', width=60, borderwidth=2, relief='sunken') \
            .grid(row=1, column=1, sticky='nesw')

        if self.itemType == dt.FdtPropertyType.STRINGS:
            self.e1 = tk.Entry(self, justify='left', width=50)
            if self.item:
                self.e1.insert(0, strarray_to_string(self.item.get_value()))
            self.e1.grid(row=2, column=1, sticky='nesw')
        elif self.itemType == dt.FdtPropertyType.WORDS or self.itemType == dt.FdtPropertyType.BYTES:
            # show hex representation
            tk.Label(self, text='Hex Value(s)  : ', justify='left', width=20, borderwidth=2,
                     relief='groove').grid(row=3)

            # the value editor itself
            if self.itemType == dt.FdtPropertyType.WORDS:
                # validation commands
                check_dec = self.register(self.check_words_dec)
                check_hex = self.register(self.check_words_hex)
            else:  # (self.itemType == pyfdt.FdtPropertyType.BYTES)
                # validation commands
                check_dec = self.register(self.check_bytes_dec)
                check_hex = self.register(self.check_bytes_hex)

            # source data for filling the textbox
            if self.item:
                source_data = self.item.get_value()
            else:
                source_data = []

            # entries
            self.e1 = tk.Entry(self, justify='left', width=50, validate='all', font='TkFixedFont',
                               validatecommand=(check_dec, '%P'))
            self.e2 = tk.Entry(self, justify='left', width=50, validate='all', font='TkFixedFont',
                               validatecommand=(check_hex, '%P'))

            # place the entries appropriately
            self.e1.grid(row=2, column=1, sticky='nesw')
            self.e2.grid(row=3, column=1, sticky='nesw')

            # insert the initial value into the entry
            self.e1.insert(0, ' '.join([str(val) for val in source_data]))
            last_row = 4

        # buttons to save/cancel
        tk.Button(self, text='Cancel', justify='right', width=20, bg='red', fg='white',
                  command=self.destroy).grid(row=last_row)
        tk.Button(self, text='Save', justify='right', width=60, bg='green', fg='white',
                  command=self.save_result).grid(row=last_row, column=1, sticky='nesw')

        # expand to fill
        tk.Grid.columnconfigure(self, 1, weight=1)

        # key binding enter press = save
        self.bind('<Return>', self.save_result)
        # give focus to e0 if we are adding a new property
        if len(self.path[1]) == 0:
            self.e0.focus()

    def check_name(self, new_str):
        # always has to start with the same thing
        if not new_str.startswith(self.path[0]):
            return False

        new_str = new_str.replace(self.path[0], '', 1)

        # has to contain valid characters
        PROP_ALLOWED_CHARS = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        PROP_ALLOWED_CHARS += ',._+?#-'
        return all([c in PROP_ALLOWED_CHARS for c in new_str])

    def check_hex(self, new_str, max_val):
        if self.ignore_change:
            return True

        res = check_data_nbr(new_str, max_val, base=16)

        if res is None:
            # parse error = invalid
            return False

        self.ignore_change = True
        self.e1.delete(0, tk.END)
        self.e1.insert(0, ' '.join([str(val) for val in res]))
        self.ignore_change = False

        # validation passed
        self.currentValue = res
        return True

    def check_words_hex(self, new_str):
        # uint32 max is 4,294,967,295
        return self.check_hex(new_str, 4294967295)

    def check_bytes_hex(self, new_str):
        # byte max is 255
        return self.check_hex(new_str, 255)

    def check_dec(self, new_str, max_val):
        if self.ignore_change:
            return True

        res = check_data_nbr(new_str, max_val, base=10)

        if res is None:
            # parse error = invalid
            return False

        self.ignore_change = True
        self.e2.delete(0, tk.END)
        self.e2.insert(0, ' '.join([format(val, 'x') for val in res]))
        self.ignore_change = False

        # validation passed
        self.currentValue = res
        return True

    def check_words_dec(self, new_str):
        # uint32 max is 4,294,967,295
        return self.check_dec(new_str, 4294967295)

    def check_bytes_dec(self, new_str):
        # byte max is 255
        return self.check_dec(new_str, 255)

    def save_result(self, _=None):
        name_result = self.e0.get()

        # cannot make the name empty
        if len(name_result.replace(self.path[0], '', 1)) == 0:
            tk.messagebox.showerror('Invalid input', 'Property name cannot be empty!')
            return

        try:
            # save the main result
            self.result = commit_result(self.currentValue, self.itemType == dt.FdtPropertyType.STRINGS, self.e1)
            if self.result == self.initialValue:
                # we basically didn't make a change
                self.result = None

            # save the name result, if applicable
            self.path[0] = self.path[0][:-1]
            if name_result != '/'.join(self.path):
                self.nameResult = name_result
            else:
                # no change in name
                self.nameResult = None

            # done!
            self.destroy()
        except Exception as ex:
            tk.messagebox.showerror('Invalid input', 'Could not parse input! Changes not saved. Error details:\n' +
                                    getattr(ex, 'message', str(ex)))


class DtbSmartEntry(tk.Entry):
    result = None
    value_set = False
    maxValue = 0
    currentValue = ''
    useHex = False
    rowid = ''
    path = ''
    item = None
    itemType = None
    initialValue = None

    def __init__(self, controller, parent, width, update_cb, next_cb, prev_cb):
        self.ve = parent.register(self.validate_entry)
        super().__init__(parent, width=width, validate='all', font='TkFixedFont',
                         validatecommand=(self.ve, '%P'), justify='left')

        # controller, for access to dtw class
        self.controller = controller

        # various callbacks used
        self.update_cb = update_cb
        self.next_cb = next_cb
        self.prev_cb = prev_cb

        # scroll to end
        super().xview_moveto(1)

        # give focus to this element
        self.focus_force()

        # configure convenience keybindings
        self.bind('<Shift-Tab>', self.on_backwards_tab)
        try:
            self.bind('<ISO_Left_Tab>', self.on_backwards_tab)
        except tk.TclError:
            # above key combination is only for Linux
            pass
        self.bind('<Tab>', self.on_tab)
        self.bind('<Return>', self.on_return)
        self.bind('<Escape>', self.on_esc)

    def set_value(self, rowid, path, item, view_format):
        # for some reason there seems to be a race condition where tk will set this entry to empty AFTER the
        # initialization code runs if the initialization code is in __init__ (what this means is that the entry is
        # randomly cleared). so, we move it to a separate function, which makes things more annoying to use, but should
        # *hopefully* fix the issue.

        # information
        self.maxValue = 0
        self.currentValue = ''
        self.useHex = False
        self.rowid = rowid
        self.path = path
        self.item = item
        self.itemType = item.get_type()
        self.initialValue = item.get_value()

        self.currentValue = item.get_value()

        if self.itemType == dt.FdtPropertyType.WORDS or self.itemType == dt.FdtPropertyType.BYTES:
            if self.itemType == dt.FdtPropertyType.WORDS:
                # uint32 max is 4,294,967,295
                self.maxValue = 4294967295
            else:  # pyfdt.FdtPropertyType.BYTES
                # byte max is 255
                self.maxValue = 255
            if view_format == 'hex':
                self.insert(0, ' '.join([format(val, 'x') for val in self.currentValue]))
                self.useHex = True
            else:
                self.insert(0, ' '.join([str(val) for val in self.currentValue]))
        elif self.itemType == dt.FdtPropertyType.STRINGS:
            self.currentValue = strarray_to_string(self.currentValue)
            self.insert(0, self.currentValue)

        self.value_set = True

    def validate_entry(self, new_str):
        if not self.value_set:
            # allow anything if there is no actual value set yet
            return True

        if self.itemType == dt.FdtPropertyType.STRINGS:
            # no validation yet
            return True
        elif self.itemType == dt.FdtPropertyType.EMPTY:
            # no value allowed
            return False

        res = check_data_nbr(new_str, self.maxValue, base=16 if self.useHex else 10)

        if res is None:
            # parse error = invalid
            return False

        self.currentValue = res
        return True

    def on_return(self, _=None):
        try:
            # save the main result
            self.result = commit_result(self.currentValue, self.itemType == dt.FdtPropertyType.STRINGS, self)
            if self.result == self.initialValue:
                # we basically didn't make a change
                self.result = None

            # done!
            self.destroy()
        except Exception as ex:
            tk.messagebox.showerror('Invalid input', 'Could not parse input! Changes not saved. Error details:\n' +
                                    getattr(ex, 'message', str(ex)))

        # we always destroy ourselves in the smartentry mode
        # this does mean that the user may lose some changes if the input was invalid
        self.destroy()
        self.update_cb(self.rowid, self.path, self.item)

    def on_esc(self, _=None):
        self.destroy()
        # don't call with any arguments = cancelled
        self.update_cb()

    def on_tab(self, _=None):
        self.on_return()
        self.next_cb()
        return 'break'

    def on_backwards_tab(self, _=None):
        self.on_return()
        self.prev_cb()
        return 'break'
