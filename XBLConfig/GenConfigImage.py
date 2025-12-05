#!/usr/bin/env python

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause


from __future__  import print_function
from optparse import OptionParser
import platform
import subprocess
import shutil
import os
import sys
import locale
import re
import time
import datetime
import json
from collections import OrderedDict
import commons
from commons import *

if sys.version_info < MINIMUM_SUPPORTED_PYTHON_VERSION:
  print("Must use Python " + str(MINIMUM_SUPPORTED_PYTHON_VERSION) + " or greater")
  sys.exit(1)


#####################################################################
# get corresponding python path
# input python version like 2, 3
#####################################################################
def get_python_path(version):
  python_path=b''
  if platform.system() == "Windows":
    python_paths = subprocess.check_output('where python', stderr=subprocess.STDOUT , shell=True)
    python_list=python_paths.split(b'\r\n')
    
    python_version_match=b'Python '+str(version).encode()
    for python_exe in python_list:
      python_version = b''
      if python_exe !=b'':
        try:
          python_version = subprocess.check_output(python_exe.decode()+' --version',stderr=subprocess.STDOUT , shell=True)
        except Exception as error:
          #print (error)
          continue
        if re.match(python_version_match,python_version):
           python_path=python_exe
  
    if python_path==b'':
      print('[Buildex.py] Error Can not find python',str(version))
      sys.exit(1)
  else:
     python_path = b'python'+str(version).encode()

  return python_path.decode()+' '

def disassemble_xbl_config_file(config_file_to_be_disassembled, 
                                format, 
                                output_xbl_config_directory, 
                                autogen_directory,
                                tools_path):
  # Create output based on format
  if (format == "ELF32" or format == "ELF"):
    disassemble_elf(config_file_to_be_disassembled,
                    format,
                    output_xbl_config_directory,
                    autogen_directory,
                    tools_path)
  else:
    print("\nBinary output is currently not supported.")

def generate_xbl_config_file(json_config_path,
                             format, 
                             elf_address, 
                             output_xbl_config_filename,
                             base_directory, 
                             output_xbl_config_directory,
                             sectools_directory, 
                             autogen_directory,
                             tools_path,
                             soc_hw_version,
                             soc_vers,
                             sectools_version,
                             sign_id,
                             security_profile,
                             signing_mode,
                             single_segment,
                             signing_params,
                             alignment,
                             relocatable,
                             integrity_image_generation,
                             integrity_image_no_metadata,
                             store_original_size=False):
  storeoriginalsize=''                      
  # Read JSON config data
  try:
    with open(json_config_path) as json_file:    
      json_data = json.load(json_file, object_pairs_hook=OrderedDict)
  except:
    print("\nERROR: An error occurred while reading JSON config file.  " + \
          "Please check contents.")
    exit(-1)

  if store_original_size:
      storeoriginalsize = ' --store-original-size'
  # Call XBL config metadata generator to construct the config headers
  call_os_system("python \"" + tools_path + "/" + XBL_CONFIG_METADATA_SCRIPT + "\""+\
                 " -i " + json_config_path + \
                 " -b " + base_directory + \
                 " -o " +  autogen_directory + \
                 " -a " + alignment +\
                 storeoriginalsize)
  # Verify that all binary blobs were generated using JSON config entries
  major_version = json_data["CFGL"].pop("major_version", 1)
  minor_version = json_data["CFGL"].pop("minor_version", 0)
  for current_CFG in json_data:
    if not os.path.isfile(autogen_directory + "/" + current_CFG + ".bin"):
      print("\nERROR: XBLconfig_metadata_generator.py did not generate " + \
            "expected binary files: " + autogen_directory + "/" + current_CFG + ".bin")
      exit(-1)
    # if elf_address is 0 and if ELF_ADDRESS is captured in 
    # first cfg_meta item's first item then use that as elf_address
    if (elf_address=="0x0") and (FIRST_CFG_FILE_KEY in json_data[current_CFG]) \
                         and (ELF_ADDRESS in json_data[current_CFG][FIRST_CFG_FILE_KEY]):
      elf_address = json_data[current_CFG][FIRST_CFG_FILE_KEY][ELF_ADDRESS]

  # Create output based on format
  if (format == "ELF32" or format == "ELF"):
    try:
      create_elf(base_directory,
                 json_data,
                 autogen_directory,
                 int(elf_address, base=16),
				 format,
                 output_xbl_config_filename,
                 tools_path,
                 output_xbl_config_directory,
                 single_segment,
                 relocatable,
                 alignment)
    except:
      print("\nERROR: Exception occurred for create_elf function call.")
      exit(-1)

    #sign generated xbl_config if sectools directory is provided
    if sectools_directory:
      if sectools_version == 'v1': 
          sign_elf_v1(sectools_directory,
                  autogen_directory,
                  output_xbl_config_filename,
                  output_xbl_config_directory,
                  soc_hw_version,
                  soc_vers)
      elif sectools_version == 'v2':
          sign_elf_v2(sectools_directory,
                  autogen_directory,
                  output_xbl_config_filename,
                  output_xbl_config_directory,
                  sign_id,
                  security_profile,
                  signing_mode,
                  signing_params,
                  integrity_image_generation,
                  integrity_image_no_metadata)
    else:
          print("Signing skipped as sectools directory is not provided!")
          #Copy raw xbl_config to output dir under "raw folder"
          output_raw_path = output_xbl_config_directory + RAW_FOLDER
          create_directory(output_raw_path)

          file_to_be_copied = autogen_directory + \
                              ELF_GEN_SCRIPT_OUTPUT_RELATIVE_PATH + \
                              output_xbl_config_filename

          shutil.copy(file_to_be_copied, output_raw_path)
          print("\nRaw", output_xbl_config_filename, "copied to", output_raw_path, "\n")
      
  else:
    print("\nBinary output is currently not supported.")

