#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
from flags import flags as gf
from flags import global_info as gl_info
import subprocess
import os
import shutil
import sys
import json
import version_2_assemble
import platform
import dtlogger

#Using magic to detect the compress image
import lzma

test_debug = 1


class assemble:

    def fetch_gendtbelf_script(self):
        tool_path = ''
        dtlogger.info(os.path.dirname(__file__))
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'XBLConfig')):
            gf['xbltoolsDir'] = os.path.join(os.path.dirname(__file__), 'XBLConfig')
        else:
            gf['xbltoolsDir'] = os.path.join(gl_info['sign_json_path'], 'XBLConfig')

        if os.path.exists(os.path.join(gf['xbltoolsDir'], 'GenConfigImage.py')):
            tool_path = os.path.join(gf['xbltoolsDir'], 'GenConfigImage.py')
        else:
            raise Exception('ERROR: Gen DTB tools does not exist', 'Please choose correct GEN DTB tools path!!\n')
        return tool_path

    def load_disassembled_elf_info(self):
        self.disassembled_elf_info = {}
        try:
            with open(os.path.join(self.outdir, 'disassembled_elf_info.json'), mode='r', encoding="utf-8") as fp:
                self.disassembled_elf_info = json.load(fp)
                fp.close()
        except Exception as e:
            #self.logline('Error: Open '+os.path.join(self.outdir, 'disassembled_elf_info.json')+'failed')
            dtlogger.info(e)

    # detect if orginal DTB elf is single segment DTB elf
    def check_single_segment(self):
        #disassembled_elf_info = None
        number_of_segments = 0
        self.load_disassembled_elf_info()
        # Get the number of segments
        for key in self.disassembled_elf_info.keys():
            if key.startswith('segment_'):
                number_of_segments += 1
        dtlogger.info(number_of_segments)
        if number_of_segments == 3:
            return 'True'
        else:
            return ''
    
    # get the alignment setting
    def check_alignment_setting(self):
        try:
            with open(os.path.join(self.outdir,'auto_gen' 'phdr.bin'), mode='r', encoding="utf-8") as fp:
                self.disassembled_elf_info = json.load(fp)
                fp.close()
        except Exception as e:
            dtlogger.info(e)
    
    # detect if the elf is compressed elf
    def is_compressed_elf(self, inputfile):
        try:
            with open(inputfile,'rb') as inputfp:
                header = inputfp.read(6)
                return header == b'\xfd7zXZ\x00'
        except FileNotFoundError:
            dtlogger.info("{} doesn't exist!".format(inputfile))
        except Exception as e:
            dtlogger.info("Open {} encountered error:{}".format(inputfile,e))
        return False

    def decompress_elf_file(self, inputfile, outputfile):
        try:
            with lzma.open(inputfile, 'rb') as compressedfp:
                with open(outputfile, 'wb') as outputfp:
                    outputfp.write(compressedfp.read())
            return True
        except FileNotFoundError:
            dtlogger.info("Error: input file {} not found".format(inputfile))
        except lzma.LZMAError as e:
            dtlogger.info("Decompressed with error:{}".format(e))
        except Exception as e:
            dtlogger.info("Error occurred:{}".format(e))
        return False

    def dissamble_config_elf(self):
        ##check if the image is compressed image.

        if (self.is_compressed_elf(gf['inputFile'])):
            dtlogger.info("{} is compressed file".format(gf['inputFile']))
            self.compressed_elf = True
            decompressed_output_file = os.path.join(self.outdir,os.path.basename(gf['inputFile']))
            if self.decompress_elf_file(gf['inputFile'],decompressed_output_file):
                gf['inputFile'] = decompressed_output_file
            else:
                return False
        else:
            self.compressed_elf = False
        ## dissamble elf file
        return_code = version_2_assemble.disassemble_version_2_elf(gf['inputFile'],
                                                                   self.outdir,
                                                                   self.outdir,
                                                                   os.path.dirname(self.fetch_gendtbelf_script()),
                                                                   True)

        # If version_2_assemble is successful, return 0
        if return_code == 0:
            return True

        if return_code == -2:
            raise Exception("Error: DTB size is greater than length of file.")

        # Clean directory from initial disassemble
        if self.outdir != os.path.dirname(gf['inputFile']):
            for file in os.listdir(self.outdir):
                os.remove(os.path.join(self.outdir, file))

        proc = None
        tool_path = None
        try:
            tool_path = self.fetch_gendtbelf_script()
        except Exception as e:
            raise Exception("{}".format(e))
        if gf['inputFile'] == None or not os.path.exists(gf['inputFile']):
            raise Exception("Error: input path {}.{}".format(gf['inputFile'], " is invalid path!!"))
        try:
            proc = subprocess.Popen(["python",
                                     self.fetch_gendtbelf_script(),
                                     '-t', gf['xbltoolsDir'],
                                     '-a', self.outdir,
                                     '-d', gf['inputFile'],
                                     '-f', 'ELF',
                                     '-o', self.outdir
                                     ], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True
                                    )
        except Exception as e:
            raise Exception("Error:{}".format(e))
        hints = []
        errlines = []
        while True:
            outs, errs = proc.communicate()
            for line in outs.split('\n'):
                dtlogger.info(line)
                if 'Error:' in line or 'ERROR' in line or 'Errno' in line:
                    errlines.append(line)
                    if 'GenXBLConfig.py' in line and 'No such file or directory' in line:
                        hints.append('Are you sure the Config tool is valid?')

                else:
                    if 'XBLconfig_metadata_generator.py: Couldn\'t find XBL config' in line:
                        hints.append('Are you sure the XBLConfig file is valid?')

            if proc.poll != None:
                break
        if gf['testexp']:
            raise Exception('test dissamble exception')
        if errlines != []:
            raise Exception('\n'.join(errlines))
                    
        #check if there is dtbs.bin in disassemble output folder.
        #If there is dtbs.bin, disassemble it
        dtbs_bin_list=[file for file in os.listdir(self.outdir) if file.endswith('dtbs.bin')]
        for dtbs_bin in dtbs_bin_list:
            #create dtbs bin folder for store dtb and dtbo binariese
            dtbs_file = os.path.join(self.outdir,dtbs_bin)
            dtbs_folder_name = dtbs_file.rsplit('.bin',1)[0]
            os.mkdir(dtbs_folder_name)
            
            meta_entry_json = version_2_assemble.walk_dtbs(dtbs_file, False)

            if "-1" in meta_entry_json or "-2" in meta_entry_json:
                if "-1" in meta_entry_json:
                    dtlogger.info("ELF file doesn't consist entirely of DTBs. Moving onto legacy disassemble...")
                    return -1
                if "-2" in meta_entry_json:
                    dtlogger.info("Misshapen size in a DTB. Returning early.")
                    return -2
                # # Get rid of all files disassembled from this as long as they're not in the same directory as config
                # if dtbs_folder_name != os.path.dirname(config_file_to_be_disassembled):
                #     for file in os.listdir(output_xbl_config_directory):
                #         os.remove(os.path.join(output_xbl_config_directory, file))

                # if autogen_directory != os.path.dirname(config_file_to_be_disassembled):
                #     for file in os.listdir(autogen_directory):
                #         os.remove(os.path.join(autogen_directory, file))

            # Turn each DTB within the DTBs into its own separate DTB file
            version_2_assemble.disassembled_dtbs_to_separate_files(dtbs_file, meta_entry_json, dtbs_folder_name)
            os.remove(dtbs_file)

    def reassemble_config_elf(self):
        sectool_name = ''
        if platform.system().startswith("Windows"):
            sectool_name = "sectools.exe"
        else:
            sectool_name = "sectools"
        # Check to see whether the legacy version of reassembly should be invoked
        if not "create_xbl_config.json" in os.listdir(self.outdir):
            if os.path.exists(os.path.join(gf['sectoolsDir'], sectool_name)):
                sectool_path = os.path.join(gf['sectoolsDir'], sectool_name)

            dtlogger.info(self.outdir)
            # Make directories if needed
            if not os.path.exists(os.path.join(self.outdir, 'auto_gen')):
                os.mkdir(os.path.join(self.outdir, 'auto_gen'))

            if not os.path.exists(os.path.join(self.outdir, 'auto_gen', 'elf_files')):
                os.mkdir(os.path.join(self.outdir, 'auto_gen', 'elf_files'))

            if not os.path.exists(os.path.join(self.outdir, 'auto_gen', 'elf_files', 'create_cli')):
                os.mkdir(os.path.join(self.outdir, 'auto_gen', 'elf_files', 'create_cli'))

            desired_name = version_2_assemble.reassemble_version_2_elf(self.outdir,
                                                                       os.path.join(self.outdir, 'auto_gen',
                                                                                    'elf_files', 'create_cli'),
                                                                       sectool_path,
                                                                       gf['outputFile'][:-4] if gf[
                                                                           'outputFile'].endswith('.elf') else gf[
                                                                           'outputFile'],
                                                                       True)
            if desired_name is None:
                raise Exception("Reassemble dtb elf file failed!")
            # Make a copy and use that as a secure-image for signing
            shutil.copy(os.path.join(self.outdir, 'auto_gen', 'elf_files', 'create_cli',
                                     os.path.basename(gf['outputFile'])),
                        gf['outputFile'])
            return True
        # Reassembles a directory of individual DTBs into a single DTBS file    
        dtb_dtbs_folder = [folder for folder in os.listdir(self.outdir) if folder.endswith('.dtbs')]
        for dtbs_folder in dtb_dtbs_folder:
            dtbs_file = os.path.join(self.outdir,dtbs_folder+".bin")
            if os.path.exists(dtbs_file):
                os.remove(dtbs_file)
                dtbs_file = ''
            dtbs_file = version_2_assemble.reassemble_output_dtb_dtbs(os.path.join(self.outdir,dtbs_folder),self.outdir)
            if dtbs_file != '':
                os.rename(dtbs_file,os.path.join(self.outdir,dtbs_folder+".bin"))

        ELF_FORMATS = [None, "ELF32", "ELF"]
        self.load_disassembled_elf_info()
        # reassemable the dtb elfs
        tool_path = self.fetch_gendtbelf_script()
        cmd = ["python",
               self.fetch_gendtbelf_script(),
               "-t", gf['xbltoolsDir'],
               '-a', self.outdir,
               '-i', os.path.join(self.outdir, 'create_xbl_config.json'),
               '-b', self.outdir,
               '-f', ELF_FORMATS[int(self.disassembled_elf_info['E_CLASS'], 16)],
               '-o', gf['outputFile'][:-4] if gf['outputFile'].endswith('.elf') else gf['outputFile'],
               '-x', self.disassembled_elf_info['alignment']
               ]
        if self.check_single_segment() == 'True':
            cmd.append('--single_segment')
        dtlogger.info("excute {}".format(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
        errlines = []
        hints = []
        unsigned_supp = True
        while True:
            line = proc.stdout.readline()
            if not line:
                # execution done
                #dtlogger.info("exit command")
                break

            if 'Error:' in line or 'ERROR' in line or 'Errno' in line:
                if 'Signed' in line and gf['allowUnsigned']:
                    # ignore signing errors and treat them as warnings
                    dtlogger.info("{} warn".format(line))
                    unsigned_supp = True
                else:
                    errlines.append(line)
                    dtlogger.info("{} err".format(line))
                if 'sectools.py' in line and 'No such file or directory' in line:
                    hints.append('Are you sure the sectools directory is valid?')
            elif 'WARNING' in line or 'SKIPPING' in line:
                dtlogger.warning(line)
            elif 'Disassembled' in line or 'Generated' in line:
                dtlogger.info("{} success".format(line))
            elif '***' in line or 'SUMMARY' in line:
                dtlogger.info("{} info".format(line))
            else:
                dtlogger.info(line)
        if errlines != []:
            raise Exception(' '.join(errlines))
        else:
            return True
