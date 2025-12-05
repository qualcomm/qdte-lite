# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
import platform
import argparse
"""
@file flags.py
This file contains the specification of various runtime flags that may be specified by the user.

These include the flags, default values, and help text.

Additionally, this file has validation logic to ensure that conflicting flags are not specified (e.g. since memory
usage profiling will increase execution speed of the program, performance profiling at the same time will be disabled).
"""

helpmsg = '''
DeviceTree GUI (DTGUI) Editor:\n
This tool provides a graphical way to make modifications to DeviceTree Blob files (DTBs). Supported changes include
 adding and removing nodes or properties, renaming properties, and changing the value of properties. DTGUI is also able
 to disassemble config elf files, edit the DTBs inside of them, and re-assemble/sign the config elf, provided that the
 right paths to the tools are given.
'''
if platform.system().startswith("Windows"):
    global_info = {
        "user_cfg": r"C:\ProgramData\Qualcomm\QDTE\user_cfg.json",
        "quts": r"C:\Program Files (x86)\Qualcomm\QUTS\Support\python",
        "quts2": r"C:\Program Files\Qualcomm\QUTS\Support\python",
        "meta_cli_t": r"common\build\app\windows_x86_64\meta_cli.exe",
        "tmp_xblcfg": r"C:\Qualcomm\QDTE\tmp_cfg",
        "log": r"C:\Qualcomm\QDTE\log",
        "sign_json_path":r"C:\Program Files (x86)\Qualcomm\QDTE"
    }
else:
    # Linux path
    global_info = {
        "user_cfg": r"/tmp/Qualcomm/QDTE/user_cfg.json",
        "quts": r"/opt/qcom/QUTS/Support/python",
        "meta_cli_t": r"common/build/app/windows_x86_64/meta_cli.exe",
        "tmp_xblcfg": r"/tmp/Qualcomm/QDTE/tmp_xblcfg",
        "log": r"/tmp/Qualcomm/QDTE/log",
        "sign_json_path": r"/opt/qcom/QDTE"
    }