###############################################################################
# sign_elf
###############################################################################
def sign_elf_v1(sectools_directory,
             autogen_directory,
             output_xbl_config_filename,
             output_xbl_config_directory,
             soc_hw_version,
             soc_vers):
  try:
    if sectools_directory and os.path.isdir(sectools_directory):
      filepath_to_be_signed = autogen_directory + \
                              ELF_GEN_SCRIPT_OUTPUT_RELATIVE_PATH + \
                              output_xbl_config_filename

      output_unsigned_path = output_xbl_config_directory + UNSIGNED_FOLDER
      create_directory(output_unsigned_path)

      print("************* Sign generated Elf ************\n")

      subprocess.check_call(('python '+ sectools_directory + "/" + SECTOOLS_SCRIPT + SECTOOLS_COMMAND
                             + " -i " + filepath_to_be_signed
                             + " -o " + autogen_directory + UNSIGNED_FOLDER
                             + " -ta "
                             + " -g " + SIGN_ID 
                             + " -c " + sectools_directory + SECTOOLS_CONFIG_XML ), shell=True )

      shutil.copy((autogen_directory + UNSIGNED_FOLDER + DEFAULT_SIGN_DIR_ROOT + SIGN_ID 
                   + "/" + output_xbl_config_filename)
                  ,output_unsigned_path)
      
      subprocess.check_call(('python '+ sectools_directory + "/" + SECTOOLS_SCRIPT + SECTOOLS_COMMAND
                             + " -i " + filepath_to_be_signed
                             + " -o " + autogen_directory + SIGNED_FOLDER
                             + " -sa "
                             + " -g " + SIGN_ID 
                             +" -c " + sectools_directory + SECTOOLS_CONFIG_XML
                             +" --cfg_segment_hash_algorithm " + "sha384"
                             +" --cfg_soc_hw_version " + soc_hw_version
                             +" --cfg_in_use_soc_hw_version " + SECTOOLS_IN_USE_SOC_HW_VERSION
                             +" --cfg_soc_vers " + "\"" + soc_vers + "\""),  shell=True )

      shutil.copy((autogen_directory + SIGNED_FOLDER + DEFAULT_SIGN_DIR_ROOT + SIGN_ID 
                   + "/" + output_xbl_config_filename)
                  ,output_xbl_config_directory)
      
      print("\n Signed image: " + (output_xbl_config_directory + "/" + output_xbl_config_filename + "\n"))
                      
      print("*************  Signing Successful   ************")
    else:
      print("\n\n    !!!!! No Sectools Folder provided. SKIPPING IMAGE SIGNING !!!!!")
      print("\n    ERROR: Could not generate Signed XBL Config  \n\n")
  except Exception as error:
    print(error)
    print("\nERROR: An error occurred while Signing the ELF file.")
    exit(-1)
    
