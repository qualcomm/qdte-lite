# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file xblcfgint.py
This file contains the code that interfaces with the XBLConfig tools (mostly GenXBLConfig.py) to disassemble and
reassemble XBLConfig ELFs into a temporary directory for the main DTGUI tool to edit.

The bulk of the code in this file is from the XblCfgGUI class. This class handles all of the interfacing with the
XBLConfig tools (diassembly, reassembly, signing) and provides a nice graphical console to view the output of the
tools.

This file was originally imagined as a separate component that could be run and would "embed" the main DTGUI editor by
treating the DTGUI as a dialog box, and have the DTGUI return the updated DTB in some way. However, in order to present
a single unified GUI for the user, it was changed to be a "helper" window for the main DTGUI editor instead. Now, the
DTGUI controller (controller.py) will instantiate a copy of the XblCfgGUI class when the user chooses to open an
XBLConfig ELF. The XblCfgGUI class takes the filename, creates a temporary directory, disassembles the XBLConfig to the
temporary directory, and lists out all of the DTB files that were found in the XBLConfig disassembly. The user can then
pick a DTB file to edit in the main DTGUI. The DTGUI will read from and save to the DTB in the temporary directory.
When the user has completed all of their changes, they can press the "Reassemble and Sign..." button in the XblCfgGUI to
specify a location to save the reassembled XBLConfig ELF to. The XblCfgGUI will then proceed to reassemble the ELF and
sign it if necessary.

