# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from cmath import exp
from logging import exception
from operator import ge
from tkinter import W
from XBLConfig import elf_gen_tools
from flags import flags as gf
import subprocess
import os
from fs import open_fs
import datetime
import time
import os
import re
import fs.opener
from pyfatfs.PyFatFSOpener import PyFatFSOpener
import dtlogger

fs.opener.registry.install(PyFatFSOpener)

name_regex="([a-z,A-Z]+_(dtb|DTB|dtbs|config)).(((b|B)\d+)|mdt|MDT|bin|mbn|elf){1}"

class nhlos_Operator:
    dtb_files = {}
    dtb_files_name = []
    nhlos_handler = None

    def get_dict_key(self,master_key,search_key):
        for dict_key in self.dtb_files[master_key].keys():
            m = re.search(search_key,dict_key,re.l)
            if m:
               return m.group(0)
        return None

    def get_dtb_elf_names(self,nhlos_image):
        try:
            with open_fs("fat://"+nhlos_image.replace("\\","//")) as self.nhlos_handler: 
                #files_tree =  self.nhlos_handler.tree()
                #dtlogger.info("Files in nonhlos binary:{}".format(files_tree))
                for path in self.nhlos_handler.walk.files(filter=['*dtb.*','*DTB.*','*dtbs.*','*xbl_config.*']):
                    dtlogger.debug(path)
                    dtlogger.debug(os.path.basename(path))
                    m = re.search(name_regex,path)
                    if m :
                        # save dtb split binary path in non_hlos binary
                        dtlogger.debug(m.group(1))
                        if m.group(1) not in self.dtb_files:
                            self.dtb_files[m.group(1)] = {}
                        self.dtb_files[m.group(1)][os.path.basename(path)]=path
                        if m.group(1) not in self.dtb_files_name:
                            self.dtb_files_name.append(m.group(1))
                            dtlogger.debug(m.group(1))
                dtlogger.debug(self.dtb_files_name)
                self.nhlos_handler.close()
        except Exception as e:
            dtlogger.error(e)
            if "Is this a FAT partition?" in e.args:
                dtlogger.debug("this is not FAT partition")
                return None
        return self.dtb_files_name
    
    def extract_dtb_elf_file(self, dtb_elf_name, nhlos_image, output_path):
        split_b00_file_name = None
        elf_header = {}
        phdr_table = {}
        input_file = None

        # merge dtb files into elf
        Lb = ''
        Lb=list(self.dtb_files[dtb_elf_name].keys())[0].split('.')[1][0]
        if Lb=='':
            dtlogger.debug("b00 split bin can't be found!")
            return False
        nhlos_handler = open_fs("fat://"+nhlos_image.replace("\\","//"))
        try:
                phdr_num = 1
                i = 0
                write_file = None
                while (i < phdr_num):
                    dtb_file_full_name = "{}.{}{:0>2d}".format(dtb_elf_name,Lb,i)
                    dtlogger.debug(dtb_file_full_name)
                    dtb_file_path = None
                    dtb_file_path = self.dtb_files[dtb_elf_name][dtb_file_full_name]
                    if dtb_file_path != None:
                        dtlogger.debug(dtb_file_path)
                        dtlogger.debug("start read file:.{}".format(dtb_file_path))
                        if i == 0 :
                            write_file = open(os.path.join(output_path,"{}.elf".format(dtb_elf_name)),"wb")
                        else:
                            write_file = open(os.path.join(output_path,"{}.elf".format(dtb_elf_name)),"rb+")

                        with nhlos_handler.open(dtb_file_path,"rb") as input_file_fp:
                            data = input_file_fp.read()
                            input_file_fp.close()
                            if i != 0 :
                                dtlogger.debug("write {} start offset {}".format(dtb_file_full_name,phdr_table[i].p_offset))
                                write_file.seek(phdr_table[i].p_offset)

                            dtlogger.debug("write file offset: %s" % write_file.tell())
                            write_file.write(data)
                            write_file.close()
                            if i == 0:
                                [elf_header, phdr_table] = \
                                        elf_gen_tools.preprocess_elf_file(os.path.join(output_path,"{}.elf".format(dtb_elf_name)))
                                phdr_num =  elf_header.e_phnum
                            
                            dtlogger.debug("end read file:.{}".format(dtb_file_path))
                            i = i + 1
                    else:

                        break
        except Exception as e:
            dtlogger.error(e)
        nhlos_handler.close()

    def write_dtb_elf_into_nhlos_file(self, dtb_elf_name, nhlos_image, dtb_elf,output_path):

        Lb =''
        Lb=list(self.dtb_files[dtb_elf_name].keys())[0].split('.')[1][0]
        #split dtb elf file
        try:
            phdr_num = 0
            i = 0
            write_file = None
            [elf_header, phdr_table] = \
                                    elf_gen_tools.preprocess_elf_file(dtb_elf)
            phdr_num =  elf_header.e_phnum

            #call elf_gen script to dissamble dtb elf file
            subprocess.check_call(["python",os.path.join(gf["xbltoolsDir"],"elf_gen.py"),
                                   "-d",dtb_elf,
                                   "-e",os.path.join(output_path,dtb_elf_name),
                                   "-o",output_path])

            #rename segment name and create mdt file
            mdt_fp =  open(os.path.join(output_path,"{}.mdt".format(dtb_elf_name)),"wb+")
  
            nhlos_handler = open_fs("fat://"+nhlos_image.replace("\\","//"))
            for i in range (phdr_num):          
                dtb_file_full_name = "{}.{}{:0>2d}".format(dtb_elf_name,Lb,i)
                dtlogger.debug(dtb_file_full_name)
                dtb_file_path = None
                dtb_file_path = self.dtb_files[dtb_elf_name][dtb_file_full_name]
                if dtb_file_path != None:
                    dtlogger.debug("dtb file path:%s" % dtb_file_path)
                    dtlogger.debug("start read file:.{}".format(dtb_file_path))
                    input_file_size = os.path.getsize(os.path.join(output_path,"segment_{}.bin".format(i)))
                    input_file_fp = open(os.path.join(output_path,"segment_{}.bin".format(i)),"rb")
                    write_file_size = 0
                    if nhlos_handler.exists(dtb_file_path):
                        nhlos_handler.remove(dtb_file_path)
                    dtb_file_path= os.path.dirname(dtb_file_path)+"/"+os.path.basename(dtb_file_path).lower()
                    with nhlos_handler.open(dtb_file_path,"wb") as output_file_fp:
                        while write_file_size < input_file_size:
                            data = input_file_fp.read(1024)
                            output_file_fp.write(data)
                            write_file_size+=1024
                        output_file_fp.close()
                    input_file_fp.close()

                    #write eheader,pheader and hash segment into mdt file
                    if i==0 or i == (phdr_num -1):
                        mdt_fp.write(data)

                else:
                    break
            #write mdt 
            dtb_mdt_name = ''
            if Lb == 'B':
                dtb_mdt_name = "{}.MDT".format(dtb_elf_name)
            else:
                dtb_mdt_name = "{}.mdt".format(dtb_elf_name)

            dtb_mdt_path = self.dtb_files[dtb_elf_name][dtb_mdt_name]
            
            mdt_fp.seek(0)
            mdt_data=mdt_fp.read()
            mdt_fp.close()
            if nhlos_handler.exists(dtb_mdt_path):
              nhlos_handler.remove(dtb_mdt_path)
            dtb_mdt_path = os.path.dirname(dtb_mdt_path)+"/"+os.path.basename(dtb_mdt_path).lower()
            with nhlos_handler.open(dtb_mdt_path,"wb") as output_file_fp:
                dtlogger.debug("write data to file: %s" % dtb_mdt_path)
                output_file_fp.write(mdt_data)
                output_file_fp.close()
                dtlogger.debug("write file:{} done".format(dtb_mdt_path))
            nhlos_handler.close()
        except Exception as e:
            nhlos_handler.close()
            dtlogger.error(e)
