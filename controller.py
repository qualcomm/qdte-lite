# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
@file controller.py
This file contains the primary controller for the DTGUI application.

The main class in this file is the DTGUIController, which holds instances of the various other classes; given that
most classes are actually windows/views, the controller is the only component that actually knows whether components
are visible and has a variable representing them (i.e., is able to notify them of events). As a result, it serves as
the "proxy" (or handler) for all events that occur in the application. Since the DTGUIController holds the instance of
the DTWrapper (dtwrapper.py), it is the only class permitted to make changes to the DeviceTree. The EditView, TreeView,
etc., all simply take in the user's intention to make modifications to the DeviceTree and notify the controller of this
intention, so that the controller can pass the intent on to the DTWrapper.

Another example of the controller's proxying is when the user requests to highlight a path using the TreeView. The
TreeView will notify the controller of this intent and the controller will then propagate that information to the
HexWindow (if it is open) and the TreeView itself; note that the TreeView highlight event handler never directly calls
a TreeView function to highlight the path, and that all of this passes through the controller first.

There are probably better ways to structure this system, but I am not highly familiar with GUI programming models, so
this simple view/controller system was chosen since it seemed easiest to implement with Tkinter and seemed to make sense
in my mind.
"""

# python core libraries
import os
import re
import math
import multiprocessing as mp
import traceback
import time
import threading
import subprocess
import shutil
import json

# Main tkinter library
import sys
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog


# Windows/Views we use
from findview import FindWindow
from treeview import TreeView
from editview import EditDialog
from hexview import HexWindow

# configuration, debug, etc.
from flags import flags as gf
from flags import global_info as gl_info
from settings import Json_Operate
import dbgutil as dbg
import settings
import dtlogger

# packaging help
import package

# fdt interface
import dtwrapper as dt
import xblcfgint as xbl
from pyfdt import pyfdt
import Autocmd as cmd

#nhlos parser lib
import non_hlos_parser

import get_qsahara_files


QUTS_STATE = None
quts_path = None
if os.path.exists(gl_info["quts"]):
    quts_path = gl_info["quts"]
elif os.path.exists(gl_info["quts2"]):
    quts_path = gl_info["quts2"]
if quts_path and os.path.exists(os.path.join(quts_path,'Common','ttypes.py'))\
    and os.path.exists(os.path.join(quts_path,'ImageManagementService','ImageManagementService.py'))\
    and os.path.exists(os.path.join(quts_path,'ImageManagementService','ttypes.py')):
    sys.path.append(quts_path)
    try:
        import QutsAtom.Atom_ImageManagementService
        import QutsClient
        import Common.ttypes
        import ImageManagementService.ImageManagementService
        import ImageManagementService.ttypes
    except Exception as e:
        dtlogger.info(e)
        QUTS_STATE='old'
    else:
        QUTS_STATE="import"


# title and version
DTGUI_TITLE = 'QDTE (Qualcomm Device Tree Editor)'
DTGUI_VERSION = 'V1.5.7'
QDTE_ICON = "QDTE.png"
About_Info="""%s %s

Features Supported
    1. Load and Parse DTB files.
    2. Edit DTB Properties (double-click) and Save DTB.
    3. Add and remove nodes and properties.
    4. Read/Write DTB elf file from Local/Device.
    5. Edit Diassemble/Reassemble DTB elf.

Support: qdte.support@qti.qualcomm.com