def sign_elf_v2(sectools_directory,
             autogen_directory,
             output_xbl_config_filename,
             output_xbl_config_directory,
             sign_id,
             security_profile,
             signing_mode,
             signing_params,
             integrity_image_generation,
             integrity_image_no_metadata):
  try:
    if sectools_directory and os.path.isdir(sectools_directory):
      filepath_to_be_signed = autogen_directory + \
                              ELF_GEN_SCRIPT_OUTPUT_RELATIVE_PATH + \
                              output_xbl_config_filename

      if integrity_image_generation:
        print("*************  Generating Unsigned/Integrity Elf  ************\n")      
        if os.path.isfile(filepath_to_be_signed):
          out_file = os.path.join(autogen_directory, "unsigned", output_xbl_config_filename)
          CMD = (os.path.join(sectools_directory, V2_SECTOOLS_SCRIPT)
            + " secure-image " + filepath_to_be_signed 
            + " --outfile " + out_file 
            + " --image-id " + sign_id
            + " --security-profile " + security_profile 
            + " --hash")

          if integrity_image_no_metadata:
            CMD += str(" --platform-binding INDEPENDENT")

          print(CMD)
          os.system(CMD)
          os.makedirs(os.path.join(output_xbl_config_directory, "unsigned"), exist_ok=True)
          shutil.copy(out_file, os.path.join(output_xbl_config_directory, "unsigned"))
          print("\n Unsigned/Integrity image: " + os.path.join(output_xbl_config_directory, "unsigned", output_xbl_config_filename) + "\n")    
        print("*************  Unsigned/Integrity Generation Successful  ************")

      print("************* Sign generated Elf ************\n")      
      if os.path.isfile(filepath_to_be_signed):
        if integrity_image_generation:
          out_file = os.path.join(autogen_directory, "sign", output_xbl_config_filename)
        else:
          out_file = os.path.join(autogen_directory, output_xbl_config_filename)
        CMD = (os.path.join(sectools_directory, V2_SECTOOLS_SCRIPT)
          + " secure-image " + filepath_to_be_signed 
          + " --outfile " + out_file 
          + " --image-id " + sign_id
          + " --security-profile " + security_profile 
          + " --sign " 
          + " --signing-mode " + signing_mode
          + " " + signing_params)
        print(CMD)
        os.system(CMD)
        if integrity_image_generation:
          os.makedirs(os.path.join(output_xbl_config_directory, "sign"), exist_ok=True)
          shutil.copy(out_file, os.path.join(output_xbl_config_directory, "sign"))
          print("\n Signed image: " + os.path.join(output_xbl_config_directory, "sign", output_xbl_config_filename) + "\n")    
        else:
          shutil.copy(out_file  ,output_xbl_config_directory)
          print("\n Signed image: " + os.path.join(output_xbl_config_directory, output_xbl_config_filename) + "\n")    
        print("*************  Signing Successful   ************")

    else:
      print("\n\n    !!!!! No Sectools Folder provided. SKIPPING IMAGE SIGNING !!!!!")
      print("\n    ERROR: Could not generate Signed XBL Config  \n\n")
  except Exception as error:
    print(error)
    print("\nERROR: An error occurred while Signing the ELF file.")
    exit(-1)         

