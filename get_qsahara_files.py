# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import os
import sys
import dtlogger
import importlib.util
from xml.etree import ElementTree as et
# --- 1. Define a simple logger class ---
class SimpleLogger:
    def log(self, message):
        dtlogger.info(f"META_LIB_LOG: {message}")

# --- 2. Main script logic ---
def get_all_sahara_files(meta_root_path, flavor=None, storage='ufs', firehose_type=None):

    """
    Initializes meta_info and uses get_qsahara_files to list Sahara files.

    Args:
        contents_xml_path (str): Path to the contents.xml file of the meta-build.
        flavor (str, optional): The flavor to filter by. Defaults to None.
        storage (str, optional): The storage type to filter by. Defaults to None.
        firehose_type (str, optional): The firehose type to filter by. Defaults to None.

    Returns:
        list: A list of file paths to Sahara files.
    """
    sahara_files = {}
    if not os.path.exists(meta_root_path):
        dtlogger.info("Error: meta path {} does not exist!".format(meta_root_path))
        return None
    
    contents_xml_path =  os.path.join(meta_root_path,"contents.xml")
    if not os.path.exists(contents_xml_path):
        dtlogger.info(f"Error: contents.xml not found at '{contents_xml_path}'")
        return None
    
    meta_lib_dir = os.path.join(meta_root_path,"common","build","lib")

    if not os.path.exists(meta_lib_dir):
        dtlogger.info(f"Error: meta lib path not found at '{meta_lib_dir}'")
        return None
    
    if meta_lib_dir not in sys.path:
        sys.path.append(meta_lib_dir)
        dtlogger.info(f"append '{meta_lib_dir}' to python sys path")
        dtlogger.info(f"sys path : '{sys.path}'")
    
    if not os.path.exists(os.path.join(meta_lib_dir,'meta_lib.py')):
        dtlogger.info("{} doesn't exist!".format(os.path.join(meta_lib_dir,'meta_lib.py')))
        return None
    #Import the meta_info class from meta_lib
    try:
        import meta_lib
    except Exception as e:
        dtlogger.info(f"import meta_lib : {e}")
        return None



    logger = SimpleLogger()
    
    # Instantiate the meta_info class
    try:
        # --- FIX: Removed 'on_linux' as a keyword argument ---
        meta_obj = meta_lib.meta_info(
            file_pfn=contents_xml_path,
            logger=logger,
            # fb_nearest=None,  # Your meta_lib.py *does* expect these if they're not optional
            # local_image=None  # in its actual __init__ definition. Let's make them None explicitly for safety.
        )
    except Exception as e:
        dtlogger.info(f"Error initializing meta_info: {e}")
        dtlogger.info("This often happens if contents.xml is invalid, or meta_lib.py has unfulfilled dependencies (e.g., 'fb_info_lib').")
        return None

    if flavor is None:
        flavor = meta_obj.get_product_flavors()
        if len(flavor)>0:
           flavor = flavor[0]   
        else:
           dtlogger.info('Build does not support any flavor')
           return None
    if storage is None:
        storage = meta_obj.get_storage_types()
        if len(storage) > 0:
            storage = storage[0]
        else:
            dtlogger.info('No storage type defined build')
            return None
    dtlogger.info(f"\nAttempting to get Sahara files from '{contents_xml_path}'...")
    dtlogger.info(f"  Flavor: {flavor}")
    dtlogger.info(f"  Storage: {storage}")
    dtlogger.info(f"  Firehose Type: {firehose_type}")

    try:
        # Call the get_qsahara_files method
        # Note: Your meta_lib.py has get_qsahara_files(self, flavor, storage, firehose_type=None, abs=True)
        # Ensure 'abs' is handled if you don't want absolute paths. Default is True.
        if hasattr(meta_obj, 'get_qsahara_files') == True:
            sahara_files = meta_obj.get_qsahara_files(
                flavor=flavor,
                storage=storage,
            )
        else:
            sahara_files = meta_obj.get_device_programmer(
                flavor=flavor,
                storage=storage,
            )
            if len(sahara_files) > 1:
                sahara_files = [sahara_files[0]]
        if sahara_files == {}:
            try:
            # getting files and picking first one from list assuming only one device programmer file should be present
                (executable_dir, executable_file) = os.path.split( meta_obj.get_files(file_types="device_programmer", flavor=flavor,storage = storage )[0] )
            except(IndexError):
            # did not find even one file
                dtlogger.info('ERROR: Couldn\'t properly parse for device programmer executable file (prog_emmc_firehose_XXX_ddr.elf)')
                quit()
            dtlogger.info(os.path.join(executable_dir,executable_file))
            sahara_files = {0:os.path.join(executable_dir,executable_file)}
        return sahara_files
    except Exception as e:
        dtlogger.info(f"Error calling get_qsahara_files: {e}")
        dtlogger.info("This could mean the contents.xml doesn't contain expected elements or attributes for Sahara files.")
        return None


# --- 3. Example Usage ---
if __name__ == "__main__":
    # IMPORTANT: Replace this with the actual path to your contents.xml file.
    # This file is typically found in the root of a Qualcomm meta-build.
    # Example: C:\path\to\your\meta_build\common\build\contents.xml
    # Or for the path you provided earlier (likely to the meta_lib.py itself)
    # the contents.xml would be somewhere above that, e.g., in the build root.
    
    # A placeholder for your actual contents.xml path
    # You MUST change this line to point to a valid contents.xml file in your meta-build
    # For example, if your meta_lib.py is at:
    # \\grilled\nsid-sha-spsp-02\Kaanapali.LA.1.0-00839-STD.INT-1\common\build\lib\meta_lib.py
    # then contents.xml might be at:
    # \\grilled\nsid-sha-spsp-02\Kaanapali.LA.1.0-00839-STD.INT-1\common\build\contents.xml
    
    meta_root_path = r"R:\Pakala.LA.1.0-01230-PERF.INT-1" 
    # Or if you know the exact path relative to where meta_lib.py is located
    # current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # # Assuming contents.xml is two directories up and then in 'build'
    # example_contents_xml = os.path.join(current_script_dir, '..', '..', 'build', 'contents.xml')

    # Example: Filter by UFS storage (if your contents.xml supports it)
    # You might also try: flavor="DEBUG", firehose_type="ufs" etc.
    # Refer to your contents.xml for actual valid values.
    
    # Get all sahara files without filters
    all_sahara_files = get_all_sahara_files(meta_root_path)
    if all_sahara_files:
        dtlogger.info("\n--- All Sahara Files Found (No Filters) ---")
        dtlogger.info("length of image:",len(all_sahara_files))
        for f in all_sahara_files:
            dtlogger.info(f,all_sahara_files[f])
    else:
        dtlogger.info("\nNo Sahara files found or an error occurred. Check logs above.")