config = {
    # testing flags
    '--coverage': {'nargs': '?', 'const': True, 'default': False, 'metavar': 'COVERAGE_FILE','help': argparse.SUPPRESS},
                #    'help': 'Generate a coverage report of the code executed at the end of the session. Automatically '
                #            'enables test mode and is not compatible with the profile flags.'},
    '--test': {'action': 'store_true', 'help': argparse.SUPPRESS},
                                            #    'Run in test mode. Exposes some features of the GUI that may be '
                                            #    'confusing to regular users, but useful when testing functionality and '
                                            #    'code coverage.'
                                            #    },
    
    '--verify_hash': {'action': 'store_true',   'help':argparse.SUPPRESS},
                                                    # 'help': 'Verify the stored hash of every item in the journal when '
                                                    #   'performing a re-do operation. Automatically enabled in test '
                                                    #   'mode.'},
    '--profile': {'nargs': '?', 'const': True, 'default': False, 'metavar': 'PROFILE_FILE','help':argparse.SUPPRESS},
                #   'help': 'Profile the application. If no file is specified, the program will print the output to '
                #           'stdout upon termination.'},
    '--profile_mem': {'action': 'store_true', 'help':argparse.SUPPRESS},#'help': 'Profile the memory usage of the program.'},
    '--detailed_console': {'action': 'store_true', 'help':argparse.SUPPRESS},
                                                #    'help': 'Show detailed output from GenXBLConfig scripts in the '
                                                #            'console window.'},
    '--nogui': {'action': 'store_true', 'default': False, 'help': 'Do not launch the GUI, run by command line mode '},
    '--dry_run': {'action': 'store_true', 'help':argparse.SUPPRESS},
                                                #'help': 'Do not actually write to any output file, but instead write out a '
                                                #'JSON change report that can be used in --nogui mode.'},
   
    '--sectools_dir': {'nargs': '?', 'const': None,  'metavar': 'SECTOOLS_LOCATION',
                       'help': 'Path of the sectools v2 signature tools, for signing config elfs. \n'
                               'Only avaiable when --allow_unsigned disable'},

    '--allow_unsigned': {'action': 'store_true', 'help': 'allow to generate unsigned config ELF.'},
    '--input_file': {'nargs': '?', 'const': None, 'default': '', 'metavar': 'DTB_ELF_FILE', 
                     'help': 'input DTB elf file.\n'
                     'Like xbl_config.elf, qdsp6sw_dtbs.elf'
                                                                                                            },
    '--modify': {'nargs': '?', 'const': None, 'default': None, 'metavar': 'MODIFY_LOCATION', 
                 'help': 'input the property and nodes which needs to be modified.\n'
                         'For multi properties,input by &.\n' 
                         'For multi values, input by ;\n'
                         'Format:\n'
                         '    Singal property: --modify \"platform.dtb/sw/boot/vibration=0\"\n'
                         '    Multi properties: --modify \"platform.dtb/compatible=Qcom,Kailua;Qcom,Aurora;Qcom,mtp&platform.dtb/model=Qualcomm Technologies, Inc. Kailua cdp\"\n'
                         '    Multi values: --modify  \"platform.dtb/compatible=Qcom,Kailua;Qcom,Aurora;Qcom,mtp\"'},
    '--sign_json': {'nargs': '?', 'const': None, 'default': None, 'metavar': 'SIGN_PARAMETER_JSON_LOCATION', 
                 'help': r'Please choose sign parameters json file from C:\Program Files (x86)\Qualcomm\QDTE\\n'
                         'For internal sign, please choose test_signing_mode.json\n'
                         'Only avaiable when --allow_unsigned disable'}, 
    '--output_path': {'nargs': '?', 'const': None, 'default': None, 'metavar': 'OUTPUT_LOCATION', 
                 'help': 'output path for storing dissamble files and re-assemble file \n'},
    '--output_file': {'nargs': '?', 'const': None, 'default': None, 'metavar': 'OUTPUT_FILENAME', 
                 'help': 'output file name.\nLike xbl_config.elf, qdsp6sw_dtbs.elf\n'},
    '--profileXml': {'nargs': '?', 'const': None, 'default': None, 'metavar': 'SECTOOL_PROFILEXML', 
                 'help': 'sectool profile xml file for signature!!\n'
                         'Only avaiable when --allow_unsigned disable\n'
                         r'Example: Kailua boot profile file kailua_tme_security_profile.xml comes from boot_images\ssg_tmefw\profiles\kailua\n'},
    
 
                   

}

flags = {
    'nogui': False,
    # debug mode will show the "Debug" menu in the controller and print out error tracebacks to console. it is enabled
    # by --test and --profile flags
    'debug': False,
    # read only mode is toggled by a checkbox in the debug menu and will prevent accidental edits from inline editing,
    # etc. this is not fully foolproof, though, and some edits will still be allowed.
    'readonly': False,
    # whether or not XBLConfig integration is enabled. Decided at launch based on whether the xbltools & sectools dirs
    # are specified.
    'xblEnabled': True,
    # whether to view values as hex (True) or decimal (False). Toggled by the user in the View -> Values As... menu
    'viewAsHex': False
}


def store(args):
    """Store the parsed arguments into the global flags dict

    This function fetches all of the parsed arguments from the argparse.ArgumentParser object and stores them into the
    global `flags` dictionary. It also validates the flags to ensure that conflicting flags have not been given.

    :param args: argparse.ArgumentParser object that has had all of the flags in config added, and had parse_args()
                 called on it
    """

    for arg in config:
        # we convert from the arguments' snake case first_second to camelCase firstSecond to store as keys in flags
        arg_camel = ''.join([word[0].upper() + word[1:] if i != 0 else word for i, word in enumerate(arg[2:].split('_'))
                             ])
        flags[arg_camel] = getattr(args, arg[2:])

    # custom handling code
    if flags['coverage']:
        flags['test'] = True
        if flags['profile'] or flags['profileMem']:
            print('Cannot profile and test coverage at the same time! Disabling profiling.')
            flags['profile'] = False
            flags['profileMem'] = False

    if flags['test']:
        flags['verifyHash'] = True

    if flags['profile'] and flags['profileMem']:
        print('Cannot profile both performance and memory at the same time! Disabling memory profiling.')
        flags['profileMem'] = False

    if flags['test'] or flags['profile'] or flags['profileMem']:
        flags['debug'] = True
    else:
        flags['debug'] = False