###############################################################################
# disassemble_elf
###############################################################################
def disassemble_elf(config_file_to_be_disassembled,
                    format,
                    output_xbl_config_directory,
                    autogen_directory,
                    tools_path):
  disassembled_elf_info_json = os.path.join(output_xbl_config_directory, DISASSEMBLED_ELF_INFO_JSON)
  # Execute the ELF Generator script to disassemable XBL-config elf
  call_os_system("python \"" + tools_path + "/" +  ELF_GENERATOR_SCRIPT + "\"" +\
                 " -d " + "\""+config_file_to_be_disassembled+"\"" + \
                 " -o " + autogen_directory + \
                 " -e " + disassembled_elf_info_json)

  out_create_xcfg_json = os.path.join(output_xbl_config_directory, OUT_CREATE_XCFG_JSON)
  # Call XBL config metadata generator to locate and parse xbl-config-metadata from
  #    disassembled elf segments, generate out_create_xcfg_json with 
  #    xbl-config-items' file-name, config_name etc details
  call_os_system("python \"" + tools_path + "/" + XBL_CONFIG_METADATA_SCRIPT + "\"" +\
                 " -d " + disassembled_elf_info_json + \
                 " -o " + output_xbl_config_directory + \
                 " -c " + out_create_xcfg_json)

  # prepare genxblcfg_command to display which can be used by user to re-generate
  #   xbl_config.elf using disassembled info "out_create_xcfg_json" as input
  elf_address = "0x[elf_entry_point]" #default
  if not os.path.isfile(disassembled_elf_info_json):
    print_error_exit("\nError: Disassembled elf info " + str(disassembled_elf_info_json) + " file must be valid and exist.")
  with open(disassembled_elf_info_json) as disassembled_elf_info_json_file:    
    disassembled_bins_info = json.load(disassembled_elf_info_json_file, object_pairs_hook=OrderedDict)
    if E_ENTRY in disassembled_bins_info:
      elf_address = str(disassembled_bins_info[E_ENTRY])
    disassembled_elf_info_json_file.close()
  genxblcfg_command = "python \"" + tools_path + "/" + GEN_XBL_CONFIG_SCRIPT + "\"" \
                 " -i " + out_create_xcfg_json + \
                 " -b " + output_xbl_config_directory + \
                 " -f ELF " + \
                 " -o " + str(os.path.join(output_xbl_config_directory,"xbl_config")) + \
                 " --sectools_directory " + str(os.path.join(tools_path,"sectools")) + \
                 " --sectools_version v2" + \
                 " --signing_mode TEST" + \
                 " --sign_id XBL-CONFIG" + \
                 " --security_profile " + str(os.path.join(tools_path,"tme_security_profile.xml"))
  
  print("\nDisassembled XBL config items and .json can be found in directory:\"" + \
         output_xbl_config_directory + "\"." + \
        "\n\nTo create xbl_config.elf from disassembled items, please execute below command:\n" + \
        "\"" + str(genxblcfg_command) + "\"")

###############################################################################
# align_to_size(data,alignment)
###############################################################################
def align_to_size(original_size,align_bytes):
  return (int(original_size,16)+int(align_bytes,16)-1)//int(align_bytes,16)*int(align_bytes,16) 
