#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
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
import sign
import assemble
import tempfile
import shutil

class autocmd(sign.st,assemble.assemble):
    def __init__(self,dtw):
        self.dtw = dtw
        self.sectool_name = 'sectools'
        self.outdir = ''
        self.check_python()
    
    def check_python(self):
        try:
            proc = subprocess.Popen(["python",                                 
                                 '--version'
                                 ],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True,
                                 shell=True)
        except Exception as Error:
            print("error:",Error)
            sys.exit(-1)
        while True:
            outs, errs = proc.communicate()
            output=None

            if len(outs) == 0 and len(errs) != 0:
                output = errs
            else:
                output = outs
            for line in output.split('\n'):
                if 'Python was not found' in line or r"'python' is not recognized" in line:
                    print("Python is not installed!\nPlease install python v3.7.4 or later!\n")
                    sys.exit(-1)
            return_value = proc.poll()
            if return_value!=None and return_value!=9009:
                print("sub process has been terminate:",proc.poll())
                break
            elif return_value == 9009:
                print("Python is not installed!\nPlease install python v3.7.4 or later!\n")
                sys.exit(-1)

            
        
        print("python version ",sys.version_info)
        if sys.version_info < (3, 7, 4):
            sys.exit("Python Error","Please install python v3.7.4 or later!\n")

        return True
    def execute(self):
        
        try:
            if self.outdir:
                # clean up old temporary directory
                shutil.rmtree(self.outdir)

            self.outdir = tempfile.mkdtemp(prefix='dtgui_')

        except IOError as ex:
            self.logline('Error when creating a temporary work directory: %s' % getattr(ex, 'message', repr(ex)))

        modify_properties = []
        property_value = None
        property_path = None
        if not gf['allowUnsigned']:
            # Check if all the signing requested parameters are provided correctly.
            if "sectoolsDir" not in gf.keys() or gf['sectoolsDir'] == None:
                sys.exit("Error:Please provide --sectools_dir option!\n")
            elif not os.path.exists(gf['sectoolsDir']):
                sys.exit("{}{}{}".format("Error:sectoos tool path:",gf['sectoolsDir']," doesn't exist!!!\n Please provide correct sectool path!!"))

            if 'signJson' not in gf.keys() or  gf['signJson'] == None:
                sys.exit("Error:signing json file not provided!!\n please provide --signjson option!\n")
            elif not os.path.exists(gf['signJson']):
                sys.exit("{}{}{}".format("Error:signing command file path:",gf['signJson'],"doesn't exist!!!\n Please provide correct signing commmand file path of --sign_json option!"))
        
            if "profileXml" not in gf.keys() or gf['profileXml'] == None:
                sys.exit("Error:Please provide  --profileXml option!")
            elif not os.path.exists(gf['profileXml']):
                sys.exit("{}{}{}".format("Error:profileXml  path:",gf['profileXml'],"doesn't exist!!!\n Please provide correct profileXml path!!"))
        ## dissamble elf file
        try:
            self.dissamble_config_elf()
        except Exception as e:
            sys.exit(e)

        #modify property value
        if gf['modify']:
            modify_properties=gf['modify'].split('&')
            current_dtb_name = None
            dtb_name = None
            property_path = None
            property_value = None
            dtb_path = None
            for modify_property in modify_properties:
                try:
                    if modify_property.split('/')[0].endswith('.dtbs'):
                        dtb_name = modify_property.split('/')[1]
                        property_value = modify_property.split('=')[1].split(';')
                        property_path = modify_property.split('=')[0]                 
                        index = property_path.find('.dtb/')+len('.dtb')
                        dtb_path = os.path.join(self.outdir,property_path[:index])  
                        property_path = property_path[index:]
                      
                    else:
                        dtb_name = modify_property.split('/')[0]
                        property_value = modify_property.split('=')[1].split(';')
                        property_path = modify_property.split('=')[0]
                        property_path = property_path[len(modify_property.split('/')[0]):]
                        dtb_path = os.path.join(self.outdir,dtb_name)

                    print("proterty_path:",property_path )
                    print("property_value:",property_value )
                    print("dtb_name:",dtb_name)
                except Exception as e:
                    print("Error: option --modify {} is not correct".format(modify_property))
                    sys.exit(-1)
                if not os.path.exists(dtb_path):
                    if  os.path.exists(os.path.join(self.outdir, "_{}".format(dtb_name))):
                        dtb_name = "_{}".format(dtb_name)
                    else:
                        print("Error: dtb {} does not exist in config image".format(dtb_name))
                        sys.exit(-1)
                # load dtb
                if True or current_dtb_name != dtb_name:
                  try:
                    self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.LOAD, dtb_path))
                  except Exception as e:
                    print(e, "in config image")
                    sys.exit(-1)
                  current_dtb_name = dtb_name

                # update property value
                try:
                    self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.EDIT_PROPERTY_VALUE, property_path.strip(), property_value))
                except Exception as e:
                    print (e) 
                    sys.exit(-1)

                # save DTB
                self.dtw.apply(dt.DTOperation.make(dt.DTOperationType.SAVE_DTB, dtb_path))

            #save change report 
            cr_filename = '%s_%d.json' % (os.path.basename(gf['inputFile']).rsplit('.', 1)[0], time.time())
            report = ''
            cr_report = os.path.join(gf['outputPath'],cr_filename)
            try:
                # try to generate report
                report = self.dtw.report()
            except Exception as ex:
                print('ERROR:Failed to save change report', 'Encountered error while attempting to save change '
                                                                        'report:\n' + getattr(ex, 'message', str(ex)))
                return

            # write out the file
            with open(cr_report, 'wb') as outfile:
                outfile.write(report.encode())
                outfile.close()
            
        # reassemable the dtb elfs
        try:
            print("\nentering reassembly...")
            self.reassemble_config_elf()
        except Exception as result:
            sys.exit(result)
            
        if not gf['allowUnsigned']:
            try:
                self.sign_config_image()
            except Exception as result:
                sys.exit(result)

            outfile = ""
            if not gf['outputPath']:
                outfile = gf['outputFile']
            else:
                outfile = os.path.join(gf['outputPath'],gf['outputFile'])
            print(outfile," was created and signed successfully")
        else:
            try:
                shutil.copy(os.path.join(self.outdir, 'auto_gen', 'elf_files', 'create_cli',
                                         gf['outputFile']), os.path.join(gf['outputPath'],gf['outputFile']))
            except Exception as e:
                sys.exit(e)
            print(os.path.join(gf['outputPath'],gf['outputFile'])," was created successfully")
                 