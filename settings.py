# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
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
import dtlogger

ITEMS_ALL = 0
ITEMS_SECTOOL = 1
ITEMS_DEVPRG = 2

class Json_Operate():
    def __init__(self):
        self.filename = gl_info["user_cfg"]
        data = {}
        #if user_cfg json file doesn't exist, create a new one.
        if not os.path.exists(self.filename):
            #if QDTE folder doesn't exist, make a new folder.
            os.makedirs(os.path.dirname(gl_info["user_cfg"]), mode=0o777, exist_ok=True)
            json_dict = {
                "paths": {
                    "xbltoolsDir": "",
                    "inputFile": "",
                    "buildcfg_path": "",
                    "sectoolsDir": "",
                    "profileXml": "",
                    "devprg": "",
                    "signJson": "",
                    "savefilepath":"",
                    "configed":"False",
                },
                "options":{
                    "flashtype":"UFS",
                }
            }
            try:
                #create a user_cfg json file.
                with open(self.filename, mode='w', encoding="utf-8") as fp:
                    json.dump(json_dict, fp, indent=4, separators=(',', ': '))
            except Exception:
                dtlogger.info('Error of creating cfg json file.')
        else:
            try:
                with open(self.filename, mode='r', encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                dtlogger.info('Error of opening cfg json file.')
                return False
            if data:
                if "paths" in data:
                    if "xbltoolsDir" in data["paths"]:
                        gf['xbltoolsDir'] = data["paths"]["xbltoolsDir"]

                    if "sectoolsDir" in data["paths"] :
                        gf['sectoolsDir'] =  data["paths"]["sectoolsDir"]

                    if "profileXml" in data["paths"] :
                        gf['profileXml'] = data["paths"]["profileXml"] 

                    if "signJson" in data["paths"] :
                        gf['signJson'] = data["paths"]["signJson"] 
                    
                    if "devprg" in data["paths"] :
                        gf['devprg'] = data["paths"]["devprg"]
                
                if "options" in data and "flashtype" in data["options"]:
                    gf['flashtype'] = data["options"]["flashtype"]
                else:
                    gf['flashtype'] = "UFS"
                    self.update_json_cfg_data()

        # init global parameters
        if os.path.exists(os.path.join(os.path.dirname(__file__),'XBLConfig')):
            gf['xbltoolsDir'] = os.path.join(os.path.dirname(__file__),'XBLConfig')
        else:
            gf['xbltoolsDir'] = os.path.join(gl_info['sign_json_path'],'XBLConfig')



    def read_json_cfg_data(self, select):
        data = {}
        return_value = ""

        try:
            with open(self.filename, mode='r', encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            dtlogger.info('Error of reading cfg json file due to {}'.format(e))

        if data:
            if "paths" in data and select in data["paths"] and data["paths"][select] and os.path.exists(data["paths"][select]):
                return_value = data["paths"][select]
            elif "options" in data and select in data["options"]:
                return_value = data["options"][select]

        return return_value
    
    def check_json_items(self,items):
        if items == ITEMS_ALL:
            return False
        if items == ITEMS_DEVPRG:
            if self.read_json_cfg_data("devprg")=='':  
                return False
        if items == ITEMS_SECTOOL:
            if self.read_json_cfg_data('sectoolsDir')=="" or self.read_json_cfg_data('profileXml')==''\
               or self.read_json_cfg_data('signJson') == '':
               return False
        return True

    def update_json_cfg_data(self):
        data = {}

        try:
            with open(self.filename, mode='r', encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            dtlogger.info('Error of opening cfg json file.')
            return False
            # raise Exception("Error of opening json file")
        if data:
            if  "paths" not in data:
                data["paths"]={}
            if "xbltoolsDir" in gf and gf['xbltoolsDir']:
                data["paths"]["xbltoolsDir"] = gf['xbltoolsDir']
            if "inputFile" in gf and gf['inputFile']:
                data["paths"]["inputFile"] = gf['inputFile']
            if "buildcfg_path" in gf and gf['buildcfg_path']:
                data["paths"]["buildcfg_path"] = gf['buildcfg_path']
            if "sectoolsDir" in gf and gf['sectoolsDir']:
                data["paths"]["sectoolsDir"] = gf['sectoolsDir']
            if "profileXml" in gf and gf['profileXml']:
                data["paths"]["profileXml"] = gf['profileXml']
            if "devprg" in gf and gf['devprg']:
                data["paths"]["devprg"] = gf['devprg']
            if "signJson" in gf and gf['signJson']:
                data["paths"]["signJson"] = gf['signJson']

            if "flashtype" in gf and gf['flashtype']:
                if "options" not in data:
                    data["options"] = {}
                data["options"]["flashtype"] = gf['flashtype']


            try:
                os.chmod(self.filename, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                with open(self.filename, mode='w', encoding="utf-8") as fp:
                    json.dump(data, fp, indent=4, separators=(',', ': '))
            except Exception:
                dtlogger.info('Error of writing cfg json file.')
                # raise Exception("Error of writing json file")


class Settings():
    select_width = 550
    title = "Settings"
    params_list = []

    def __init__(self, root, setting_items=ITEMS_ALL):
        self.root = root
        self.jsonx = Json_Operate()
        self.setting_items = setting_items
        if self.jsonx.check_json_items(setting_items) == False:
            self.create_settings_window()
        elif setting_items == ITEMS_SECTOOL or setting_items == ITEMS_DEVPRG:
            gf["setting_flag"] = 1

        self.sectool_name = 'v2'

    def create_settings_window(self):
        star = ""
        self.popup_win2 = tk.Toplevel(master=self.root)
        self.popup_win2.attributes('-alpha', 0)
        screenwidth = self.popup_win2.winfo_screenwidth()
        screenheight = self.popup_win2.winfo_screenheight()
        self.popup_win2.title(self.title)
        self.popup_win2.protocol("WM_DELETE_WINDOW", self.sign_popup_close)
        self.popup_win2.grab_set()
        if self.setting_items == ITEMS_SECTOOL:
            star ='*'
        else:
            star = ''
        
        start_x = 5
        start_y = 5
        lable_width = 200
        entry_width = 460
        combobox_width = 120
        bt_width = 60
        bt_start_x = start_x + entry_width + 5
        row_height = 30

        self.tool_frame = tk.LabelFrame(self.popup_win2, text="{}signature configurations:".format(star), width=self.select_width -
                                        10, height=(start_y+row_height)*6+40, font=("Times New Roman", 12, "bold"))
        self.tool_frame.pack(anchor="w", padx=5, pady=5)
        sec_tool_label = tk.Label(self.tool_frame, text="SecTool Path", anchor="w", font=("Times New Roman", 11, "bold"))
        sec_tool_label.place(x=start_x, y=start_y, width=lable_width, height=row_height)
        self.sec_tool_entry = tk.Entry(self.tool_frame, font=("Courier New", 11))
        self.sec_tool_entry.place(x=start_x, y=start_y+row_height, width=entry_width, height=row_height)
        self.sec_tool_bt = ttk.Button(self.tool_frame, text="Browse", style="my.TButton", command=self.call_sec_tool_select_bt)
        self.sec_tool_bt.place(x=bt_start_x, y=start_y+row_height, width=bt_width, height=row_height)

        profile_label = tk.Label(self.tool_frame, text="Profile File", anchor="w", font=("Times New Roman", 11, "bold"))
        profile_label.place(x=start_x, y=(start_y+row_height)*2, width=lable_width, height=row_height)
        self.profile_entry = tk.Entry(self.tool_frame, font=("Courier New", 11))
        self.profile_entry.place(x=start_x, y=(start_y+row_height)*3, width=entry_width, height=row_height)
        self.profile_bt = ttk.Button(self.tool_frame, text="Browse", style="my.TButton", command=self.call_profile_select_bt)
        self.profile_bt.place(x=bt_start_x, y=(start_y+row_height)*3, width=bt_width, height=row_height)

        sign_label = tk.Label(self.tool_frame, text="Sign cmd json", anchor="w", font=("Times New Roman", 11, "bold"))
        sign_label.place(x=start_x, y=(start_y+row_height)*4, width=lable_width, height=row_height)
        self.sign_entry = tk.Entry(self.tool_frame, font=("Courier New", 11))
        self.sign_entry.place(x=start_x, y=(start_y+row_height)*5, width=entry_width, height=row_height)
        self.sign_bt = ttk.Button(self.tool_frame, text="Browse", style="my.TButton", command=self.call_sign_select_bt)
        self.sign_bt.place(x=bt_start_x, y=(start_y+row_height)*5, width=bt_width, height=row_height)

        if self.setting_items == ITEMS_DEVPRG:
            star ='*'
        else:
            star = ''
        self.devprg_frame = tk.LabelFrame(self.popup_win2, text="{}device programmer files:".format(star), width=self.select_width -
                                        10, height=(start_y+row_height)*4+40, font=("Times New Roman", 12, "bold"))
        self.devprg_frame.pack(anchor="w", padx=5, pady=5)
        prg_label = tk.Label(self.devprg_frame, text="Meta build path:", anchor="w", font=("Times New Roman", 11, "bold"))
        prg_label.place(x=start_x, y=start_y, width=lable_width, height=row_height)

        self.prg_entry = tk.Entry(self.devprg_frame, state="normal", font=("Courier New", 11))
        self.prg_entry.place(x=start_x, y=(start_y+row_height), width=entry_width, height=row_height)

        prg_bt = ttk.Button(self.devprg_frame, text="Browse", style="my.TButton", command=self.call_prg_select_bt)
        prg_bt.place(x=bt_start_x, y=(start_y+row_height), width=bt_width, height=row_height)
        devprg_path = self.jsonx.read_json_cfg_data("devprg")
        if devprg_path :
            self.prg_entry.insert(0, os.path.normpath(devprg_path))

        '''
        Flash type select list
        '''
        Flash_type_label = tk.Label(self.devprg_frame, text="Flash type:", anchor="w", font=("Times New Roman", 11, "bold"))
        Flash_type_label.place(x=start_x, y=(start_y+row_height)*2, width=lable_width, height=row_height)

        Flash_type_val = tk.StringVar()
        self.Flash_type = ttk.Combobox(self.devprg_frame, textvariable=Flash_type_val, state="readonly")
        self.Flash_type.place(x=start_x, y=(start_y+row_height)*3, width = combobox_width,height= row_height)
        self.Flash_type['values'] = ("UFS","SPINOR","EMMC","NVME")
        flash_type = self.jsonx.read_json_cfg_data("flashtype")
        dtlogger.info("flash_type is {}".format(flash_type))
        self.Flash_type.set(flash_type)   

        self.tip_frame = tk.Frame(self.popup_win2, width=self.select_width - 10, height=80)
        self.tip_frame.pack(anchor="w", padx=5)

        self.profile_name = ""
        gf['sectools_ver'] = 'v2'

        self.fill_entry(self.sec_tool_entry, "sectoolsDir")
        self.fill_entry(self.profile_entry, "profileXml")
        self.fill_entry(self.sign_entry, "signJson")

        if self.profile_entry.get():
            profile_item = self.profile_entry.get()
            profile_item = os.path.normpath(profile_item)
            self.profile_name = os.path.basename(profile_item)
            split_list = profile_item.split(os.sep)
        else:
            self.profile_name = ' '
            split_list = [' ','']

        tip_info = "1. Sectool  Path:Sectools v2 installation path\n"+\
                   "2. Profile  file:Siging xml files like <chipset>_[tme|tz]_security_profile.xml \n"+\
                   "3. Sign cmd json:xxx_signing_mode.json file from QDTE installation directory\n"+\
                   "Note: * items are mandantory\n"
        self.var = tk.StringVar()
        self.var.set(tip_info)
        tip_label = tk.Message(self.tip_frame, textvariable=self.var, anchor="w", width=550, font=("Times New Roman", 11))
        tip_label.place(x=5, y=5, width=550, height=80)

        self.confirm_frame = tk.Frame(self.popup_win2, width=self.select_width-10, height=40)
        self.confirm_frame.pack(anchor="w", padx=5, pady=5)
        confirm_bt = ttk.Button(self.confirm_frame, text="OK", style="my.TButton", command=self.call_confirm_select_bt)
        confirm_bt.place(x=220, y=5, width=80, height=30)

        self.popup_win2.geometry("+%d+%d" % ((screenwidth - 550) / 2, (screenheight - 300) / 2))
        self.popup_win2.resizable(0, 0)
        self.popup_win2.attributes('-alpha', 1)
        self.popup_win2.wait_window()

    def fill_entry(self, x_entry, select):
        path = self.jsonx.read_json_cfg_data(select)
        if path and os.path.exists(path):
            x_entry.configure(state="normal")
            x_entry.delete(0, "end")
            x_entry.insert(0, os.path.normpath(path))

    def clear_entry(self, x_entry):
        x_entry.configure(state="normal")
        x_entry.delete(0, "end")

    def call_confirm_select_bt(self):
        profile_path = self.profile_entry.get().strip()
        sign_path = self.sign_entry.get().strip()
        sec_tool_path = self.sec_tool_entry.get().strip()
        prg_path = self.prg_entry.get().strip()
        flash_type = self.Flash_type.get().strip()
        dtlogger.info("profile file Path: "+profile_path)
        dtlogger.info("SecTool Path: "+sec_tool_path)
        dtlogger.info("Signing json File: "+sign_path)
        dtlogger.info("Programmer File: "+prg_path)
        dtlogger.info("Flash type:"+flash_type)

        if (self.setting_items == ITEMS_ALL and sec_tool_path!='') or self.setting_items== ITEMS_SECTOOL:
            if not os.path.exists(sec_tool_path):
                tkinter.messagebox.showerror(parent=self.popup_win2, title="Error", message="Please select a valid SecTool.\n")
                return False
        if (self.setting_items == ITEMS_ALL and profile_path!='') or self.setting_items== ITEMS_SECTOOL:
            if not os.path.exists(profile_path):
                tkinter.messagebox.showerror(parent=self.popup_win2, title="Error", message="Please select a valid profile file Path.\n")
                return False
            
        if (self.setting_items == ITEMS_ALL and sign_path!='') or self.setting_items== ITEMS_SECTOOL:
            if not os.path.exists(sign_path):
                tkinter.messagebox.showerror(parent=self.popup_win2, title="Error", message="Please select a valid signing mode file Path.\n")
                return False

            
        gf['sectoolsDir'] = sec_tool_path
        gf['profileXml'] = profile_path
        gf['signJson'] = sign_path
        gf['flashtype'] = flash_type
        if (self.setting_items == ITEMS_ALL and prg_path!='') or self.setting_items == ITEMS_DEVPRG:
            if not os.path.exists(prg_path):
                tkinter.messagebox.showerror(parent=self.popup_win2, title="Error", message="Not a valid meta path\n")
                return False
        gf['devprg'] = prg_path
            
        if self.setting_items != ITEMS_ALL:
            gf["setting_flag"] = 1

        self.jsonx.update_json_cfg_data()
        self.popup_win2.destroy()

   
    def call_sec_tool_select_bt(self):
        initialdir_path = self.jsonx.read_json_cfg_data("sectoolsDir")
        sec_tool_path = tkinter.filedialog.askdirectory(parent=self.popup_win2, title="Select SecTool Path", initialdir=initialdir_path)
        if os.path.exists(sec_tool_path):
            sec_tool_path = os.path.normpath(sec_tool_path)
            self.sec_tool_entry.delete(0, "end")
            self.sec_tool_entry.insert(0, sec_tool_path)

    def call_profile_select_bt(self):
        initialdir_path = ""
        initialdir_path = os.path.dirname(self.jsonx.read_json_cfg_data("profileXml"))

        profile_path = tkinter.filedialog.askopenfilename(parent=self.popup_win2, title="Select Profile File",
                                                          initialdir=initialdir_path, defaultextension='.xml', filetypes=[('xml file', "*.xml"), ('All Files', '*.*')])
        if len(profile_path) != 0:
          if os.path.exists(profile_path):
            profile_path = os.path.normpath(profile_path)
            self.profile_entry.delete(0, "end")
            self.profile_entry.insert(0, profile_path)
            profile_item = self.profile_entry.get()
            profile_item = os.path.normpath(profile_item)
            self.profile_name = os.path.basename(profile_item)
            split_list = profile_item.split(os.sep)
            tip_info = "1. Sectool version: %s\n2. Profile file: %s  (From the folder: %s)" % (gf['sectools_ver'], self.profile_name, split_list[-2])
            self.var.set(tip_info)

    def call_sign_select_bt(self):
        initialdir_path = os.path.dirname(self.jsonx.read_json_cfg_data("signJson"))
        if initialdir_path == '':
          initialdir_path = gl_info['sign_json_path']
        sign_path = tkinter.filedialog.askopenfilename(parent=self.popup_win2, title="Select signing command json File",
                                                          initialdir=initialdir_path, defaultextension='.json', filetypes=[('json file', "*.json"), ('All Files', '*.*')])

        if os.path.exists(sign_path):
            sign_path = os.path.normpath(sign_path)
            self.sign_entry.delete(0, "end")
            self.sign_entry.insert(0, sign_path)

    def call_prg_select_bt(self):
        #_filetypes = [('Programmer File', '*.melf'), ('Programmer File', '*.elf'), ('All Files', '*.*')]
        initialdir_path = os.path.dirname(self.jsonx.read_json_cfg_data("devprg"))
        prg_path = tkinter.filedialog.askdirectory(
            parent=self.popup_win2, title="Select meta build path", initialdir=initialdir_path)
        if prg_path:
            prg_path = os.path.normpath(prg_path)
            self.prg_entry.delete(0, "end")
            self.prg_entry.insert(0, prg_path)

    def call_devconfirm_select_bt(self):
        prg_path = self.prg_entry.get().strip()
        if not os.path.exists(prg_path):
            tkinter.messagebox.showerror(parent=self.popup_win2, title="Error", message="Not a valid meta path\n")
            return False
    def sign_popup_close(self):
        gf["setting_flag"] = 255
        self.setting_processing = False
        self.popup_win2.destroy()