###############################################################################
# merge_segments
###############################################################################
def merge_segments(base_directory,
                       json_data,
                       output_directory):
  segments_combination_size = 0;
  if not os.path.exists(output_directory):
    print("\ncreate directory",output_directory)
    create_directory(output_directory)
  segments_combination_bin = os.path.join(output_directory,SEGMENTS_COMBINATION_FILE_NAME)
  if os.path.exists(segments_combination_bin):
    os.remove(segments_combination_bin)
  
  segments_combination_bin_fp = open(segments_combination_bin, mode='ab')
  for CFG_section in json_data:
    CFG_section_file = os.path.join(output_directory,correct_path(CFG_section + ".bin"))
    if not os.path.exists(CFG_section_file):
      print_error_exit("\nError:",CFG_section_file," doesn't exist\n")
    CFG_section_file_fp = open(CFG_section_file, mode='rb')
    print("write ",CFG_section_file," to ",segments_combination_bin)
    segments_combination_bin_fp.write(CFG_section_file_fp.read())
    segments_combination_size += os.path.getsize(CFG_section_file)
    CFG_section_file_fp.close()
    for current_section in json_data[CFG_section]:
      #if the file path in json is absolute, use it directly
      if os.path.isfile(str(json_data[CFG_section][current_section][JSON_CONFIG_FILE_KEY_NAME])):
        current_section_file = str(json_data[CFG_section][current_section][JSON_CONFIG_FILE_KEY_NAME])
      #if the file path in json is relative, join it with base directory
      else:
        current_section_file = (os.path.join(base_directory, correct_path(json_data[CFG_section][current_section][JSON_CONFIG_FILE_KEY_NAME])))
      print(current_section_file)
      if not os.path.exists(current_section_file):
        print_error_exit("\nError:",current_section_file," doesn't exist\n")
      section_file_fp = open(current_section_file, mode='rb')
      print("write ",current_section_file," to ",segments_combination_bin)
      segments_combination_bin_fp.write(section_file_fp.read())
      section_file_fp.close()
      segments_combination_size +=os.path.getsize(current_section_file)
      
  segments_combination_bin_fp.close()
  print(segments_combination_bin," write done. size is ",segments_combination_size)
  return segments_combination_size

