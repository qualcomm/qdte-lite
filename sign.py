#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file sign.py
This file contains the interface of signature. it will call sectools v2 for signing. 
"""
#from asyncio import exceptions
from dis import disassemble
import os
import sys
import subprocess
from tkinter import E
from flags import flags as gf
import dtwrapper as dt
import json
import xml.dom.minidom
import re
import time
import dtlogger

class st:
    
    
    def sign_config_image(self):
        errlines = []
        hints = []
        cmd = []
        # re-sign DTB elf file
        # open signing command json file

        try:
            with open(gf["signJson"], mode='r', encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            dtlogger.info('Error of reading signing mode command json file.')
            dtlogger.info(e)
            return  False
        # If signing command doesn't contain  --image-id option, fetch it from origninal DTB elf. If the orginal DTB elf is unsigned DTB elf. 
        # If the orginal DTB elf is unsigned DTB elf, it will popout a warning windows and termined signing process.
        if '--image-id' not in data.keys():
            # fetch Software ID from DTB elfs by sectools inspect command
            sign_id_cmd = r'%s secure-image --inspect %s' % (os.path.join(gf['sectoolsDir'],self.sectool_name), gf['inputFile'])
            proc = subprocess.Popen(sign_id_cmd, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True,shell=True)
            dtlogger.info ('Waiting for secure inspect commnad excute done')
            while True:
                out, err= proc.communicate()
                dtlogger.info (out)
                dtlogger.info (err)
                
                for line in out.split('\n'):
                    dtlogger.info(line)
                    if 'Software ID' in line:
                        sign_id_pattern = re.compile(r'0x\d+')
                        sign_id_num = sign_id_pattern.findall(line)[0]
                        break
                    if 'Error:' in line or 'ERROR' in line or 'Errno' in line: 
                        errlines.append(line)
                        dtlogger.info("{} err".format(line))
                        return False
                if proc.poll() != None:
                    dtlogger.info ('secure inspect commnad excute done')
                    break
            if sign_id_num:
                # fetch image ID from profile xml according software ID.
                dom = xml.dom.minidom.parse(r'%s' % gf['profileXml'])
                dom_context = dom.documentElement
                image_all = dom_context.getElementsByTagName('image')
                sw_id_all = dom_context.getElementsByTagName('sw_id')
                for idx, val in enumerate(sw_id_all):
                    if val.firstChild.data == sign_id_num:
                        dtlogger.info(image_all[idx].getAttribute('id'))
                        break

                gf['sign_id'] = image_all[idx].getAttribute('id')
            if gf['sign_id']== '':
                raise Exception('ERROR:Signed DTB elf failed', 'Please provide sign ID for the DTB elf\n')
                   
        # excute sign command seperately
        # Debugged so signing works
        outfile = ""
        dtlogger.info("{}{}".format(gf['outputPath'],gf['outputFile']))
        if not gf['outputPath']:
            outfile = gf['outputFile']
        else:
            outfile = os.path.join(gf['outputPath'], os.path.basename(gf['outputFile']))
      
        cmd = [
                os.path.join( gf['sectoolsDir'], self.sectool_name),
                'secure-image', os.path.join(self.outdir, 'auto_gen', 'elf_files', 'create_cli',
                                    os.path.basename(gf['outputFile'])),
                '--image-id', gf['sign_id'],
                '--security-profile', gf['profileXml'],
                '--sign',
                '--outfile', outfile
                ]
        if self.compressed_elf:
            cmd.append('--compress')

        if data:
            if "SigningCommand" in data:
                for command in data["SigningCommand"]:
                    cmd.append(command)
                    cmd.append(data["SigningCommand"][command])

        dtlogger.info('Excute Signing Command:\n{}'.format(cmd))
  

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
        
       # proc.wait()
        while True:
            line = proc.stdout.readline()
            Err_flag = False
            if not line:
                # execution done
                break
            if 'Error:' in line or 'ERROR' in line or 'Errno' in line: 
                Err_flag = True
                
                
            if Err_flag:
                errlines.append(line)
            else:
                dtlogger.info(line)  

        if errlines != []:
            dtlogger.info(' '.join(errlines))
            return False
        else:
            dtlogger.info("Signing Success!")
            return True
