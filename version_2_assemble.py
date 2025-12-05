# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

import json
import assemble

from optparse import OptionParser
from pathlib import Path
from pyfdt.pyfdt import FdtBlobParse

from XBLConfig.commons import *
import dtlogger
# ============================================================================
# DISASSEMBLY HELPER FUNCTIONS
# ============================================================================


def walk_dtbs(dtbs_file, verbose):
    """
    Takes a DTBS file and extract all the DTBs found into separate files
    Turns it into a JSON similar to create_build_config.json that is able to be read from
    XBLConfig/XBLconfig_metadata_generator.py

    :param dtbs_file: Path to the DTBs file
    :param verbose: Boolean to turn on verbose mode
    """
    # First, read in the binary, line by line
    data = bytes()
    data = Path(dtbs_file).read_bytes()

    meta_dtbs_entry_json = {}

    # Create variables for the offsets of the various DTB files encountered
    dtb_start = 0
    dtb_end = 4
    num_dtbs = 0

    # The loop will terminate upon EOF or the first non-occurrence of D0 0D FE ED
    while dtb_end < len(data):
        d00d_feed_tag = data[dtb_start:dtb_end]
        if d00d_feed_tag == b'\x00\x00\x00\x00':
            return meta_dtbs_entry_json
        if d00d_feed_tag != b'\xd0\x0d\xfe\xed':
            # Put an error entry symbolizing that 0xD00DFEED was found
            meta_dtbs_entry_json["-1"] = {}
            return meta_dtbs_entry_json

        # Add the offset of this DTB to the entry dictionary
        num_dtbs += 1
        meta_dtbs_entry_json["dtb_" + str(num_dtbs)] = {}
        meta_dtbs_entry_json["dtb_" + str(num_dtbs)]["seg_offset"] = dtb_start

        # Total size is uint32_t according to DTSpec. These constants can be taken for granted.
        dtb_start += 4
        dtb_end += 4
        dtb_size = int.from_bytes(data[dtb_start:dtb_end], byteorder='big', signed=False)
        meta_dtbs_entry_json["dtb_" + str(num_dtbs)]["seg_size"] = dtb_size

        # Check that DTB size doesn't go beyond the end of the file
        if meta_dtbs_entry_json["dtb_" + str(num_dtbs)]["seg_offset"] + dtb_size > len(data):
            # Include an error entry
            meta_dtbs_entry_json["-2"] = {}
            return meta_dtbs_entry_json

        # Change end to be the size
        dtb_start = meta_dtbs_entry_json["dtb_" + str(num_dtbs)]["seg_offset"] + dtb_size
        dtb_end = dtb_start + 4

        if verbose:
            dtlogger.info(meta_dtbs_entry_json)

    return meta_dtbs_entry_json


def disassemble_dtbs_elf(config_file_to_be_disassembled, output_xbl_config_directory, autogen_directory,
                         tools_path, verbose):
    """
    Extract a DTBS.elf file

    Returns the path to the extracted DTBS.elf file as a JSON

    :param config_file_to_be_disassembled: The XBL Config ELF that we're breaking into segments
    :param output_xbl_config_directory: The output directory for the XBL Config ELF
    :param autogen_directory: The output directory for all automatically generated bins
    :param tools_path: The directory where all XBLConfig tools are. Traditionally, this is the XBLConfig directory
    :param verbose: Boolean to turn on verbose mode
    """
    # Disassemble the ELF into a JSON using XBLConfig/elf_gen.py
    disassembled_elf_info_json = os.path.join(output_xbl_config_directory, DISASSEMBLED_ELF_INFO_JSON)
    call_os_system("python \"" + tools_path + os.path.sep + ELF_GENERATOR_SCRIPT + "\"" +
                   " -d " + config_file_to_be_disassembled +
                   " -o " + autogen_directory +
                   " -e " + disassembled_elf_info_json)

    if verbose:
        dtlogger.info("\nDisassembled ELF into a JSON of the following structure:")
        dtlogger.info(disassembled_elf_info_json)

    return disassembled_elf_info_json