###############################################################################
# create_elf
###############################################################################
def create_elf(base_directory,
               json_data,
               output_directory,
               elf_address,
               format,
               output_filename,
               tools_path,
               output_xbl_config_directory,
               single_segment,
               relocatable,
               alignment='0x1'):

  segment_count = 0
  current_offset = 0
  physically_relocatable_flag = 0x0

  if relocatable:
    physically_relocatable_flag = 0x1

  current_address = elf_address

  if single_segment == False:
    # Calculate how many segments will be created
    # Main section does not need a metadata segment so start with -1
    for CFG_section in json_data:
      # Add one for metadata segment
      segment_count += 1
  
      # Add ubjson segments
      segment_count += len(json_data[CFG_section])
  else:
    segment_count = 1
  
    print("segment count",segment_count)
  # Construct initial JSON for elf generator
  elf_json = {}
  
  elf_json.update({"config_output_path" : output_directory})
  elf_json.update({"config_output_file" : output_filename})
  
  elf_json.update({"elf_header" : {"e_ident" : {"ei_class" : "0x2",
                                                "ei_version" : "0x0"},
                                   "ph_num" : str(hex(segment_count).rstrip("L")),
                                   "type" : "0x2",
                                   "machine" : "0x1",
                                   "entry_addr" : str(hex(elf_address).rstrip("L")),
                                   "ph_offset" : "0x40",
                                   "sh_offset" : "0x0",
                                   "flags" : "0x5",
                                   "sh_size" : "0x0",
                                   "sh_num" : "0x0"},
                   "program_header" : {"segment_alignment_offset" : alignment,
                                       "segment" : list()}})

  if (format == "ELF32"):
    elf_json["elf_header"]["e_ident"]["ei_class"] = "0x1"

  # combine all the cfg sections into one binary
  combined_bin_size = merge_segments(base_directory,json_data,output_directory)

  if not single_segment:
    # Add segments to program header dictionary
    for CFG_section in json_data:
      # Add metadata segment
      elf_json["program_header"]\
            ["segment"].append({"type" : "0x0",
                                "offset" : str(hex(current_offset).rstrip("L")),
                                "vaddr" : str(hex(current_address).rstrip("L")),
                                "paddr" : str(hex(current_address).rstrip("L")),
                                "file_size" : str(hex(os.path.getsize(os.path.join(output_directory,
                                                                                   correct_path(CFG_section + ".bin")))).rstrip("L")),
                                "mem_size" : str(hex(os.path.getsize(os.path.join(output_directory,
                                                                                  correct_path(CFG_section + ".bin")))).rstrip("L")),
                                "flags" : "0x7",
                                "access_type" : "0x0",
                                "segment_type" : "0x1",
                                "addr_alignment" : alignment,
                                "binary" : str(os.path.join(output_directory, correct_path(CFG_section + ".bin"))),
                                "binary_class" : "0x2",
                                "relocatable" : str(hex(physically_relocatable_flag).rstrip("L"))})
      if (format == "ELF32"):
        elf_json["program_header"]["segment"][0]["binary_class"] = "0x1"
      
      # Update the current_offset and address
      current_offset += (align_to_size(hex(os.path.getsize(os.path.join(output_directory, correct_path(CFG_section + ".bin")))),alignment))
      current_address += os.path.getsize(os.path.join(output_directory, correct_path(CFG_section + ".bin")))
      
      # Add all files/segments
      segment_count = 1
      for current_file in json_data[CFG_section]:
        #if the file path in json is absolute, use it directly
        if os.path.isfile(str(json_data[CFG_section][current_file][JSON_CONFIG_FILE_KEY_NAME])):
          current_file_path = str(json_data[CFG_section][current_file][JSON_CONFIG_FILE_KEY_NAME])
        #if the file path in json is relative, join it with base directory
        else:
          current_file_path = (os.path.join(base_directory, correct_path(json_data[CFG_section][current_file][JSON_CONFIG_FILE_KEY_NAME])))
        elf_json["program_header"]\
                ["segment"].append({"type" : "0x0",
                                    "offset" : str(hex(current_offset).rstrip("L")),
                                    "vaddr" : str(hex(current_address).rstrip("L")),
                                    "paddr" : str(hex(current_address).rstrip("L")),
                                    "file_size" : str(hex(os.path.getsize(current_file_path)).rstrip("L")),
                                    "mem_size" : str(hex(os.path.getsize(current_file_path)).rstrip("L")),
                                    "flags" : "0x7",
                                    "access_type" : "0x0",
                                    "segment_type" : "0x1",
                                    "addr_alignment" : alignment,
                                    "binary" : current_file_path,
                                    "binary_class" : "0x2",
                                    "relocatable" : str(hex(physically_relocatable_flag).rstrip("L"))})
        if (format == "ELF32"):
          elf_json["program_header"]["segment"][segment_count]["binary_class"] = "0x1"
        segment_count += 1
        
        # Update the current_offset
        current_offset += (align_to_size(hex(os.path.getsize(current_file_path)),alignment))
        
        current_address += \
          os.path.getsize(current_file_path)
  else:
    # Add metadata segment
    elf_json["program_header"]\
          ["segment"].append({"type" : "0x0",
                              "offset" : str(hex(current_offset).rstrip("L")),
                              "vaddr" : str(hex(current_address).rstrip("L")),
                              "paddr" : str(hex(current_address).rstrip("L")),
                              "file_size" : str(hex(os.path.getsize(os.path.join(output_directory,SEGMENTS_COMBINATION_FILE_NAME))).rstrip("L")),
                              "mem_size" : str(hex(os.path.getsize(os.path.join(output_directory,SEGMENTS_COMBINATION_FILE_NAME))).rstrip("L")),
                              "flags" : "0x7",
                              "access_type" : "0x0",
                              "segment_type" : "0x1",
                              "addr_alignment" : alignment,
                              "binary" : str(os.path.join(output_directory,SEGMENTS_COMBINATION_FILE_NAME)),
                              "binary_class" : "0x2",
                              "relocatable" : str(hex(physically_relocatable_flag).rstrip("L"))})
    if (format == "ELF32"):
      elf_json["program_header"]["segment"][0]["binary_class"] = "0x1"
    

  ELF_Generator_JSON_File = output_directory + "/" + ELF_GENERATOR_JSON_FILE_NAME
  
  # Write ELF JSON file out
  with open(ELF_Generator_JSON_File, "w") as elf_json_file:
    json.dump(elf_json, elf_json_file, separators=(',', ':'), indent=4)


  # Execute the ELF Generator script
  subprocess.check_call(("python \"" + tools_path + "/" +  ELF_GENERATOR_SCRIPT + "\""\
                         " --cfg " + ELF_Generator_JSON_File + \
                         " -a " + alignment),shell=True)
  return