Despite the changes to make the XblCfgGUI class a "helper" window, the file is still structured a little bit differently
compared to the other files in this path. Notably, it contains a lot more backend logic and very closely integrates with
the controller's internals, which most other files do not. However, doing so keeps the controller "pure" in the sense
that it does not heavily rely on the XBLConfig format; for example, if one day, the XBLConfig is radically modified or
even no longer used, the main DTUGI can still function perfectly fine to edit regular standalone DeviceTree Blobs.
"""

import json
import threading
import time
import tempfile
import shutil
import os
import stat
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import traceback
import subprocess
import atexit
import xml.dom.minidom
import re
import platform
# gui things
from flags import flags as gf
from flags import global_info as gl_info
import assemble
import version_2_assemble
import sign
from settings import Json_Operate
import settings
import dtlogger
if platform.system().startswith("Windows"):
    sectool_name = "sectools.exe"
else:
    sectool_name = "sectools"

class XblCfgGUI(tk.Toplevel,assemble.assemble,sign.st):
    inlbl = None
    listbox = None
    instructionslbl = None
    cmdsout = None
    reassembleText = ''

    def __init__(self, root, controller, xbl_fn):
        super().__init__(root)

        # check xblconfig is even enabled
        if not gf['xblEnabled']:
            raise ValueError('XBLConfig integration disabled')

        # initialize variables
        self._root = root
        self.xbl_fn = xbl_fn
        self.outdir = None
        self.dtbs = None
        self.changes = {}
        self.changesTransient = None
        self.dtbs_modified = False
        self.last_edited_file = None
        self.controller = controller
        self.reassembleText = 'Reassemble'
        self.magicnumberstring='d00dfeed'
        self.reassembleSignText = 'Reassemble and Sign...'
        self.sectool_name = sectool_name
        # setup ui components
        self.init_components()

        # give window title
        self.title('DTB ELF Helper')
        gf['inputFile']=xbl_fn
        # handle unclean exits
        atexit.register(self.cleanup_tempdir)

        # delay the disassembly process for a bit so that the main UI will show for the user
        self._root.after(1, self.generate_tempdir)

    def init_components(self):
        self.geometry('900x400')
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        tk.Grid.columnconfigure(self, 0, weight=1)

        # row 0: instructions
        self.instructionslbl = tk.Label(self, text='Double-click any item below to edit the DTB:')
        self.instructionslbl.grid(row=0, column=0, columnspan=2, sticky='nesw')

        # row 1: input
        # self.inlbl = tk.Label(self, text=self.xbl_fn, justify='left', borderwidth=2,
        #                       relief='groove')
        # self.inlbl.grid(row=1, column=0, sticky='nesw', columnspan=2)

        # row 2: Treeview with DTB's to edit
        self.treeview = ttk.Treeview(self)
        tk.Grid.rowconfigure(self, 2, weight=10)
        self.treeview.grid(column=0,row=2,sticky='NSEW')
        self.treeview.heading('#0', text=self.xbl_fn, anchor='w')
        # event handler
        self.treeview.bind('<Double-Button-1>', self.edit_file)



        # row 3: save button
        tmp_frame = tk.Frame(self,)
        tmp_frame.grid(row=3, column=0, columnspan=2, sticky='nesw')
        ttk.Button(master=tmp_frame, text=self.reassembleText, width=25, command=self.export_xbl_unsign).grid(row=0, column=2, pady=5, sticky='ew')
        ttk.Button(master=tmp_frame, text=self.reassembleSignText, width=25, command=self.export_xbl_sign).grid(row=0, column=4, pady=5, sticky='ew')
        tmp_frame.grid_columnconfigure((0, 1, 3, 5, 6), weight=1)
        # tk.Button(self, text=self.reassembleText, command=self.export_xbl).grid(row=3, column=0, columnspan=2, sticky='nesw')

        # row 4: scrolled text console
        self.cmdsout = tk.scrolledtext.ScrolledText(self, height=5, font='TkFixedFont')
        self.cmdsout.tag_config('err', foreground='#CC0000')
        self.cmdsout.tag_config('info', foreground='#0066CC')
        self.cmdsout.tag_config('success', foreground='#008800')
        self.cmdsout.tag_configure('warn', foreground='#EE8800')
        self.cmdsout.grid(row=4, column=0, columnspan=2, sticky='nesw')
        tk.Grid.rowconfigure(self, 4, weight=20)
        self.geometry("+%d+%d" % ((screenwidth - 900) / 2, (screenheight - 400) / 2))

        # cach close
        self.protocol('WM_DELETE_WINDOW', self.cleanup_and_close)

    def logline(self, line, tag=None):
        if tag is not None:
            # this line has some sort of special tag, so we
            self.cmdsout.insert(tk.END, line, (tag,))
            if line[-1] != '\n':
                self.cmdsout.insert(tk.END, '\n')
        elif gf['detailedConsole']:
            # untagged info is only shown in detailed console view mode
            self.cmdsout.insert(tk.END, line)
            if line[-1] != '\n':
                self.cmdsout.insert(tk.END, '\n')

        self.cmdsout.see(tk.END)
        self.cmdsout.update_idletasks()

    def generate_tempdir(self):
        # step 2: generate a new temp directory
        self.logline('Generating temporary directory for output...', 'info')
        try:
            if self.outdir:
                # clean up old temporary directory
                shutil.rmtree(self.outdir)
                # can no longer edit those files
                self.listbox.delete(0, tk.END)
            self.outdir = tempfile.mkdtemp(prefix='dtgui_')
        except IOError as ex:
            self.logline('Error when creating a temporary work directory: %s' % getattr(ex, 'message', repr(ex)))
            if gf['debug']:
                traceback.print_exc()
            # throw an error if there is an invalid file
            tk.messagebox.showerror('Failed to create work directory', 'Failed to create a temporary work directory:\n'
                                                                       '%s' % getattr(ex, 'message', repr(ex)))
            return

        self.disassemble_xblconfig()


    def disassemble_xblconfig(self):
        # step 3: parse the file
        self.logline('Disassembling XBLConfig file...', 'info')
        # start a child python process
        errlines = []
        
        self.config(cursor='watch')
        self.cmdsout.config(cursor='watch')
        self.update()

        # First, attempt to disassemble the ELF using Version 2 Disassemble
        try:
            self.dissamble_config_elf()
        except Exception as result:
            if not gf['detailedConsole']:
                tk.messagebox.showwarning('Failed to disassemble', 'Failed to disassemble XBLConfig:\n'
                                                               '%s' % (result))

        self.config(cursor='')
        self.cmdsout.config(cursor='')

        # step 4: figure out what the files disassembled were
        self.logline('Scanning disassembled files for DeviceTrees...', 'info')
        self.dtbs={}
        self.scan_disassembly(self.outdir,self.dtbs)
        if len(self.dtbs) == 0:
            self.logline('No DTBs found in XBLConfig', 'err')
            return False
        self.list_dtbs(self.dtbs,"")
        self.logline('Success!', 'success')
        return 
            
        if len(hints) > 0:
            for hint in hints:
                self.logline('Hint: %s' % hint, 'warn')

    def scan_disassembly(self,dir,dtbs_dic):

        #Finding dtbs using magicnumber
        for f in os.listdir(dir):
            if os.path.isfile(os.path.join(dir, f)):
                file = open(os.path.join(dir, f), "rb")
                magicnumber = file.read(4)
                magicnumberhex=magicnumber.hex()
                if magicnumberhex==self.magicnumberstring:
                    #self.dtbs.append(f)
                    dtbs_dic[f]=f
                file.close()
            elif "dtbs" in f:
                #dtbs_dic[f+".bin"]={}
                dtbs_dic[f]={}
                dtbs_folder_path=os.path.join(os.path.join(dir, f))
                self.scan_disassembly(dtbs_folder_path,dtbs_dic[f])

        return True

    def list_dtbs(self,dtbs_dic,root):
        # step 5: get user input on which file to edit
        for key,value in dtbs_dic.items():
            if isinstance(value,dict):
                tree_view = self.treeview.insert(root,tk.END, text=key,open=True)
                self.list_dtbs(dtbs_dic[key],tree_view)
            else:
                self.treeview.insert(root,tk.END, text=value,open=True)
        # done one chain of steps
        # self.treeview.pack()
        return True

    def edit_file(self, _=None):

        sel_dtb_path = ''
        sel_dtb = None
        curItem = self.treeview.focus()
        parentItem = self.treeview.parent(curItem)
        
        if parentItem == '':
            if self.treeview.item(curItem)['text'].endswith('.bin'):
                return
            else:
                sel_dtb = self.dtbs[self.treeview.item(curItem)['text']]
                sel_dtb_path = os.path.join(self.outdir,sel_dtb)
        else:
            sel_dtb = self.dtbs[self.treeview.item(parentItem)['text']][self.treeview.item(curItem)['text']]
            sel_dtb_path = os.path.join(self.outdir,self.treeview.item(parentItem)['text'].rstrip('.bin'),sel_dtb)

        if self.last_edited_file == sel_dtb:
            # double-clicking the same file
            return

        # store the change report for the most recent file before re-opening
        if not self.update_changes():
            # error occurred while updating changes
            return

        # step 6: edit the file
        if self.controller.open_file(new_filename=sel_dtb_path):
            self.last_edited_file = sel_dtb
            self.logline('Editing %s' % sel_dtb, 'info')
            self._root.lift()
            self.dtbs_modified = True
            self.instructionslbl.config(text='Press the "%s" button below to write changes to the XBLConfig' %
                                             self.reassembleText)

    def update_changes(self, transient=False):
        """Update the XBLConfigHelper window's knowledge of the changes made to the DTB

        This function updates the changes variable, which keeps track of the changes made to all of the DTBs in the
        XBLConfig ELF, and is also stored out when the user reassembles an XBLConfig.

        :param transient: Whether or not to clear the modifications added in this call to update_changes() in the next
                          call to update_changes()
        :return: Whether knowledge of the changes made was successfully updated
        """
        if self.last_edited_file is None:
            # no last edited file
            return True

        # save the DTB
        if not self.controller.save_file(from_xbl=True):
            # failed to save file
            return False

        # transient changes exist, so we have to discard them
        if self.changesTransient:
            key, value = self.changesTransient
            self.changes[key] = value
            self.changesTransient = None

        # get the change report from the controller
        cr = self.controller.get_changes(pyobj=True)
        # the first report item will always be the LOAD item
        if len(cr) < 2:
            # no changes made (just 1 item, or 0, = only LOAD)
            return True

        # trim the first LOAD item
        cr = cr[1:]

        # before making changes, check if things are transient
        if transient:
            # yes, so make a backup copy first
            key = self.last_edited_file
            if key in self.changes:
                value = self.changes[key].copy()
            else:
                value = []
            self.changesTransient = (key, value)

        if self.last_edited_file in self.changes:
            # changes already made, so extend the existing array
            self.changes[self.last_edited_file].extend(cr)
        else:
            # no changes made to this file yet, so create a new index
            self.changes[self.last_edited_file] = cr

        return True
    # detect if orginal DTB elf is single segment DTB elf
    def check_single_segment(self):
        disassembled_elf_info = None
        number_of_segments = 0
        try:
            with open(os.path.join(self.outdir, 'disassembled_elf_info.json'), mode='r', encoding="utf-8") as fp:
                disassembled_elf_info = json.load(fp)
        except Exception as e:
            #self.logline('Error: Open '+os.path.join(self.outdir, 'disassembled_elf_info.json')+'failed')
            dtlogger.debug(e)
        # statistics the number of segments
        for key in disassembled_elf_info.keys():
           if key.startswith('segment_'):
             number_of_segments+=1
        dtlogger.debug(number_of_segments)
        if number_of_segments==3:
           return 'True'
        else:
           return ''
            
    def export_xbl_unsign(self):
        gf['allowUnsigned'] = 1
        if not self.update_changes(transient=True):
            return False
        # step 7: ask user for output location
        output_filename = tk.filedialog.asksaveasfilename(defaultextension='.elf',
                                                          filetypes=[('XBLConfig/DTB ELF', '*.elf'),
                                                                     ('All Files', '*.*')])
        self.lift()
        if output_filename:
            if gf['dryRun']:
                self.logline('Will not actually save to the file specified, because dry run.', 'info')
                self.controller.dtlogger.debug("change:{}".format(self.changes))
                return
            else:
                self.logline('Saving all changes to %s...' % output_filename, 'info')
            gf['outputFile'] = os.path.basename(output_filename)

            gf['outputPath'] = os.path.dirname(output_filename)
            # store the change report, too
            # the output filename format will be basename_timestamp.json
            cr_filename = '%s_%d.json' % (output_filename.rsplit('.elf', 1)[0], time.time())
            try:
                with open(cr_filename, 'wb') as outfile:
                    outfile.write(json.dumps(self.changes, indent=2).encode())
                    self.logline('Saved report of changes made to %s' % cr_filename, 'info')
            except IOError:
                self.logline('Warning: failed to save change report to accompany new XBLConfig', 'warn')

            # start a child python process
            self.config(cursor='watch')
            self.cmdsout.config(cursor='watch')
            self.update()
            self.logline('Excute Reassembling...', 'info')
            try:
                # First, find if the xbl_config JSON exists, then determine which reassemble method to use
                self.reassemble_config_elf()
                shutil.copy(os.path.join(self.outdir, 'auto_gen', 'elf_files', 'create_cli',
                                             os.path.basename(output_filename)), output_filename)

            except Exception as result:
                self.logline('Excute Reassembling failed:'+result, 'err')
                if not gf['detailedConsole']:
                    tk.messagebox.showwarning('Failed to save', 'Failed to save results:\n%s' % ''.join(result))

                return False
            self.logline('Reassembling Success!', 'success')  
            self.dtbs_modified = False
            self.instructionslbl.config(text='Success!')
            self.config(cursor='')
            self.cmdsout.config(cursor='')
            return True
        return False
    def export_xbl_sign(self):
        gf['allowUnsigned'] = 0
        tmp_thread= threading.Thread(target=self.call_tmp_thread_sign, name="tmp Thread")
        tmp_thread.setDaemon(True)
        tmp_thread.start()

    def call_tmp_thread_sign(self):
        # why transient? because the user can press "save as" again without switching DTB's, and since they never closed
        # the previous session, that will keep the most recent edit session's change report, which will basically
        # result in duplicated change report items. this is one way to fix that; when we store this copy of the change
        # report we mark it "transient" which means that the changes we add in this function call will be reset the next
        # time update_changes() is called.
        
        gf["setting_flag"] = 0
        gf['sign_id'] = ''
        sign_id_num = 0
        return_result = False
        result = ''
        settings.Settings(self._root,settings.ITEMS_SECTOOL)
        while(gf['setting_flag'] == 0):
           time.sleep(0.2)
        if gf['setting_flag'] == 255:
            return

        if not self.update_changes(transient=True):
            return False

        if gf['setting_flag'] == 1:
           # step 7: ask user for output location
            output_filename = tk.filedialog.asksaveasfilename(defaultextension='.elf',
                                                          filetypes=[('XBLConfig/DTB ELF', '*.elf'),
                                                                     ('All Files', '*.*')])
            self.lift()
            if output_filename: 
                prog_win = DT_ProgressBar(self._root)
                if gf['dryRun']:
                    self.logline('Will not actually save to the file specified, because dry run.', 'info')
                    dtlogger.info("change:{}".format(self.changes))
                    return
                else:
                    self.logline('Saving all changes to %s...' % output_filename, 'info')
                gf['outputFile'] = os.path.basename(output_filename)

                gf['outputPath'] = os.path.dirname(output_filename)
                # store the change report, too
                # the output filename format will be basename_timestamp.json
                cr_filename = '%s_%d.json' % (output_filename.rsplit('.elf', 1)[0], time.time())
                try:
                    with open(cr_filename, 'wb') as outfile:
                        outfile.write(json.dumps(self.changes, indent=2).encode())
                        self.logline('Saved report of changes made to %s' % cr_filename, 'info')
                except IOError:
                    self.logline('Warning: failed to save change report to accompany new XBLConfig', 'warn')
                
               

                # start a child python process
                # reassemble xbl images without sign
                self.update()
                sectoolsDir = os.path.dirname(gf['sectoolsDir'])
                gf['outputFile']=output_filename
                self.logline('Excute Reassembling...', 'info')
                try:
                    # See if a legacy or new ELF file has been disassembled
                    self.reassemble_config_elf()

                except Exception as result:
                    self.logline('Excute Reassembling failed:{}'.format(result), 'err')
                    prog_win.call_popup_close()
                    return False
                self.logline('Reassembling Success!', 'success')

               

                # If signing command doesn't contain  --image-id option, fetch it from origninal DTB elf. If the orginal DTB elf is unsigned DTB elf. 
                # If the orginal DTB elf is unsigned DTB elf, it will popout a warning windows and termined signing process.
                self.cmdsout.insert(tk.END, 'Excute Signing Command\n', 'info')
                try:
                    return_result = self.sign_config_image()
                except Exception as result:
                    self.cmdsout.insert(tk.END, 'Excute Signing Failed!', 'err')
                prog_win.call_popup_close()
                if not gf['detailedConsole'] and return_result == False:
                    tk.messagebox.showerror('Signing failed', 'Please check signing log!')
               

                
                if return_result:
                    self.dtbs_modified = False
                    self.instructionslbl.config(text='Success!')
                    self.logline('Reassembling and Signing Success!', 'success')
                    return True

               
                return False

    def cleanup_and_close(self, _=None):
        if self.dtbs_modified or self.controller.fdtModified:
            r = tk.messagebox.askyesnocancel('Save changes', 'Save changes before closing XBLConfig file?',
                                             icon='warning')
            if r:
                # yes = save changes, then continue
                if not self.export_xbl_sign():
                    # failed to save changes, so cancel cleanup & close
                    return
            if r is None:
                # cancel = do not do anything
                return

        # step 8: clean up temporary directory
        self.cleanup_tempdir()
        atexit.unregister(self.cleanup_tempdir)

        # step 9: close the window
        self.controller.on_xbldialog_close()
        self.destroy()

        return True

    def cleanup_tempdir(self):
        if self.outdir and os.path.isdir(self.outdir):
            # delete the temporary directory if it exists
            shutil.rmtree(self.outdir)


class DT_Select_GUI():
    select_width = 400
    title = "Get Partition Image"

    def __init__(self, root, _dt_dict):
        self.root = root
        self.dt_dict = _dt_dict
        self.partition_list = [item for item in self.dt_dict]
        f1=tkFont.Font(family="TkFixedFont", size=10)
        partitionMax = max(self.partition_list, key = len)
        self.PartitionListMaxLength = f1.measure(partitionMax) + 25
        dtlogger.debug(self.PartitionListMaxLength)
        dtlogger.debug(self.partition_list)
        self.create_select_window()

    def create_select_window(self):
        self.popup_win = tk.Toplevel(master=self.root)
        self.popup_win.attributes('-alpha', 0)
        screenwidth = self.popup_win.winfo_screenwidth()
        screenheight = self.popup_win.winfo_screenheight()

        self.popup_win.title(self.title)
        self.popup_win.attributes('-topmost', 1)
        self.popup_win.protocol("WM_DELETE_WINDOW", self.dt_select_popup_close)
        self.popup_win.grab_set()

        main_frame = tk.Frame(self.popup_win, width=270+self.PartitionListMaxLength, height=60)
        main_frame.pack(anchor="w", padx=5, pady=10, side="top")
        partition_label = tk.Label(main_frame, text="Partition Name:", anchor="w", font=("Times New Roman", 11, "bold"))
        partition_label.place(x=5, y=10, width=120, height=30)

        
        self.partition_combobox = ttk.Combobox(main_frame, values=self.partition_list, font=("TkFixedFont", 10))
        self.partition_combobox.place(x=130, y=10, width=self.PartitionListMaxLength, height=30)
        self.partition_combobox.current(0)
        # partition_combobox.bind("<<ComboboxSelected>>", self.call_select_partition)

        read_bt = ttk.Button(main_frame, text="Read Partition", command=self.call_read_partition_bt)
        read_bt.place(x=150+self.PartitionListMaxLength, y=10, width=100, height=30)

        self.popup_win.geometry("+%d+%d" % ((screenwidth - 400) / 2, (screenheight - 200) / 2))
        self.popup_win.resizable(0, 0)
        self.popup_win.attributes('-alpha', 1)

    def call_read_partition_bt(self):
        partition_name = self.partition_list[self.partition_combobox.current()]
        if not partition_name:
            tkinter.messagebox.showerror(parent=self.popup_win, title="Error", message="Please select a valid partition name\n")
            return False

        gf['partition_name'] = partition_name
        gf['partition_name_flag'] = 1
        self.popup_win.destroy()

    def dt_select_popup_close(self):
        gf['partition_name'] = ""
        gf['partition_name_flag'] = 255
        self.popup_win.destroy()


class DT_ProgressBar():
    title = "Waiting..."

    def __init__(self, root):
        self.root = root
        self.create_main_win()

    def create_main_win(self):
        self.popup_win = tk.Toplevel(master=self.root, height=1, width=1)
        self.popup_win.attributes('-alpha', 0)
        screenwidth = self.popup_win.winfo_screenwidth()
        screenheight = self.popup_win.winfo_screenheight()

        self.popup_win.title(self.title)
        self.popup_win.attributes('-topmost', 1)
        self.popup_win.grab_set()
        self.popup_win.protocol("WM_DELETE_WINDOW", self.call_popup_close)
        #self.popup_win.attributes("-toolwindow", 1)

        main_frame = tk.Frame(self.popup_win, width=400, height=200)
        main_frame.pack(anchor="w", padx=5, pady=10, side="top")
        self.progressbarOne = tkinter.ttk.Progressbar(main_frame, length=300, mode='indeterminate', orient=tkinter.HORIZONTAL)
        self.progressbarOne.pack(pady=10)
        self.progressbarOne.start()
        self.popup_win.geometry("+%d+%d" % ((screenwidth - 300) / 2, (screenheight - 200) / 2))
        self.popup_win.resizable(0, 0)
        self.popup_win.attributes('-alpha', 1)

    def call_popup_close(self):
        self.popup_win.destroy()




class DT_Write_GUI():
    select_width = 500
    title = "Write EFL File with DTBs"

    def __init__(self, root, _dt_dict):
        self.root = root
        self.dt_dict = _dt_dict
        self.partition_list = [item for item in self.dt_dict]
        self.checkbutton_state = "normal"
        f1=tkFont.Font(family="TkFixedFont", size=10)
        partitionMax = max(self.partition_list, key = len)
        self.PartitionListMaxLength = f1.measure(partitionMax) + 25
        self.create_select_window()

    def check_A_B_partition(self,sel_partition):
        partition_postfix_regex="(_(BACKUP|a|b)){1}$"
        m = re.search(partition_postfix_regex,sel_partition,re.I)
        if m:
            return "normal"
        else:
            if len([x for x in self.partition_list if (sel_partition in x)])==2:
                return "normal"
        return "disable"

    def update_checkbutton_state(self,event):
        sel_partition_name = self.partition_list[self.partition_combobox.current()]
        self.pacheckbutton_state = self.check_A_B_partition(sel_partition_name)
        if self.pacheckbutton_state == "disable":
            self.check_var.set(0)
        else:
            self.check_var.set(1)
        self.check_bt.config(state=self.pacheckbutton_state)

    def create_select_window(self):
        self.popup_win = tk.Toplevel(master=self.root)
        self.popup_win.attributes('-alpha', 0)
        screenwidth = self.popup_win.winfo_screenwidth()
        screenheight = self.popup_win.winfo_screenheight()
        
        self.popup_win.title(self.title)
        # self.popup_win.attributes('-topmost', 1)
        self.popup_win.protocol("WM_DELETE_WINDOW", self.dt_flash_close)
        self.popup_win.grab_set()

        main_frame = tk.LabelFrame(self.popup_win, text="Write EFL File with DTBs",
                                   font=("Times New Roman", 11, "bold"), width=400+self.PartitionListMaxLength, height=120)
        
        main_frame.pack(anchor="w", padx=5, pady=10, side="top")
        image_label = tk.Label(main_frame, text="Image:", anchor="w", font=("Times New Roman", 11, "bold"))
        image_label.place(x=5, y=10, width=50, height=30)

        self.partition_combobox = ttk.Combobox(main_frame, values=self.partition_list, font=("TkFixedFont", 10))
        self.partition_combobox.place(x=60, y=10, width=self.PartitionListMaxLength, height=30)
        self.partition_combobox.current(0)
        self.partition_combobox.bind('<<ComboboxSelected>>',self.update_checkbutton_state)

        self.image_entry = tk.Entry(main_frame, state="normal", font=("Courier New", 11))
        self.image_entry.place(x=60+self.PartitionListMaxLength+5, y=10, width=260, height=30)
        image_bt = ttk.Button(main_frame, text="Browse", style="my.TButton", command=self.call_image_select_bt)
        image_bt.place(x=320+self.PartitionListMaxLength+10, y=10, width=60, height=30)

        confirm_bt = ttk.Button(main_frame, text="FLASH", style="my.TButton", command=self.call_confirm_select_bt)
        confirm_bt.place(x=320+self.PartitionListMaxLength+10, y=60, width=60, height=30)

        self.check_var=tk.IntVar()
        self.checkbutton_state=self.check_A_B_partition(self.partition_list[0])
        self.check_bt = tk.Checkbutton(main_frame, text="Write A & B Partition Both", state=self.checkbutton_state,variable=self.check_var, onvalue=1, offvalue=0, command=self.call_check_select_bt,


        font=("Times New Roman", 11, "bold"))
        self.check_bt.place(x=10, y=60, width=200, height=30)
        # dtlogger.info(self.check_var.get())
        if self.checkbutton_state == "disable":
            self.check_bt.deselect()
        else:
            self.check_bt.select()
        self.popup_win.geometry("+%d+%d" % ((screenwidth-500)/2, (screenheight-200)/2))
        self.popup_win.resizable(0, 0)
        self.popup_win.attributes('-alpha', 1)

    def call_image_select_bt(self):
        _filetypes = [('Image File', '*.elf'), ('Image File', '*.bin'), ('All Files', '*.*')]

        image_path = tkinter.filedialog.askopenfilename(parent=self.popup_win, title="Select ELF File with DTBs",
                                                        defaultextension='.elf', filetypes=_filetypes)
        if os.path.exists(image_path):
            image_path = os.path.normpath(image_path)
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, image_path)

    def call_confirm_select_bt(self):
        gf['PartitionImage_Flag'] = 0
        gf['PartitionImage'] = ""
        gf['PartitionName'] = ""
        gf['PartitionABCheck'] = 0

        partition_name = self.partition_list[self.partition_combobox.current()]
        image_path = self.image_entry.get().strip()
        dtlogger.debug("Image File: {}".format(image_path))
        if not os.path.exists(image_path):
            tkinter.messagebox.showerror(parent=self.popup_win, title="Error", message="Please select a valid Image File.\n")
            return False

        gf['PartitionName'] = partition_name
        gf['PartitionImage'] = image_path
        gf['PartitionImage_Flag'] = 1
        if self.check_var.get():
            gf['PartitionABCheck'] = 1
        self.popup_win.destroy()

    def call_check_select_bt(self):
        dtlogger.info(self.check_var.get())

    def dt_flash_close(self):
        gf['PartitionImage_Flag'] = 255
        self.popup_win.destroy()


class XblDirGUI():
    select_width = 500
    title = "Input The DTB/DTBO elf file"

    # ttk.Style().configure("my.TButton", anchor="center", font=("Times New Roman", 12, "bold"))

    def __init__(self, root):
        self.root = root
        self.jsonx = Json_Operate()
        self.create_select_window()
        self.sectool_name = sectool_name

    def create_select_window(self):
        self.popup_win = tk.Toplevel(master=self.root)
        self.popup_win.attributes('-alpha', 0)
        screenwidth = self.popup_win.winfo_screenwidth()
        screenheight = self.popup_win.winfo_screenheight()

        self.popup_win.title(self.title)
        self.popup_win.attributes('-topmost', 1)
        self.popup_win.protocol("WM_DELETE_WINDOW", self.xbl_popup_close)
        self.popup_win.grab_set()

        main_frame = tk.Frame(self.popup_win, width=self.select_width-10, height=90)
        main_frame.pack(anchor="w", padx=5, pady=10, side="top")
        image_label = tk.Label(main_frame, text="ELF file with DTBs (eg: XBLConfig.elf, Q6_MPSS_DTB.elf):",
                               anchor="w", font=("Times New Roman", 11, "bold"))
        image_label.place(x=5, y=0, width=420, height=25)
        self.image_entry = tk.Entry(main_frame, state="normal", font=("Courier New", 11))
        self.image_entry.place(x=5, y=25, width=415, height=30)
        image_bt = ttk.Button(main_frame, text="Browse", style="my.TButton", command=self.call_xblcfgimage_select_bt)
        image_bt.place(x=425, y=25, width=60, height=30)

        confirm_bt = ttk.Button(main_frame, text="OK", style="my.TButton", command=self.call_confirm_select_bt)
        confirm_bt.place(x=220, y=60, width=60, height=30)

        self.popup_win.geometry("+%d+%d" % ((screenwidth - 500) / 2, (screenheight - 300) / 2))
        self.popup_win.resizable(0, 0)
        self.popup_win.attributes('-alpha', 1)


        xblcfgimage_path = self.jsonx.read_json_cfg_data("inputFile")
        if xblcfgimage_path and os.path.exists(xblcfgimage_path):
            self.image_entry.insert(0, os.path.normpath(xblcfgimage_path))

    def call_cfg_tool_select_bt(self):
        initialdir_path = self.jsonx.read_json_cfg_data("xbltoolsDir")
        cfg_tool_path = tkinter.filedialog.askdirectory(
            parent=self.popup_win, title="Select GenConfigimage/GenXBLConfig Tool Path", initialdir=initialdir_path)
        if os.path.exists(cfg_tool_path):
            cfg_tool_path = os.path.normpath(cfg_tool_path)
            self.cfg_tool_entry.delete(0, "end")
            self.cfg_tool_entry.insert(0, cfg_tool_path)

    def call_xblcfgimage_select_bt(self):
        initialdir_path = os.path.dirname(self.jsonx.read_json_cfg_data("inputFile"))
        image_path = tkinter.filedialog.askopenfilename(parent=self.popup_win, title="Select Elf File with DTBs",
                                                        initialdir=initialdir_path, defaultextension='.elf', filetypes=[('ELF File With DTBs', '*.elf'), ('All Files', '*.*')])
        if os.path.exists(image_path):
            image_path = os.path.normpath(image_path)
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, image_path)

    def call_confirm_select_bt(self):
        image_path = self.image_entry.get().strip()
        dtlogger.debug("Elf File with DTBs: {}".format(image_path))

        if not os.path.exists(image_path):
            tkinter.messagebox.showerror(parent=self.popup_win, title="Error", message="Please select a valid Elf File with DTBs.\n")
            return False

        gf['inputFile'] = image_path
        gf['XBLConfigFlag'] = 1

        self.jsonx.update_json_cfg_data()
        self.popup_win.destroy()

    def xbl_popup_close(self):
        gf['XBLConfigFlag'] = 255
        self.popup_win.destroy()


class Json_Partition_Operate():
    def __init__(self, partitionPath):
        self.filename = partitionPath
        if not os.path.exists(self.filename):
            os.makedirs(os.path.dirname(self.filename), mode=0o777, exist_ok=True)
            self.create_json_partition_data()

    def create_json_partition_data(self):
        json_dict = {
            "format": " * or (*|*)",
            "partition": "(xbl_config|dtb)",
            "partitionBan": "dtb"
        }
        try:
            with open(self.filename, mode='w', encoding="utf-8") as fp:
                json.dump(json_dict, fp, indent=4, separators=(',', ': '))
        except Exception:
            dtlogger.debug('Error of creating partition_name json file.')

    def read_json_partition_data(self):
        try:
            with open(self.filename, mode='r', encoding="utf-8") as fp:
                partitionName = json.load(fp)
            if not partitionName:
                self.create_json_partition_data()
                partitionName=self.read_json_partition_data()
            return partitionName
        except Exception:
            dtlogger.debug('Error of reading partition_name json file.')
            return None




# if __name__ == "__main__":
#     root = tk.Tk()
#     root.withdraw()
#     a = ["a", "b", "c"]
#     sub = DT_Write_GUI(root, a)
#     root.mainloop()