Copyright(c) 2020-2024 Qualcomm Technologies, Inc.
 """ %(DTGUI_TITLE,DTGUI_VERSION)


class DTGUIController(tk.Frame,non_hlos_parser.nhlos_Operator):
    hexView = None
    hexViewShowing = None
    viewStyleHex = None
    viewStyleDec = None
    viewStyleIgnTrace = False
    findView = None
    knownHighlights = []
    editMenu = None
    lastFindOpts = None
    fdtModified = False
    xblDialog = None
    userFirstTimeXbl = True
    readDeviceDtbElf = False
    Nonhlosdtb = False

    def __init__(self, root, initial_file=None):
        """Initialize the DTGUIController

        This function initializes all of the variables and views in the DTGUIController and calls various other internal
        helper functions to initialize the menu bar and catch key bindings.

        :param root: The root tk.Tk() object
        :param initial_file: The initial file to edit. Defaults to None, in which case the editor will be blank.
        """

        super().__init__()
        self._root = root
        icon_path = None
        if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)),QDTE_ICON)):
            icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),QDTE_ICON)
        elif os.path.exists(os.path.join(gl_info["sign_json_path"],QDTE_ICON)):
            icon_path = os.path.join(gl_info["sign_json_path"],QDTE_ICON)
        if icon_path!= None:
            self._root.icon = tk.PhotoImage(file = icon_path)
            self._root.iconphoto(True,self._root.icon)
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self._root.geometry("+%d+%d" % ((screenwidth-1100)/2, (screenheight-700)/2))
        
        # qdte logger initialization
        logger_file = os.path.join(gl_info['log'],"log.txt")
        dtlogger.logger_init(log_file=logger_file)
        
        # DTWrapper initialization
        self.dtw = dt.DTWrapper()

        # initialize components of the main controller
        self.treeView = TreeView(self._root, self)
        self._init_menus()
        self._init_key_bindings()
        self.treeView.pack(fill='both', expand=True)

        # open the initial file, if given
        self._update_title()
        self._root.geometry("+%d+%d" % ((screenwidth-1100)/2, (screenheight-700)/2))
        if initial_file is not None:
            ext = initial_file.rsplit('.elf', 1)
            if initial_file.lower().endswith('.elf'):
                self.open_xblfile(xbl_fn=initial_file)
                pass
            else:
                self._update_view_file(initial_file)

        # catch window close
        self._root.protocol('WM_DELETE_WINDOW', self.on_close)

    def _init_menus(self):
        """Initialize menu bar items"""

        # top level items
        menu_bar = tk.Menu(self._root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu = tk.Menu(menu_bar, tearoff=0)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='File', menu=file_menu)
        menu_bar.add_cascade(label='Edit', menu=edit_menu)
        menu_bar.add_cascade(label='View', menu=view_menu)
        menu_bar.add_command(label='Setting', command=self.Settings_gui)
        menu_bar.add_cascade(label='Help', menu=help_menu)
        self._root.config(menu=menu_bar)

        # help menu items
        help_menu.add_command(label='About...', compound='left', underline=0,
                              command=self.show_about)
        help_menu.add_command(label='User Manual...', compound='left', underline=0, command=self.open_manual)

        # view menu items
        self.hexViewShowing = tk.BooleanVar()
        if gf['test']:
            self.hexViewShowing.set(True)
            self.show_hexview()
        else:
            self.hexViewShowing.set(False)
        self.hexViewShowing.trace('w', self.show_hexview)
        view_menu.add_checkbutton(label='Raw', variable=self.hexViewShowing)
        view_menu.add_separator()
        # default to show hex value
        self.viewStyleHex = tk.BooleanVar()
        self.viewStyleHex.set(gf['viewAsHex'])
        self.viewStyleHex.trace('w', self.change_viewstyle)
        self.viewStyleDec = tk.BooleanVar()
        self.viewStyleDec.set(not gf['viewAsHex'])
        self.viewStyleDec.trace('w', self.change_viewstyle)
        view_style_menu = tk.Menu(view_menu, tearoff=0)
        view_style_menu.add_checkbutton(label='Hexadecimal', onvalue=1, offvalue=0, variable=self.viewStyleHex)
        view_style_menu.add_checkbutton(label='Decimal', onvalue=1, offvalue=0, variable=self.viewStyleDec)
        view_menu.add_cascade(label='Values As...', menu=view_style_menu, underline=0)
        view_menu.add_separator()
        view_menu.add_command(label='Clear Highlights', command=self.clear_highlights)
        view_menu.add_separator()
        view_menu.add_command(label='Expand All Nodes', accelerator='Ctrl+E', command=self.treeView.expand_all_items)
        view_menu.add_command(label='Collapse All Nodes', accelerator='Ctrl+D',
                              command=self.treeView.collapse_all_items)

        # edit menu items
        # NB: will need to adjust the update_undoredo() function if the order/position of undo/redo is changed here
        edit_menu.add_command(label='Undo', accelerator='Ctrl+Z', command=self.undo)
        edit_menu.add_command(label='Redo', accelerator='Ctrl+Shift+Z', command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label='Find...', accelerator='Ctrl+F', command=self.find_popup)
        edit_menu.add_command(label='Find Next', accelerator='F3', command=self.find_next)
        # edit_menu.add_separator()
        # edit_menu.add_command(label='Preferences...')
        self.editMenu = edit_menu
        self.update_undoredo()

        # file menu items
        if gf['test']:
            file_menu.add_command(label='New Window...', command=self.open_file_new_win)
            file_menu.add_separator()
        file_menu.add_command(label='Open DTB...', accelerator='Ctrl+O', compound='left', underline=0,
                              command=self.open_file)
        xbl_cfg_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label='Open DTB Elf', menu=xbl_cfg_menu, underline=0)
        xbl_cfg_menu.add_command(label='From Build', command=self.open_build_dtb_elf)
        xbl_cfg_menu.add_separator()
        xbl_cfg_menu.add_command(label='From Device', command=self.open_device_dtb_elf)
        file_menu.add_command(label='Write DTB Elf', compound='left', underline=0, command=self.write_dtb_elf_file)

        # file_menu.add_command(label='Open XBLConfig...', accelerator='Ctrl+Shift+O', compound='left', underline=0,
        #                       command=self.open_build_dtb_elf)
        file_menu.add_command(label='Reload File', command=self.reload_file)
        file_menu.add_separator()
        file_menu.add_command(label='Save', accelerator='Ctrl+S', command=self.save_file)
        file_menu.add_command(label='Save Copy As...', accelerator='Shift+Ctrl+S', command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label='Export Change Report...', command=self.change_report)
        file_menu.add_command(label='Export to DTS...', compound='left', underline=0, command=self.export_dts)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.on_close)

        # debug menu items
        self.viewReadOnly = tk.BooleanVar()
        self.viewReadOnly.set(False)
        self.viewReadOnly.trace('w', self.update_readonly)

        if gf['debug']:
            debug_menu = tk.Menu(menu_bar, tearoff=0)
            menu_bar.add_cascade(label='Debug', menu=debug_menu)
            debug_menu.add_checkbutton(label='Read Only', variable=self.viewReadOnly)
            debug_menu.add_command(label='Import Journal....', command=self.import_cr)
            if gf['profileMem']:
                debug_menu.add_command(label='Trace memory usage', accelerator='Shift+Ctrl+M',
                                       command=lambda _=None: dbg.display_mem_usage())


    def Settings_gui(self):
        self.settings = settings.Settings(self._root, settings.ITEMS_ALL)


    def _init_key_bindings(self):
        """Initialize various key bindings for the controller"""

        # file menu
        # self._root.bind('<Control-o>', self.open_file)
        # self._root.bind('<Control-O>', self.open_build_dtb_elf)
        # self._root.bind('<Control-s>', self.save_file)
        # self._root.bind('<Control-S>', self.save_as)
        # edit menu
        self._root.bind('<Control-z>', self.undo)
        self._root.bind('<Control-Z>', self.redo)
        self._root.bind('<Control-f>', self.find_popup)
        self._root.bind('<F3>', self.find_next)
        # view menu
        self._root.bind('<Control-e>', self.treeView.expand_all_items)
        self._root.bind('<Control-d>', self.treeView.collapse_all_items)
        if gf['debug']:
            # debug menu
            if gf['profileMem']:
                self._root.bind('<Control-M>', lambda _=None: dbg.display_mem_usage())

    def _update_views(self, path=None, fdtModified=True):
        """Internal helper function to update the TreeView and HexView when changes have occurred.

        This function is called whenever changes have been made to the DeviceTree and the TreeView, HexView, and window
        title need to be updated. A path, or multiple, can be specified, which will constrain the scope of updates and
        can help the program run more efficiently and avoid losing state information. This function calls the TreeView
        update_fdt() function and the Hexview update_view() functions, and also updates the window title and undo/redo
        stack information.

        :param path: The paths that were updated. Not specifying this will result in the default value of None, which
                     will refresh the entire view, which may be undesirable in some cases. This parameter can be a
                     string of a single path that was modified, or it can also be a list of strings of paths that have
                     been modified.
        :param fdtModified: Whether or not the fdt has been modified since the last save. If this value is True, then
                            an asterisk will appear next to the window title. Defaults to True.
        :return:
        """

        # update the title
        self.fdtModified = fdtModified
        self._update_title()
        self.update_undoredo()

        if isinstance(path, list):
            # support updating a list of paths if necessary
            for p in path:
                self.treeView.update_fdt(p)
        else:
            self.treeView.update_fdt(path)

        # tell the hexview to update
        if self.hexViewShowing.get():
            self.hexView.update_view()

    def _update_view_file(self, new_filename=None):
        """Update the file that is currently being edited in the DTGUIController

        This file calls into the DTWrapper to apply a new Load DTOperation and open a given file.

        :param new_filename: The new filename to open, or None to close the existing file without opening a new one
        :return: whether the new file was successfully opened
        """

        if new_filename and not os.path.exists(new_filename):
            tk.messagebox.showerror('File not found', 'Could not open file ' + new_filename)
            return False

        # read and parse the bytes
        self._root.config(cursor='watch')
        self._root.update()
        try:
            if new_filename:
                self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.LOAD, new_filename))
            else:
                self.dtw.reset()
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            # throw an error if there is an invalid file
            tk.messagebox.showerror('File read error', 'Could not open file ' + new_filename +
                                    ':\n' + getattr(ex, 'message', repr(ex)))
            self._root.config(cursor='')
            return False
        self._root.config(cursor='')

        # Everything worked!
        self.knownHighlights = []
        self._update_views(fdtModified=False)
        return True

    def _update_title(self):
        """Update the window title with the currently open filename and asterisk if changes have been made"""

        title_str = ''
        if self.dtw.fdt_name is not None:
            title_str += '*' if (not self.xblDialog) and self.fdtModified else ''
            title_str += os.path.basename(self.dtw.fdt_name)
            title_str += ' - '
        #title_str += 'devicetree DTB viewer/editor '
        title_str += DTGUI_TITLE
        title_str += DTGUI_VERSION
        self._root.title(title_str)

    def check_python(self):
        try:
            proc = subprocess.Popen(["python",                                 
                                 '--version'
                                 ],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
                                 #universal_newlines=True,
                                 #shell=True)
        
            while True:
                outs, errs = proc.communicate()
                output=None
                dtlogger.debug("out:{} errs:{}".format(outs,errs))

                if len(outs) == 0 and len(errs) != 0:
                    output = errs
                else:
                    output = outs
                if output!=None:
                    if isinstance(output,bytes):
                        output=output.decode()
                    for line in output.split('\n'):
                        if isinstance(line,bytes):
                            line = line.decode()
                        line = line.strip("\r\n")
                        line = line.strip("\r")
                        dtlogger.debug("out line:{}".format(line))
                        if  line.lower().find('Python was not found'.lower())!=-1 or r"'python' is not recognized" in line:
                            dtlogger.debug("Error: Python is not installed. Please install python v3.7.x or later!")
                            tkinter.messagebox.showerror("Python is not installed","Please install python v3.7.x or later!\n")
                            return False
                        else:
                            if 'Python' in line or "python" in line:
                                python_version = line.split(' ')[1]
                                if int(python_version.split('.')[0]) >= 3 and int(python_version.split('.')[1]) >= 7:
                                    return True
                                else:
                                    tkinter.messagebox.showerror("Python Error", "Please install python v3.7 or later!\n")
                                    return False
                return_value = proc.poll()
                if return_value!=None and return_value!=9009:
                    dtlogger.debug("sub process has been terminate:{}".format(proc.poll()))
                    break
                elif return_value == 9009:
                    tkinter.messagebox.showerror("Python is not installed","Please install python v3.7.x or later!\n")
                    return False
        except Exception as Error:
            dtlogger.debug("Errors1:{}".format(Error))
            return False
        return True

    def check_quts(self):
        if QUTS_STATE == 'old':
            tkinter.messagebox.showerror(title="QUTS Error", message="Please install the latest QUTS from QPM\n")
            return False
        elif QUTS_STATE == None:
            tkinter.messagebox.showerror('Warning', "Please install QUTS to enable this function")
            return False
        else:
            return True

    def on_close(self, _=None):
        """Handler to prompt the user to save changes before closing the DTGUI application.

        :param _: ignored
        """

        if not self.xblDialog and self.fdtModified:
            r = tk.messagebox.askyesnocancel('Save changes', 'Save changes before quitting?', icon='warning')
            if r:
                # yes = save changes, then continue
                self.save_file()
            if r is None:
                # cancel = do not do anything
                return

        if self.xblDialog:
            # cleanup & close existing xbl file
            if not self.xblDialog.cleanup_and_close():
                # user cancelled closing
                return
            self.xblDialog = None

        self._root.destroy()

    def open_file(self, _=None, new_filename=None):
        """Callback for when the user expresses an intent to open a DTB file

        This function ensures that the user has saved all changes and then calls _update_view_file() to open a new file.

        :param _: ignored (sometimes it is a tkinter event)
        :param new_filename: New filename to open. Defaults to None, in which case the user will be prompted with a
                             dialog box to pick the path to the new file to open.
        :return: Whether or not opening the new file was successful
        """

        if not self.xblDialog and self.fdtModified:
            # prompt user if they have unsaved changes (only do this if there is no XBLConfig DTB open)
            r = tk.messagebox.askyesnocancel('Save changes', 'Save changes before opening new file?', icon='warning')
            if r:
                # yes = save changes, then continue
                self.save_file()
            if r is None:
                # cancel = do not do anything
                return False

        # get the new filename
        if not new_filename:
            if self.xblDialog:
                # cleanup & close existing
                if not self.xblDialog.cleanup_and_close():
                    # user cancelled closing
                    return False
                self.xblDialog = None

            new_filename = tk.filedialog.askopenfilename(defaultextension='.dtb',
                                                         filetypes=[('Device Tree Blob', '*.dtb'),
                                                                    ('Device Tree Blob', '*.dtbo'),
                                                                    ('All Files', '*.*')])
        if new_filename:
            return self._update_view_file(new_filename)
        return False

    def open_file_new_win(self, _=None):
        """Open a file in a new instance of the DTGUI. Experimental and probably doesn't work.

        :param _: ignored
        """

        _ = self
        # get the new filename
        new_filename = tk.filedialog.askopenfilename(defaultextension='.dtb',
                                                     filetypes=[('Device Tree Blob', '*.dtb'),
                                                                ('All Files', '*.*')])
        if new_filename:
            # start a new process
            p = mp.Process(target=run, kwargs={'initial_file': new_filename})
            p.start()

    def open_build_dtb_elf(self):
        """Callback when the user expresses intent to open an XBLConfig file.

        This function validates the XBLConfig setup to ensure that XBLConfig integration is enabled, prompts the user to
        pick an XBLConfig file to open (if none is specified), and then calls into the xblcfgint.py XblCfgGUI helper
        class/window to disassemble the XBLConfig, etc.

        :param _: ignored (sometimes it is a Tkinter event)
        :param xbl_fn: filename/path to the XBLConfig file. Defaults to None, in which case the user will be prompted
                       for the filename to open.
        """
        if self.check_python() == False:
            return False

        if not gf['xblEnabled']:
            tk.messagebox.showerror('XBLConfig integration disabled', 'XBLConfig integration has been disabled. Please '
                                                                      're-run the program and ensure that the '
                                                                      '--xbltools_dir path has been specified and that '
                                                                      'either --sectools_dir has been given, or '
                                                                      '--allow_unsigned is enabled.\n'
                                                                      'For more help, please run the program with the '
                                                                      '--help flag.')
            return

        if self.xblDialog:
            # cleanup & close existing
            if not self.xblDialog.cleanup_and_close():
                # user cancelled closing
                return
            self.xblDialog = None
        elif self.fdtModified:
            # prompt user if they have unsaved changes
            r = tk.messagebox.askyesnocancel('Save changes', 'Save changes before opening new file?', icon='warning')
            if r:
                # yes = save changes, then continue
                self.save_file()
            if r is None:
                # cancel = do not do anything
                return

        self._update_view_file(None)
        tmp_thread = threading.Thread(target=self.call_tmp_thread, name="Tmp Thread")
        tmp_thread.setDaemon(True)
        tmp_thread.start()

    def call_tmp_thread(self):
        gf['XBLConfigFlag'] = 0
        if self.readDeviceDtbElf == False:
            xbl.XblDirGUI(self._root)
            while(gf['XBLConfigFlag'] == 0):
                time.sleep(0.2)
        
        if (gf['XBLConfigFlag'] == 1 and gf['inputFile']) or (self.readDeviceDtbElf == True):
            xbl_fn = gf['inputFile']
        elif gf['XBLConfigFlag'] == 255:
            return

        self.readDeviceDtbElf = False
        # open the new dialog with the filename
        self.xblDialog = xbl.XblCfgGUI(self._root, self, xbl_fn)

    def write_dtb_elf_file(self):
        if self.check_quts() == False:
            return False

        tmp_thread = threading.Thread(target=self.call_write_dtb_elf_thread, name="Write Thread")
        tmp_thread.setDaemon(True)
        tmp_thread.start()

    def write_parition(self,partition_info):
        dataChunkOptionList = []
        dataChunkOptionList.append(ImageManagementService.ttypes.DataChunkOptions(
            partition_info["lun"], partition_info["s_lba"], partition_info["cnt"], partition_info["image"]))
        resu = QutsAtom.Atom_ImageManagementService.writePartitionData(self.dev_handle, dataChunkOptionList)
        return resu

    def call_write_dtb_elf_thread(self):
        self.dt_dict = {}
        self.dev_handle = None
        # get partition info from device
        gf['devprg'] = ""
        gf['setting_flag'] = 0
        settings.Settings(self._root,settings.ITEMS_DEVPRG)
        while(gf['setting_flag'] == 0):
            time.sleep(0.2)
        if gf['setting_flag'] == 255:
            return False
        while self.get_dev_partitioninfo() == 2:
            time.sleep(0.1)
        if not self.dt_dict:
            return False

        # write partition image
        flash_info = {}
        gf['PartitionName'] = ""
        gf['PartitionImage'] = ""
        gf['PartitionImage_Flag'] = 0
        xbl.DT_Write_GUI(self._root, self.dt_dict)
        while(gf['PartitionImage_Flag'] == 0):
            time.sleep(0.2)
        if gf['PartitionImage_Flag'] == 255:
            return False

        prog_win = xbl.DT_ProgressBar(self._root)
        time.sleep(0.5)
        dtlogger.debug(gf['PartitionName'][:-2])
        dtlogger.debug(gf['PartitionName'].split('_'))
        dtlogger.debug(gf['PartitionABCheck'])

        A_B_POSTFIX=["_a","_b"]
        BACKUP_POSTFIX=["","_BACKUP"]
        partition_postfix = ''
        # POSTFIX_list=[]
        # write_partititon_list=[]
        partition_postfix_regex="(_((BACKUP){1}|(a|b){1})){1}$"
        m = re.search(partition_postfix_regex,gf['PartitionName'],re.I)
        if m:
            partition_postfix = m.group(0)

        # write subsystem DTB elfs into non-hlos.bin
        #if partition_postfix in BACKUP_POSTFIX:
        if self.dt_dict[gf['PartitionName']]["container"] !=None:
            self.write_dtb_elf_into_nhlos_file(self.dt_dict[gf['PartitionName']]["name"], 
                                             os.path.join(gl_info["tmp_xblcfg"],self.dt_dict[gf['PartitionName']]["container"]+".bin"),
                                             gf['PartitionImage'],
                                             gl_info["tmp_xblcfg"])


        #write dtb elfs or non-hlos.bin into corresponding paritons. 
        flash_partition_list = [gf['PartitionName']]
        # check if needs to write into A&B partition.
        if gf['PartitionABCheck'] == 1:
            partition_list = [item for item in self.dt_dict]
            partition_root_name = self.dt_dict[gf['PartitionName']]["name"].rstrip(partition_postfix)
            flash_partition_list = [x for x in partition_list if (partition_root_name in x)]

        #write dtb elfs or non-hlos.bin into paritons. 
        for Partition_name in flash_partition_list:
            if Partition_name not in self.dt_dict:
                dtlogger.debug("partition can't be found!")
            #if container exists, that means dtb elf is in nhlos binary
            if self.dt_dict[Partition_name]["container"]!=None:
                flash_info["partition"] = self.dt_dict[Partition_name]["container"]
                flash_info["image"] = os.path.join(gl_info["tmp_xblcfg"],self.dt_dict[gf['PartitionName']]["container"]+".bin")
            else:
                flash_info["partition"] = Partition_name
                flash_info["image"] = gf['PartitionImage']

            flash_info["lun"] = self.dt_dict[Partition_name]["lun"]
            flash_info["s_lba"] = self.dt_dict[Partition_name]["s_lba"]
            flash_info["cnt"] = self.dt_dict[Partition_name]["cnt"]
            
            resu = self.write_parition(flash_info)
            if resu:
                prog_win.call_popup_close()
                dtlogger.debug("Can't flash image %s to device." % flash_info["partition"])
                tkinter.messagebox.showerror('Error', "Can't flash image %s to device" % flash_info["partition"])
                return False
        prog_win.call_popup_close()
        if len(flash_partition_list)==2:
            dtlogger.debug("Flash image into {} & {} Successfully".format(flash_partition_list[0],flash_partition_list[1]))
            tkinter.messagebox.showinfo('Success', "Flashed {} to A&B partitions!".format(gf['PartitionName']))
        else:
            dtlogger.debug("Flash image into {} Successfully".format(flash_partition_list[0]))
            tkinter.messagebox.showinfo('Success', "Flashed {} to device!".format(gf['PartitionName']))

    def open_device_dtb_elf(self):
        if self.check_python() == False:
            return False
        if self.check_quts() == False:
            return False
        
        self.tmp_thread = threading.Thread(target=self.call_device_dtb_elf_thread, name="Dev XblCfg Thread")
        self.tmp_thread.setDaemon(True)
        self.tmp_thread.start()

    # read dtb elf file from partition of device
    def read_partition_from_device(self,partition_inf,output_file):
        dataChunkOptions = []
        dataChunkOptions.append(ImageManagementService.ttypes.DataChunkOptions(
            partition_inf["lun"], partition_inf["s_lba"], partition_inf["cnt"], output_file))
        resu = QutsAtom.Atom_ImageManagementService.readPartitionData(self.dev_handle, dataChunkOptions)
        if resu or not os.path.exists(output_file):
            dtlogger.debug("Can't get partition image from device.")
            tkinter.messagebox.showerror('Error', "Can't get partition image from device")
            return False



    def call_device_dtb_elf_thread(self):
        self.dt_dict = {}
        self.dev_handle = None

        # get partition info from device
        gf['devprg'] = ""
        gf['setting_flag'] = 0
        settings.Settings(self._root,settings.ITEMS_DEVPRG)
        while(gf['setting_flag'] == 0):
            time.sleep(0.2)
        if gf['setting_flag'] == 255:
            return False
        while self.get_dev_partitioninfo() == 2:
            time.sleep(0.1)
        if not self.dt_dict:
            return False

        # delete the old xbl cfg file
        #shutil.rmtree(gl_info["tmp_xblcfg"])

        # get partition image from device
        gf['partition_name'] = ""
        gf['partition_name_flag'] = 0
        xbl.DT_Select_GUI(self._root, self.dt_dict)
        while(gf['partition_name_flag'] == 0):
            time.sleep(0.2)
        if gf['partition_name_flag'] == 255:
            return False

        readDir = gl_info["tmp_xblcfg"]
        parti_name = gf['partition_name']
        image_name = self.dt_dict[parti_name]["name"]+".elf"

        if self.dt_dict[parti_name]['container'] == None:
            if self.read_partition_from_device(self.dt_dict[parti_name],os.path.join(readDir, image_name)) == False:
                return False
        else:
            self.extract_dtb_elf_file(self.dt_dict[parti_name]["name"],os.path.join(gl_info["tmp_xblcfg"],self.dt_dict[parti_name]["container"]+".bin"),readDir)
       
        gf["inputFile"] = os.path.join(readDir, image_name)
        self.jsonx = Json_Operate()
        self.jsonx.update_json_cfg_data()

        # open and edit xbl cfg file
        self.readDeviceDtbElf = True
        self.open_build_dtb_elf()

    def get_dev_partitioninfo(self):
        if self.check_quts() == False:
            return False
        prog_win = xbl.DT_ProgressBar(self._root)
        memoryTypes = {
            "EMMC"  :0,
            "UFS"   :1,
            "NAND"  :2,
            "NVME"  :3,
            "SPINOR":4
        }
        # get xbl cfg partition
        try:
            client = QutsClient.QutsClient("ImageInfo")
            devMgr = client.getDeviceManager()
            deviceList = devMgr.getDeviceList()
            dtlogger.debug(deviceList)
            self.dev_handle = None
            for device in deviceList:
                for protocol in device.protocols:
                    dtlogger.debug("Protocol:{}{}".format( protocol.description, protocol.protocolType))
                    #if(Common.ttypes.ProtocolType.PROT_SAHARA == protocol.protocolType):
                    if '9008' in protocol.description:
                        self.dev_handle = device.deviceHandle
                        dtlogger.debug("Protocol:{}".format( protocol.description))
                        dtlogger.debug("DeviceHandle: {}".format(self.dev_handle))
                        break
                if self.dev_handle != None:
                    break
        except Exception as e:
            dtlogger.debug(e)


        if not self.dev_handle:
            dtlogger.debug("Can't get the device handle. Please boot to EDL mode first.")
            prog_win.call_popup_close()
            rst = tkinter.messagebox.askretrycancel(
                title="Retry or Cancel", message="Can't get the device handle.\n\nPlease ensure device is in EDL mode \n QPCAT/QUT is closed and retry.")
            if rst:
                return 2
            else:
                return False
        
        buildOption = None
        Qsahara_files = get_qsahara_files.get_all_sahara_files(gf["devprg"],storage=gf['flashtype'].lower())
        devprg_file = None
        Qsahara_files_list = {}
        if Qsahara_files == None:
            prog_win.call_popup_close()
            tkinter.messagebox.showerror('Error', "Can't get dev programmer file!")
            return False

        if len(Qsahara_files) == 1:
            if isinstance(Qsahara_files, list):
                devprg_file = Qsahara_files[0]
            elif isinstance(Qsahara_files, dict):
                for key,val in Qsahara_files.items():
                    devprg_file = Qsahara_files[key]
            else:
                dtlogger.debug("Qsahara file return value is incorrect with {}".format(type(Qsahara_files)))
                return False
            buildOption = ImageManagementService.ttypes.DownloadBuildOptions(
                memoryType=memoryTypes[gf['flashtype']], firehoseProgPath=devprg_file)
        else:
            for key, values in Qsahara_files.items():
                Qsahara_files_list[int(key)]=Qsahara_files[key][0]
            buildOption = ImageManagementService.ttypes.DownloadBuildOptions(
                memoryType=memoryTypes[gf['flashtype']], saharaImageList=Qsahara_files_list)
    
        buildOption.partitionIndexList = []
        buildOption.readImages = True
        buildOption.readImagesPath = gl_info["tmp_xblcfg"]

        partitionTable = []
        try:
            partitionTable = QutsAtom.Atom_ImageManagementService.initPartitionTable(self.dev_handle, buildOption)
        except Exception as e:
            dtlogger.debug("Exception of getting partition table:{}".format(e))
            dtlogger.info("Exception of getting partition table:{}".format(e))
            prog_win.call_popup_close()
            tkinter.messagebox.showerror('Error', "Exception of getting partition table")
            return False
        if not partitionTable:
            dtlogger.debug("Can't get the partition table. Please boot to EDL mode, select correct flash type and try again.")
            prog_win.call_popup_close()
 
            rst = tkinter.messagebox.askretrycancel(
                title="Retry or Cancel", message="Can't get the partition table.\n\nPlease boot to EDL mode and retry.")
            if rst:
                return 2
            else:
                return False

        self.dt_dict.clear()
        partitionName = {}
        partitionPath = './partition_name.json'
        partitionJson = xbl.Json_Partition_Operate(partitionPath)
        partitionName = partitionJson.read_json_partition_data()
        if partitionName:
            dt_pattern = re.compile(r"%s" % (partitionName["partition"]), flags=re.I)
            if partitionName["partitionBan"] != "":
                dt_pattern_ban = re.compile(r"%s" % (partitionName["partitionBan"]), flags=re.I)
        else:
            prog_win.call_popup_close()
            # tkinter.messagebox.showerror(title="Error", message="Can't get the partition format.\n\nPlease generate info in json file and retry.")
            return False
        #dtlogger.info("all the partitionTable: ",partitionTable)

        #NHLOS_name_regex = "^(NHLOS|modem|BOOT_FW1|BOOT_FW2){1}(_(BACKUP{1}|(a|b|A|B){1}){1})?$"
        NHLOS_name_regex = "^(NHLOS|modem){1}(_(BACKUP{1}|(a|b|A|B){1}){1})?$"
        for partition in partitionTable:
            q6_dtb_name = None
            #if it's NHLOS , read out NHLOS.bin from device.
            m = re.search(NHLOS_name_regex,partition.name)
            if m:
                partition_info={}
                partition_info["name"]= partition.name
                partition_info["lun"] = partition.lun
                partition_info["s_lba"] = str(partition.startingLba)
                partition_info["cnt"] = str(partition.endingLba-partition.startingLba+1)

                # read NHLOS.bin from device
                if self.read_partition_from_device(partition_info, os.path.join(gl_info["tmp_xblcfg"],partition.name+".bin"))==False:
                    return False

                # fetch DTB_elf files name from nhlos binary file
                self.get_dtb_elf_names(os.path.join(gl_info["tmp_xblcfg"],partition.name+".bin"))

                # get partition postfix, like _A/_B or _BACKUP  
                parition_index = ""
                if m.group(2):
                    parition_index = m.group(2)

                dtlogger.debug("NHLOS dtb elf:{}".format(self.dtb_files_name))
                if self.dtb_files_name:
                    for q6_dtb_name in self.dtb_files_name:
                        q6_dtb=q6_dtb_name+parition_index
                        self.dt_dict[q6_dtb] = {}
                        self.dt_dict[q6_dtb]["name"] = q6_dtb_name
                        self.dt_dict[q6_dtb]["lun"] = partition.lun
                        self.dt_dict[q6_dtb]["s_lba"] = str(partition.startingLba)
                        self.dt_dict[q6_dtb]["cnt"] = str(partition.endingLba-partition.startingLba+1)  
                        self.dt_dict[q6_dtb]["container"] = partition.name

            dt_list = dt_pattern.findall(partition.name)
            dt_list_ban = []
            if partitionName["partitionBan"] != "":
                dt_list_ban = dt_pattern_ban.findall(partition.name)
            if dt_list and not dt_list_ban:
                self.dt_dict[partition.name] = {}
                self.dt_dict[partition.name]["name"] = partition.name
                self.dt_dict[partition.name]["lun"] = partition.lun
                self.dt_dict[partition.name]["s_lba"] = str(partition.startingLba)
                self.dt_dict[partition.name]["cnt"] = str(partition.endingLba-partition.startingLba+1)
                self.dt_dict[partition.name]["container"] = None
        if not self.dt_dict:
            dtlogger.debug("Can't get partition info from device.")
            prog_win.call_popup_close()
            tkinter.messagebox.showerror(title="Error", message="Can't get partition info from device\n")
            return False

        prog_win.call_popup_close()
        dtlogger.debug("dt partition info: {}".format( str(self.dt_dict)))

    def on_xbldialog_close(self):
        """Callback when the XBLConfig dialog is closed that will clear the currently edited file since the handle to it
        is not longer valid (the file is being edited from a temporary directory that only exists while the XBLConfig
        window is open)."""

        self.xblDialog = None
        self._update_view_file(None)

    def reload_file(self, _=None):
        """Reload the file currently in the view

        This function re-reads the file currently displayed in the GUI from the disk. Undo history and the state of the
        tree view are reset.

        :param _: ignored
        """

        # disabled if we are in XBLConfig integration mode
        if self.xblDialog:
            tk.messagebox.showerror('Cannot reload DTB in XBLConfig', 'Sorry, it is not possible to reload a DTB file '
                                                                      'inside of an XBLConfig ELF.')
            return

        # just call update view again
        if self.fdtModified:
            if not tk.messagebox.askokcancel('Unsaved changes', 'You have unsaved changes, and reloading the file will '
                                                                'lose them. Proceed?', icon='warning'):
                return
        self.fdtModified = False
        self._update_view_file(self.dtw.fdt_name)

    def show_about(self, _=None):
        """Show a dialog with information about the program

        :param _: ignored
        """

        # msg = 'devicetree DTB viewer/editor ' + DTGUI_VERSION + '\n'
        # if self.dtw.fdt_name is not None:
        #     msg += 'Currently editing ' + self.dtw.fdt_name + '\n'
        # msg += ('Core Platform Boot go/vtechstudy Assignment: \n\nMar-Apr 2020 : TKinter Internals to'
        #         ' create quick cross platform python GUI front-end \n\n             devicetree DTB '
        #         'viewer/editor'
        #         '\n                                 By Dhamim P\n\n'
        #         '\n Features Supported \n1. Load and Parse DTB files \n2. Edit DTB Properties '
        #         '(double-click) and Save DTB\n'
        #         '3. Add and remove nodes and properties\n'
        #         '\nMay-Aug 2020 : Extended by Mason Xiao'
        #         )
        tk.messagebox.showinfo('About', About_Info)

    def open_manual(self):
        """Display the user manual PDF"""

        _ = self
        user_manual = package.fetch_resource('UserManual.pdf')
        if user_manual is None:
            tk.messagebox.showerror('User Manual Not Found', 'The user manual has not been bundled with this version of'
                                                             ' the QDTE.')
            return
        if sys.platform == 'win32':
            os.startfile(user_manual)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', user_manual])
        else:
            try:
                import subprocess
                subprocess.Popen(['xdg-open', package.fetch_resource('UserManual.pdf')])
            except OSError:
                tk.messagebox.showinfo('User Manual', 'Please consult the file %s for more information.' % user_manual)

    def change_report(self):
        """Save a JSON report of all of the changes made to a file

        This function prompts the user for a file to save the change report to, then calls into the DTWrapper to
        generate the report itself, and finally saves the changes into the file that the user specified.
        """

        # get the new filename
        new_filename = tk.filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON file', '*.json'),
                                                                                            ('All Files', '*.*')])

        if not new_filename:
            return

        try:
            # try to generate report
            report = self.dtw.report()
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to save change report', 'Encountered error while attempting to save change '
                                                                    'report:\n' + getattr(ex, 'message', str(ex)))
            return

        # write out the file
        with open(new_filename, 'wb') as outfile:
            outfile.write(report.encode())

    def get_changes(self, pyobj=False):
        """Get a list of all of the changes made to the DTB currently being edited.

        :param pyobj: Parameter passed directly on to the DTWrapper report() function; if it is True, then the return of
                      this function will be a Python object, if it is False, then the return of this function will be a
                      JSON string. Defaults to False (return JSON string).
        :return: Python object or string, depending on the value of pyobj.
        """
        return self.dtw.report(pyobj)

    def import_cr(self):
        """Function to prompt the user to import a change report into the DTWrapper

        This function is used as part of the testing mode in order to make testing the program's correctness slightly
        easier. It prompts the user to select an existing saved JSON change report and calls the DTWrapper import_report
        function, which allows the user to then step through each change in the report by "redo"ing the operation.
        """

        # get the filename
        cr_filename = tk.filedialog.askopenfilename(defaultextension='.json', filetypes=[('JSON file', '*.json'),
                                                                                         ('All Files', '*.*')])

        if not cr_filename:
            # no filename specified
            return

        try:
            with open(cr_filename, 'rb') as f:
                # import the report
                self.dtw.import_report(f.read())

                # update the views
                self._update_views()
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to import change report', 'Encountered error while attempting to import '
                                                                      'change report:\n' + getattr(ex, 'message',
                                                                                                   str(ex)))

    def save_file(self, _=None, from_xbl=False):
        """Save the file that is currently being edited. Saves in-place (i.e., overwrites existing file).

        :param _: ignored
        :param from_xbl: whether this function is getting called from the xblcfgint XblCfgGUI, in which case there may
                         be some useful information to display for the user.
        :return: Whether the file was successfully saved; True for yes and False for no.
        """

        new_dtb = self.dtw.dtb

        with open(self.dtw.fdt_name, 'wb') as f:
            f.write(new_dtb)

            self.fdtModified = False
            self._update_title()

        if not from_xbl and self.xblDialog and self.userFirstTimeXbl:
            self.userFirstTimeXbl = False
            tk.messagebox.showinfo('No need to save', 'Changes to a DTB are automatically saved when editing XBLConfig '
                                                      'files. You do not need to manually save them!')

        # if from_xbl and self.xblDialog and len(self.dtw.dtb) % 4:
        #     tk.messagebox.showwarning('Bad size for DTB', 'Due to technical limitations, DTBs in an XBLConfig file must'
        #                                                   ' have a length that is a multiple of four, and this DTB is '
        #                                                   'not. Please modify this file to correct the issue. To '
        #                                                   'confirm the length of this file, use the raw view.')
        #     return False
        return True

    def save_as(self, _=None):
        """Save the file that is currently being edited as a new file.

        :param _: ignored
        """

        output_filename = tk.filedialog.asksaveasfilename(defaultextension='.dtb',
                                                          filetypes=[('Device Tree Blob', '*.dtb'),
                                                                     ('All Files', '*.*')])
        if output_filename:
            new_dtb = self.dtw.dtb
            with open(output_filename, 'wb') as f:
                f.write(new_dtb)

    def export_dts(self, _=None):
        """Export the current DeviceTree state as a DTS file

        :param _: ignored
        """

        output_filename = tk.filedialog.asksaveasfilename(defaultextension='.dts',
                                                          filetypes=[('Device Tree Source', '*.dts'),
                                                                     ('All Files', '*.*')])
        if output_filename:
            result_dts = self.dtw.to_dts()
            with open(output_filename, 'wb') as f:
                f.write(result_dts.encode())

            tk.messagebox.showinfo('Export Complete', 'DTS file exported successfully!')

    def hexview_closed(self):
        """Callback for when the HexView is closed, in order to uncheck the "View->Raw" checkbox"""

        self.hexViewShowing.set(False)

    def show_hexview(self, _ivn=None, _idx=None, _op=None):
        """Event handler for when the "view->raw" check box value changes. Will either show or hide the hex view,
        depending on the value of the check box.

        :param _ivn: ignored
        :param _idx: ignored
        :param _op: ignored
        """

        if self.hexViewShowing.get():
            # check box is on, so we should display the hex view
            self.hexView = HexWindow(self._root, self, self.hexview_closed)
        else:
            # check box is off, so we should destroy the hex view
            self.hexView.close_callback = None
            self.hexView.destroy()

    def update_readonly(self, _ivn=None, _idx=None, _op=None):
        """Event handler for when the read-only checkbox value changes. Will update whether the view is currently
        read-only or not. Used in test mode only.

        :param _ivn: ignored
        :param _idx: ignored
        :param _op: ignored
        """

        if self.viewReadOnly.get():
            gf['readonly'] = True
        else:
            gf['readonly'] = False

    def _cvs_h(self):
        """Helper function to update the view style BooleanVars"""

        self.viewStyleIgnTrace = True
        self.viewStyleHex.set(gf['viewAsHex'])
        self.viewStyleDec.set(not gf['viewAsHex'])
        self.viewStyleIgnTrace = False

    def change_viewstyle(self, _ivn=None, _idx=None, _op=None):
        """Event handler for when the user changes the current view style (hex/decimal).

        This function contains all of the logic to toggle

        :param _ivn: ignored
        :param _idx: ignored
        :param _op: ignored
        """

        if self.viewStyleIgnTrace:
            # ignore
            return
        if not (self.viewStyleHex.get() or self.viewStyleDec.get()):
            # neither one was set, oops! user must've clicked on an already checked one. undo that.
            # for some reason we need to delay for a sec before we make changes to the view style BooleanVars,
            # otherwise a desync with the GUI arises.
            self._root.after(1, lambda: self._cvs_h())
            return
        if self.viewStyleHex.get() and self.viewStyleDec.get():
            # both options are selected, i.e. user just tried to switch. now we rely on which one was there
            # previously to know which one to enable.
            if gf['viewAsHex']:
                # last style was hex, now we want dec
                self.viewStyleIgnTrace = True
                self.viewStyleHex.set(False)
                self.viewStyleIgnTrace = False
                gf['viewAsHex'] = False
            else:
                # last style was dec, now we want hex
                self.viewStyleIgnTrace = True
                self.viewStyleDec.set(False)
                self.viewStyleIgnTrace = False
                gf['viewAsHex'] = True

            # at this level here, changes have occurred, so we want to re-render the treeview
            self.treeView.update_viewstyle()
            return

        # there are other possible states here but they are error states so we'll just ignore them.
        # the user can correct for it by themselves if they just press another checkbox.

    def edit_item(self, path):
        """Function called by the Tree View when the user expresses intent to edit a property at a given path.

        :param path: The path to the property that the user wants to edit
        """

        # get the item from the DeviceTree
        item = self.dtw.resolve_path(path)

        # pop up the EditDialog; this call will not return until the user has closed the dialog
        d = EditDialog(self, self._root, path, item)

        if (not d.result) and (not d.nameResult):
            # user cancelled
            return

        if d.result:
            # user has modified the property value
            try:
                modp = self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.EDIT_PROPERTY_VALUE, path, d.result))

                # update the views
                self._update_views(modp)
            except Exception as ex:
                tk.messagebox.showerror('Failed to save changes',
                                        'Encountered error while attempting to save changes:\n' +
                                        getattr(ex, 'message', str(ex)))
                return

        if d.nameResult:
            # user has modified the property name
            try:
                new_name = d.nameResult.rsplit('/', 1)
                modp = self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.RENAME_PROPERTY, new_name[1], path))

                # update the views
                self._update_views(modp)
            except Exception as ex:
                tk.messagebox.showerror('Failed to save changes',
                                        'Encountered error while attempting to save changes:\n' +
                                        getattr(ex, 'message', str(ex)))
                # TODO: also rollback the change in value if the name change failed
                return

    def edit_item_inline_cb(self, path, new_value):
        """Callback for the TreeView for when the user has finished inline editing

        :param path: Path to the property that was edited
        :param new_value: New value to set the property to
        """

        try:
            self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.EDIT_PROPERTY_VALUE, path, new_value))
        except Exception as ex:
            tk.messagebox.showerror('Failed to save changes',
                                    'Encountered error while attempting to save changes:\n' +
                                    getattr(ex, 'message', str(ex)))
            return

        # update the views
        self._update_views(path)

    def delete_item(self, path):
        """Callback for the TreeView for when the user has expressed the intent to delete an item

        :param path: Path to delete from the DeviceTree
        """

        try:
            item = self.dtw.resolve_path(path)
            op = dt.DTOperationType.DELETE_NODE if item.is_node() else dt.DTOperationType.DELETE_PROPERTY
            self.dtw.apply(dt.DTOperation.make(op, path))
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to delete item', 'Encountered error while attempting to apply changes:\n' +
                                    getattr(ex, 'message', str(ex)))
            return

        # update the views
        self._update_views(path)

    def _cleanup_highlights(self, prefix):
        """Clean up highlights with the same prefix

        This function deletes all of the elements of knownHighlights that share a prefix with the given string.
        It helps to keep the list of highlights short where there is overlap (e.g. highlight for /path/child and
        /path later will overwrite the /path/child highlight, so it's helpful to not even bother storing the highlight
        for /path/child). The function is called whenever a new highlight() is requested in order to trim the existing
        highlights that would be rendered invisible by this new highlight (highlights take precedence by order of
        when the user highlights that path).

        :param prefix: Path prefix string to match highlights with in order to determine which highlights to delete
        """
        # we traverse the array in this strange method in order to be able to delete items in the array
        arr_max = len(self.knownHighlights)
        i = 0
        while i < arr_max:
            if self.knownHighlights[i][0].startswith(prefix):
                # shared prefix, so we want to delete this item
                del self.knownHighlights[i]
                # note that we decreased the length of the array, so we decrease max
                arr_max -= 1
                # however, we don't increment i because all of the elements have shifted over by 1 due to the delete
            else:
                # not changing the array, so just increment i by one
                i += 1

    def highlight(self, path, color):
        """Callback for the TreeView for when the user has expressed an intent to highlight a path with a given color

        :param path: Path to the DeviceTree item that is getting highlighted
        :param color: Background color to highlight the path with. Foreground color black/white is automatically
                      inferred by the brightness of the background.
        """

        if color is None:
            # if no color is given, don't highlight
            return

        self._cleanup_highlights(path)

        def decide_fg(bgc):
            # algorithm from http://alienryderflex.com/hsp.html
            # expects a hex color
            bgc = bgc.lstrip('#')
            clen = len(bgc)
            r, g, b = tuple(int(bgc[i:i + clen // 3], 16) for i in range(0, clen, clen // 3))
            hsp = math.sqrt(0.299 * r * r + 0.587 * g * g + 0.114 * b * b)
            if hsp >= 128:
                # light background, so pick a dark foreground
                return '#000000'
            else:
                # dark background, so pick a light foreground
                return '#ffffff'

        bg_color = color
        fg_color = decide_fg(bg_color)

        hli = (path, bg_color, fg_color)
        self.knownHighlights.append(hli)
        self.treeView.highlight(*hli)
        if self.hexViewShowing.get():
            self.hexView.highlight(*hli)

    def clear_highlights(self, _=None):
        """Clear all highlights and update the TreeView and HexView of this change

        :param _: ignored
        """

        self.knownHighlights = []
        self.treeView.clear_highlights()
        if self.hexViewShowing.get():
            self.hexView.update_view()

    def add_node(self, parent_path):
        """Callback for the TreeView for when the user has expressed an intent to add a new node to the DeviceTree

        This function prompts the user for the

        :param parent_path: The parent path of the node that will be added
        """

        child_name = tk.simpledialog.askstring('Name', 'Name of new node?', parent=self._root)

        if child_name is None:
            # user cancelled
            return

        try:
            self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.ADD_NODE, parent_path, child_name))
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to create node', 'Encountered error while attempting to apply changes:\n' +
                                    getattr(ex, 'message', str(ex)))
            return

        # get the path of this child node
        child_path = parent_path + child_name if parent_path[-1] == '/' else parent_path + '/' + child_name

        # update the views
        self._update_views(child_path)

    def copy_node(self, node_path):
        child_path = tk.simpledialog.askstring('Copy Node', 'Path of new node?', parent=self._root, initialvalue=node_path+"_copy")
        if child_path is None:
            # user cancelled
            return

        # Basic error check of the path
        if len(child_path)<=1 or '/' not in child_path or '//' in child_path or '?' in child_path:
            tk.messagebox.showerror('Failed to copy node', 'The given path is not valid')
            return
        # Code splits based on /'s so we remove the trailing /
        if child_path[-1]=='/':
            child_path=child_path[:-1]

        #extracting child node name and parent path to feed to function
        child_name=child_path.rsplit('/', 1)[1]
        parent_path=child_path.rsplit('/', 1)[0]
        if parent_path=='':
            parent_path='/'

        # Asking the user if he wants to create the path if it does not exist
        parent_node = self.dtw._fdt.resolve_path(parent_path)
        current_path=''
        if not isinstance(parent_node, pyfdt.FdtNode):
            r = tk.messagebox.askyesno('Create New Path', 'The Path you requested does not exist. Create this path?', icon='warning')
            if r==False:
                return
            current_path+='/'
            # Need to find at which point the path needs to be created in order to call self._update_views from that point
            allnodes=parent_path.split("/")
            for i in allnodes:
                if current_path[-1]=='/':
                    current_path+=i
                else:
                    current_path+='/'+i
                current_node = self.dtw._fdt.resolve_path(current_path)
                if not isinstance(current_node, pyfdt.FdtNode):
                    break
        try:
            self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.COPY_NODE, parent_path, node_path, child_name, child_path))
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to create node', 'Encountered error while attempting to apply changes:\n' +
                                    getattr(ex, 'message', "{}".format(ex)))
            return
        if current_path!='':
            self._update_views(current_path)
        else:
            self._update_views(child_path)

    def add_property(self, parent_path, prop_type):
        """Handler for when the user expresses an intent to add a new property to the DeviceTree

        When this function is called, the user has expressed an intent to add a new property to the DevieTree. So, this
        function will create a new EditDialog to prompt the user for information on the new property to add before
        calling the DTWrapper function to add the new property.

        :param parent_path: Path to the parent node
        :param prop_type: Type of the property to add
        """

        # edit dialog only returns once the user presses ok/cancel
        d = EditDialog(self, self._root, parent_path if parent_path[-1] == '/' else parent_path + '/', prop_type)

        if d.nameResult and (d.result or prop_type == dt.FdtPropertyType.EMPTY):
            child_name = d.nameResult.replace(parent_path, '', 1)
            if child_name[0] == '/':
                child_name = child_name[1:]
            try:
                self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.ADD_PROPERTY, parent_path, child_name, prop_type,
                                                   d.result))
            except Exception as ex:
                if gf['debug']:
                    traceback.print_exc()
                tk.messagebox.showerror('Failed to save changes',
                                        'Encountered error while attempting to save changes:\n' +
                                        getattr(ex, 'message', str(ex)))
                return

            # update the views
            self._update_views(d.nameResult)

    def hexview_showpath(self, path):
        """Show a path in the hex view

        :param path: Path to show in the hex view
        """

        if not self.hexViewShowing.get():
            return

        self.hexView.show_path(path)

    def find_popup_closed(self):
        """Callback to empty the findView variable when the find view popup is closed"""

        self.findView = None

    def find_popup(self, _=None):
        """Function to pop up a new instance of the find window"""

        if self.findView is not None:
            # close and destroy old window if already open
            self.findView.destroy()
            self.findView = None

        self.findView = FindWindow(self._root, self, self.find_next, self.find_popup_closed)
        pass

    def find_next(self, opts=None):
        """Function to find an item in the DeviceTree

        :param opts: Find options. If not specified, the most recent find options will be used instead.
        """

        if opts is None or not isinstance(opts, dict) or 'str' not in opts:
            # keypress event or menu button press. set opts to most recent known opts
            opts = self.lastFindOpts
        else:
            self.lastFindOpts = opts

        if opts is None:
            # still no opts to search from (user must've used the Find Next key before ever opening the Find dialog)
            return

        # get the current selection to know where to start the find from
        sel = self.treeView.get_selection()

        if len(sel) == 0:
            # no item selected because there are no elements in the treeview
            return

        if opts['matchCase']:
            # we want to match case
            cmp_pre = lambda x: x
        else:
            # ignore case, so we will just make everything lowercase and then compare
            opts['str'] = opts['str'].lower()
            cmp_pre = lambda x: x.lower()

        # now we walk the entire tree
        find_idx = 0 if sel[0] == '/' else -1
        found_paths = []
        for path, item in self.dtw.resolve_path('/').walk():
            # first check if the property matches the search query
            if opts['searchNames']:
                # search the name of the property
                if opts['str'] in cmp_pre(path):
                    # found!
                    found_paths.append(path)
                    if find_idx >= 0:
                        break
            if opts['searchValues']:
                # search the value of the property
                # note that to allow for searches in binary values, we actually search in the pretty-printed format
                if item.is_property() and opts['str'] in cmp_pre(item.to_pretty()):
                    # found!
                    found_paths.append(path)
                    if find_idx >= 0:
                        break

            if path == sel[0]:
                # this is the index at which we want to return the find idx, if possible
                # basically this says, "we want to return the next item found"
                find_idx = len(found_paths)

        # if either found_start is False or found_path is None, then no results were found
        if len(found_paths) == 0:
            tk.messagebox.showinfo('No results found', 'Cannot find query \'%s\' in DeviceTree!' % opts['str'])
            return

        # otherwise, we found a result, so display it in the treeview
        # taking modulo allows us to do a wrap around to the 1st item if "the next item found" is not, in fact, found
        self.treeView.show_path(found_paths[find_idx % len(found_paths)])
        self.hexview_showpath(found_paths[find_idx % len(found_paths)])

    def update_undoredo(self):
        """Update the unod/redo text in the Edit menu"""

        top_op = self.dtw.top_undo()
        if top_op:
            self.editMenu.entryconfig(0, label='Undo ' + top_op.optype.to_pretty(), state=tk.NORMAL)
        else:
            self.editMenu.entryconfig(0, label='Undo', state=tk.DISABLED)

        top_op = self.dtw.top_redo()
        if top_op:
            self.editMenu.entryconfig(1, label='Redo ' + top_op.optype.to_pretty(), state=tk.NORMAL)
        else:
            self.editMenu.entryconfig(1, label='Redo', state=tk.DISABLED)

    def undo(self, _=None):
        """Undo an operation

        :param _: Ignored
        """

        undo_top = self.dtw.top_undo()

        if not undo_top:
            return

        if isinstance(undo_top, dt.DTOperationLoad) and self.xblDialog:
            # not the prettiest solution, but we can't undo load when we're in an XBLConfig editing session since that
            # breaks things
            return

        try:
            path = self.dtw.undo()
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to undo operation', 'Encountered error while attempting to apply changes:\n'
                                    + getattr(ex, 'message', str(ex)))
            return

        # update the views
        self._update_views(path)

    def redo(self, _=None):
        """Redo an operation

        :param _: Ignored
        """

        if not self.dtw.top_redo():
            return

        try:
            path = self.dtw.redo()
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            tk.messagebox.showerror('Failed to redo operation', 'Encountered error while attempting to apply changes:\n'
                                    + getattr(ex, 'message', str(ex)))
            return

        # update the views
        self._update_views(path)
        if isinstance(path, str) and path != '/':
            # if we have a specific path that was updated, jump the focus to it
            self.treeView.show_path(path)


def run(root, **kwargs):
    """

    :param root:
    :param kwargs:
    :return:
    """

    if gf['nogui']:
        # load a CR and apply all of the changes in it
        dtw = dt.DTWrapper()

        autocmd = cmd.autocmd(dtw)
        autocmd.execute()

        # comment below features
        """ 
        if 'cr' in kwargs:
            dtw.import_report(kwargs['cr'])
        else:
            if 'initial_file' in kwargs:
                cr = kwargs['initial_file']
                dtlogger.info('Using Change Report %s' % cr)
            else:
                cr = input('Change Report: ')

            try:
                with open(cr, 'rb') as f:
                    # import the report
                    dtw.import_report(f.read())
            except Exception as ex:
                if gf['debug']:
                    traceback.print_exc()
                dtlogger.info('Failed to import change report: %s' % getattr(ex, 'message', str(ex)))
                return

        # redo everything
        try:
            while dtw.top_redo() is not None:
                dtlogger.info('Applying', dtw.top_redo())
                dtw.redo()
        except dt.UndoRedoExhaustedError:
            pass
        except Exception as ex:
            if gf['debug']:
                traceback.print_exc()
            dtlogger.info('Failed to apply change report: %s' % getattr(ex, 'message', str(ex)))
            return """
    else:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        DTGUIController(root, **kwargs)
        # start processing events

        root.mainloop()


if __name__ == '__main__':
    run(tk.Tk())