##############################################################################
# main
##############################################################################
if __name__ == "__main__":
  error_count = 0  
  parser = OptionParser()

  parser.add_option("-a", "--autogen_directory",
                      action="store", type="string", dest="autogen_directory",
                      help="Temporary folder, scratch space for auto generated files.")

  parser.add_option("-b", "--config_item_base_directory",
                      action="store", type="string", dest="base_directory",
                      help="Base directory for relative paths of config items in input .json.")

  parser.add_option("-s", "--sectools_directory",
                      action="store", type="string", dest="sectools_directory",
                      help="Needs to point to sectools folder used for signing." + \
                      "signing will be skipped if this option is not provided")        
          
  parser.add_option("-t", "--tools_path",
                      action="store", type="string", dest="tools_path",
                      help="Path to tools directory containing dependent *.py scripts.")
          
  parser.add_option("-f", "--format",
                      action="store", type="string", dest="format",
                      help="Output Format: ELF, ELF32, or BIN")

  parser.add_option("-e", "--elf-address",
                      action="store", dest="elf_address", default="0x0",
                      help="If format is ELF or ELF32 then this is the beginning " + \
                           "address.  Default is 0x00000000.")

  parser.add_option("-i", "--input-json",
                      action="store", type="string", dest="json_config_path",
                      help="Input JSON config file.")

  parser.add_option("-o", "--output-file-without-extension OR output-directory with -d option used",
                      action="store", dest="output_file", default="XBL_Config",
                      help="Output file name without extention.  " + \
                      "Default is XBL_Config")

  parser.add_option("-d", "--input-config-file-to-disassemble",
                      action="store", dest="config_file_to_be_disassembled",
                      help="Command to disassemble with input config file.")

  parser.add_option("-j", "--soc-hw-version",
                      action="store", dest="soc_hw_version", default="0x60000000",
                      help="soc hw version for xblconfig image signing. " + \
                           "Default is 0x60000000.")
                           
  parser.add_option("-k", "--soc-vers",
                      action="store", dest="soc_vers", default="0x6000 0x6001",
                      help="soc vers for xblconfig image signing " + \
                           "Default is 0x6000 0x6001.")                         

  parser.add_option("-c", "--clean",
                      action="store_true", dest="clean", default=False,
                      help="cleans previously generated binaries. ")
                      
  parser.add_option("-p", "--security_profile",
                      action="store", type="string", dest="security_profile",
                      help="Path to security profile xml")

  parser.add_option("-z", "--sign_id",
                      action="store", type="string", dest="sign_id",
                      help="sign_id for Sectools V2")
  
  parser.add_option("-v", "--sectools_version",
                      action="store", type="string", dest="sectools_version",
                      help="Sectools v1 or v2", default="v1")                         

  parser.add_option("-m", "--signing_mode",
                      action="store", type="string", dest="signing_mode",
                      help="Signing mode could be TEST,LOCAL,QTI-REMOTE,CASS", default="TEST")

  parser.add_option("--single_segment",
                      action="store_true", dest="single_segment", default=False,
                      help="combine all the config sections into one segment")
  
  parser.add_option("-r", "--signing_params",
                      action="store", type="string", dest="signing_params",
                      help="provide additional pass-through arguments to signing tool", default="")
  
  parser.add_option("-x", "--align",
                      action="store", dest="align", default="0x4",
                      help="alignment requirement config items in hex")

  parser.add_option("--integrity-image",
                      action="store_true", dest="integrity_image_generation", default=False,
                      help="Generate unsigned/integrity image with metadata in addition to signed image")

  parser.add_option("--integrity-image-no-metadata",
                      action="store_true", dest="integrity_image_no_metadata", default=False,
                      help="Generate unsigned/integrity image without metadata in addition to signed image")
  
  parser.add_option("-l", "--relocatable",
                      action="store_true", dest="relocatable", default=False,
                      help="Generate relocatable elf")

  parser.add_option("--store-original-size",
                    action="store_true", dest="store_original_size",default=False,
                    help="store orignal item size in cfg header, only save the acture size of actual item size in cfg header.")

  (options, args) = parser.parse_args()
  # Format must be supplied and be valid
  if not options.format or \
     (options.format != "ELF" and options.format != "ELF32" and options.format != "BIN"):
    parser.error("Format must be supplied and be ELF, ELF32, or BIN")

  if not options.config_file_to_be_disassembled: #xbl_config generation case
    if options.output_file and \
       os.path.isdir(os.path.split(os.path.abspath(options.output_file))[0]):
      output_xbl_config_directory = os.path.split(os.path.abspath(options.output_file))[0]
    else:
      parser.error("Output filename path without extension must be valid and exist.")
  else: #xbl_config disassemable case
    output_xbl_config_directory = get_abspath_if_exist(options.output_file, parser, "Output directory must be valid and exist.")

  # Auto generated files directory is optional. Process file path level to
  # contain intermediate files
  if options.autogen_directory and os.path.isdir(options.autogen_directory):
    autogen_directory = os.path.join(os.path.abspath(options.autogen_directory), AUTO_GEN_ITEM_FOLDER)
  else:
    autogen_directory = os.path.join(output_xbl_config_directory, AUTO_GEN_ITEM_FOLDER)
  remove(autogen_directory)
  create_directory(autogen_directory)
  # Dependent Tools (XBLconfig_metadata_generator, elf_gen etc.) path directory 
  if (not options.tools_path) or (not os.path.isdir(options.tools_path)):
    options.tools_path = os.getcwd()
  options.tools_path = os.path.abspath(options.tools_path)


  # If integrity image no metadata is set then also enable integrity image generation
  if options.integrity_image_no_metadata:
    options.integrity_image_generation = True

  
  # if XBL config disassemble option is not passed.
  if not options.config_file_to_be_disassembled:
    # Base directory must be supplied and exist
    options.base_directory = get_abspath_if_exist(options.base_directory, parser, "Base directory must be supplied and exist.")
    # check directory portion of the output filename path is valid and exist
    if not options.output_file or \
        not os.path.isdir(os.path.split(os.path.abspath(options.output_file))[0]):
      parser.error("Output file name without extension must be valid and exist.")
    # Set Paths
    output_xbl_config_directory = os.path.split(os.path.abspath(options.output_file))[0]
    output_xbl_config_filename = os.path.split(os.path.abspath(options.output_file))[1]  
    output_xbl_config_filename = output_xbl_config_filename + ".elf"  
    remove(os.path.join(output_xbl_config_directory, output_xbl_config_filename))
  
    # Input JSON path must be supplied and exist
    options.json_config_path = get_abspath_if_exist(options.json_config_path, parser, "JSON config file must be supplied and exist.")
   
    #generate XBL config file only when clean is false
    if not options.clean:
      generate_xbl_config_file(options.json_config_path,
                               options.format,
                               options.elf_address, 
                               output_xbl_config_filename,
                               options.base_directory,
                               output_xbl_config_directory, 
                               options.sectools_directory, 
                               autogen_directory,
                               options.tools_path,
                               options.soc_hw_version,
                               options.soc_vers,
                               options.sectools_version,
                               options.sign_id,
                               options.security_profile,
                               options.signing_mode,
                               options.single_segment,
                               options.signing_params,
                               options.align,
                               options.relocatable,
                               options.integrity_image_generation,
                               options.integrity_image_no_metadata,
                               options.store_original_size
                               )
  else:
    if not os.path.isfile(options.config_file_to_be_disassembled):
      parser.error("XBL config file must be supplied and exist.")        
    
	# Disassemble XBL config file only when clean is false
    if not options.clean:
      disassemble_xbl_config_file(options.config_file_to_be_disassembled,  
                                  options.format,
                                  output_xbl_config_directory, 
                                  autogen_directory,
                                  options.tools_path)

  exit(0)