def disassembled_dtbs_to_separate_files(dtbs_file, dtb_entries, output_directory):
    """
    From a JSON with extracted offsets and DTB sizes, extract the bytes of each DTB and turn it into its own file

    :param dtbs_file: The path to the original DTBs file
    :param dtb_entries: The dictionary containing the sizes and offsets of each entry in the DTBs file
    :param output_directory: The output directory for the XBL Config ELF
    """
    # Open the binary
    data = Path(dtbs_file).read_bytes()
    existing_names = {}

    # Loop over all DTB file offsets and sizes from the dtb_entries dictionary
    for num_entry in range(1, len(dtb_entries) + 1):
        # First read the data into a buffer
        fixup_flag = False
        dtb_entry = dtb_entries["dtb_" + str(num_entry)]

        # Read in the length of the byte_array
        byte_array = data[dtb_entry["seg_offset"]: dtb_entry["seg_offset"] + dtb_entry["seg_size"]]

        # Create a new file and write our existing byte array to it
        filename = output_directory + os.path.sep + str(num_entry) + "_dtb.dtb"
        new_dtb_file = open(filename, "wb")
        new_dtb_file.write(byte_array)
        new_dtb_file.close()

        # Check to see if the file is an overlay file
        with (open(filename, "rb") as f):
            dt_parse = FdtBlobParse(f)
            dt = dt_parse.to_fdt()
            # Check to see if the extension is .dtbo
            if dt.resolve_path("/__fixups__"):
                fixup_flag = True

            # Check to see what the compatible names are
            # Go through a flowchart of the following:
            # See if /board-id/proc-name exists
            new_filename = filename
            value = ""

            # Rename the DTB to be more descriptive if the capabilities exist
            # First check /board-id/proc-name/ as it's the most specific
            if dt.resolve_path("/board-id/proc-name"):
                value = dt.resolve_path("/board-id/proc-name").__getitem__(0)
            elif dt.resolve_path("/board-id/compatible"):
                # Then check /board-id/compatible/
                value = dt.resolve_path("/board-id/compatible").__getitem__(0)
            elif dt.resolve_path("/compatible"):
                # As a last check, see if /compatible/ exists
                value = dt.resolve_path("/compatible").__getitem__(0)

            # If value was overwritten, rename the file
            if value != "":
                if value not in existing_names:
                    existing_names[value] = 0
                    new_filename = output_directory + os.path.sep + "%s.dtb" % value
                else:
                    existing_names[value] += 1
                    new_filename = (output_directory + os.path.sep + "%s_" + str(existing_names[value]) + ".dtb") % value
        # Rename to the proper name
        os.rename(filename, new_filename)

        if fixup_flag:
            os.rename(new_filename,
                      new_filename + "o")


def disassemble_version_2_elf(config_file_to_be_disassembled, output_xbl_config_directory, autogen_directory, tools_path,
                            verbose):
    """
    Combines version_2_disassemble methods into one overall function that's called within xblcfgint.py

    :param config_file_to_be_disassembled: The original input ELF to be disassembled
    :param output_xbl_config_directory: The output directory for the disassembled portions of the ELF
    :param autogen_directory: The output directory for all automatically generated bins
    :param tools_path: The directory where all XBLConfig tools are. Traditionally, this is the XBLConfig directory
    :param verbose: Boolean to turn on verbose mode
    """
    signed = True
    # First, disassemble the DTBS.elf file using the given ELF generator script
    disassembled_json_path = disassemble_dtbs_elf(config_file_to_be_disassembled, output_xbl_config_directory, autogen_directory,
                                             tools_path, verbose)

    # After the ELF has been disassembled into binaries, run a DTBS inspector purely on the sole binary
    # This runs on the sole binary, which can be found depending on whether this ELF is signed
    disassembled_elf_info_json = {}
    try:
        with open(disassembled_json_path, mode='r') as fp:
            disassembled_elf_info_json = json.load(fp)
            fp.close()
    except Exception as e:
        dtlogger.info(e)

    # Check to see if a signature DOESN'T exist
    if not "segment_1" in disassembled_elf_info_json:
        signed = False

    dtbs_file = autogen_directory + os.path.sep + "segment_1.bin"
    if not signed:
        dtbs_file = autogen_directory + os.path.sep + "segment_0.bin"

    if verbose:
        dtlogger.info("The DTBS file to unpack can be found at: " + dtbs_file)

    # Then, walk the DTBS file and create two JSONs for each of their directories
    meta_head_json, meta_entry_json = {}, {}

    meta_entry_json = walk_dtbs(dtbs_file, verbose)

    if "-1" in meta_entry_json or "-2" in meta_entry_json:
        if "-1" in meta_entry_json:
            dtlogger.info("ELF file doesn't consist entirely of DTBs. Moving onto legacy disassemble...")
            return -1
        if "-2" in meta_entry_json:
            dtlogger.info("Misshapen size in a DTB. Returning early.")
            return -2
        # Get rid of all files disassembled from this as long as they're not in the same directory as config
        if output_xbl_config_directory != os.path.dirname(config_file_to_be_disassembled):
            for file in os.listdir(output_xbl_config_directory):
                os.remove(os.path.join(output_xbl_config_directory, file))

        if autogen_directory != os.path.dirname(config_file_to_be_disassembled):
            for file in os.listdir(autogen_directory):
                os.remove(os.path.join(autogen_directory, file))

    # Turn each DTB within the DTBs into its own separate DTB file
    disassembled_dtbs_to_separate_files(dtbs_file, meta_entry_json, output_xbl_config_directory)

    # Clean directory of all bin
    for file in os.listdir(output_xbl_config_directory):
        if file.endswith("bin"):
            os.remove(os.path.join(output_xbl_config_directory, file))

    return 0


# ============================================================================
# REASSEMBLY HELPER FUNCTIONS
# ============================================================================
def reassemble_output_dtb_dtbs(dtb_directory, reassemble_dir):
    """
    Reassembles a directory of individual DTBs into a single DTBS file

    :param dtb_directory: The input directory containing disassembled DTBs
    :param reassemble_dir: The output directory for the DTBS file
    """
    # Open a new file within the given directory
    absolute_reassemble_path = os.path.abspath(reassemble_dir)
    new_dtbs_file = open(absolute_reassemble_path + os.path.sep +"reassembled.dtbs", "wb")

    # For each file read in from the DTB directory, append it to the new DTBS file
    for file in os.listdir(dtb_directory):
        if file.endswith(".dtb") or file.endswith(".dtbo"):
            data = Path(os.path.abspath(dtb_directory) + os.path.sep + file).read_bytes()
            new_dtbs_file.write(data)

    new_dtbs_file.close()
 
    # Create a temporary .dtbs file to pass into `reassemble_dtbs_elf`
    return absolute_reassemble_path + os.path.sep +"reassembled.dtbs"


def reassemble_dtbs_elf(dtbs_path, reassemble_dir, disassemble_dir, sectools_path, desired_name, verbose):
    """
    Packages a DTBS into an ELF using the given XBL config tool

    :param dtbs_path: The path to the DTBS file
    :param reassemble_dir: The output directory for the newly reassembled XBL Config ELF
    :param disassemble_dir: The input directory containing the outputs from disassembly
    :param sectools_path: The path to the sectools file for reassembly
    :param desired_name: The name of the new, reassembled ELF file
    """
    # Load info about the disassembled ELF
    disassembled_elf_info_json = {}
    try:
        with open(os.path.join(disassemble_dir, 'disassembled_elf_info.json'), mode='r', encoding="utf-8") as fp:
            disassembled_elf_info_json = json.load(fp)
            fp.close()
    except Exception as e:
        dtlogger.info(e)

    if verbose:
        dtlogger.info("\nDisassembled ELF info JSON follows the following format: ")
        dtlogger.info(disassembled_elf_info_json)

    # Change the desired name to relative if absolute
    if "/" in desired_name or "\\" in desired_name:
        if "/" in desired_name:
            desired_name = desired_name.split("/")[-1]
        else:
            desired_name = desired_name.split("\\")[-1]

    # Get parameters for sectools
    elf_class_int = 64
    target_arch = "AARCH64"

    if disassembled_elf_info_json["E_CLASS"] == "0x1":
        elf_class_int = 32
        target_arch = "AARCH32"

    elf_address = disassembled_elf_info_json["E_ENTRY"]

    try:
        if disassembled_elf_info_json['alignment'] is not None and int(disassembled_elf_info_json['alignment'],16)!=0:
            with open(dtbs_path,"ab") as output_fp:
                current_size = os.path.getsize(dtbs_path)
                alignment_bytes = int(disassembled_elf_info_json['alignment'],16)
                aligned_size = (current_size + alignment_bytes -1) // alignment_bytes * alignment_bytes
                padding_size = aligned_size - current_size
                if padding_size > 0:
                    dtlogger.info("Padding {} bytes to align to {}".format(padding_size, alignment_bytes))
                    output_fp.seek(current_size)
                    output_fp.write(b'\x00' * padding_size)
    except Exception as error:
        dtlogger.info(error)
        return None
        
    # Call sectools to generate an ELF from the DTBS segment
    dtlogger.info("\nentering sectools...")
    dtlogger.info(reassemble_dir)
    call_os_system(sectools_path + " elf-tool generate" +
                   " --elf-class " + str(elf_class_int) +
                   " --elf-entry " + elf_address +
                   " --elf-machine-type " + target_arch +
                   " --vaddr " + elf_address +
                   " --paddr " + elf_address +
                   " --align " + disassembled_elf_info_json['alignment'] +
                   " --data " + dtbs_path +
                   " --outfile " + os.path.abspath(reassemble_dir) + os.path.sep + desired_name + ".elf")

    return desired_name

def reassemble_version_2_elf(dtb_directory, reassemble_dir, sectools_path, desired_name, verbose):
    """
    Combines all reassembly helper functions in order.

    :param dtb_directory: The path to where the DTBs are for from disassembly
    :param reassemble_dir: The path to the directory where ./reassembled.dtbs will be output
    :param sectools_path: The path to the sectools file for reassembly
    :param desired_name: The intended name of the new, reassembled ELF
    :param verbose: Boolean to turn on verbose mode
    """
    dtlogger.info("\nentering dtb to dtbs...")
    dtbs_path = reassemble_output_dtb_dtbs(dtb_directory, reassemble_dir)

    dtlogger.info("\nentering dtbs to elf...")
    return_name = reassemble_dtbs_elf(dtbs_path, reassemble_dir, dtb_directory, sectools_path, desired_name, verbose)
    dtlogger.info(return_name)
    return return_name
