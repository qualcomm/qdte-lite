#!/usr/bin/env python3

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file package.py
This file packages the DTGUI application into a single executable (pyz file) and also provides a helper function to
extract resources from.

When run as a standalone file (i.e. python3 package.py), this file will package the entire DTGUI application into a
pyz file named "dtgui.pyz". It will copy all of the python files into a temporary directory and embed various resources
(e.g. user manual) and then call Python's zipapp to package everything nicely. Note that we don't want to do a regular
zipapp call for 2 reasons; firstly, there are other non-python files that we don't want to bundle with DTGUI in the
dtgui folder (and currently it doesn't seem as if there is any way to filter these out); and secondly, the user manual
needs to live in a place that can be opened by the user's PDF viewer, and unfortunately I haven't determined a way to
do so with pyz files.

In order to support loading of files in the packaged environment, all calls to fetch a resource should pass through the
fetch_resource() call in this file, which will determine whether the program is running in a packaged environment and
return the correct file path as necessary.

The way that embedded resources works is that an additional file is created when packaging called 'packaged_resources'.
This file contains the base64 encoded versions of the bz2 compressed files, as well as a function to decompress these
files into a temporary directory. When fetch_resouce() is called, it checks if the 'packaged_resources' file exists. If
it does, then it will tell packaged_resources to decompress the requested file. If 'packaged_resources' does not exist,
fetch_resource() will just return the path on the local filesystem.
"""
import shutil
import tempfile
import os
import base64
import bz2
import zipapp
from flags import global_info as gl_info
# these files will be available for programs to request when packaged; when not, they will simply be read from the file
# system. User Manual is copied for the user's convenience, and pyfdt README is copied for compliance with legal stuff.
# It shouldn't be hard to add some more files here as desired. Directories are not supported, though, unfortunately.
SAVED_RESOURCES = ['UserManual.pdf', 'pyfdt/README.md']

# name of the file to output to
AR_NAME = 'dtgui.pyz'

# the following variable contains the python code that unpacks the resources
# to see this file outside of the pyz, feel free to comment out the "shutil.rmtree(outdir)" line later below.
packaged_resources_src = '''
import tempfile
import atexit
import shutil
import os
import base64
import bz2

# KNOWN_RESOURCES is a variable created by package.py
KNOWN_RESOURCES = %s
stordir = ''

def init_stordir():
    # create new temporary directory
    global stordir
    stordir = tempfile.mkdtemp(prefix='dtgui_pkg_')

    # don't forget to clean up!
    atexit.register(del_stordir)

def del_stordir():
    # clean up, ignoring errors
    shutil.rmtree(stordir, ignore_errors=True)

def get_path_to(fullpath):
    if len(stordir) == 0:
        # temporary directory to extract resources to has not been set up yet, so create it
        init_stordir()

    if fullpath in KNOWN_RESOURCES:
        data = KNOWN_RESOURCES[fullpath]
        if '/' in fullpath:
            # contains directories, so we need to mkdir file's parents
            dirs = fullpath.split('/')
            # only take the directories
            filename = dirs[-1]
            dirs = dirs[:-1]
            try:
                # make all directories
                os.makedirs(os.path.join(stordir, *dirs))
            except OSError:
                # if directory exists already, etc. just ignore
                pass
            outpath = os.path.join(stordir, *dirs, filename)
        else:
            # just directly use the file name
            outpath = os.path.join(stordir, fullpath)
        with open(outpath, 'wb') as fp:
            # decompress the file and write it into the temporary directory
            fp.write(bz2.decompress(base64.standard_b64decode(data)))
        return outpath
    else:
        # unrecognized file
        return None
'''


def fetch_resource(identifier):
    """Fetch a path to a resource

    This function fetches the fully qualified path to a resource. If DTGUI is running from a pyz file, it will call into
     packaged_resources.py to return a path in a temporary directory. If not, it will get the file identifier relative
     to the script home directory (i.e., the directory where DTGUI code is located). In any case, if the file does not
     exist, it will return None.

    :param identifier: The identifier (most likely the file name)
    :return: Fully qualified path to the resource with the given identifier, or None if the resource is not found.
    """

    try:
        # will only work if we're in a pyz file
        import packaged_resources
        return packaged_resources.get_path_to(identifier)
    except ImportError:
        # not in a packaged environment, so just fetch the file as normal
        script_dir = os.path.dirname(os.path.realpath(__file__))
        script_dir = os.getcwd()
        if not os.path.exists(os.path.join(script_dir, identifier)):
            script_dir = gl_info['sign_json_path']
        fn = os.path.join(script_dir, identifier)
        if not os.path.exists(fn):
            # file does not exist on system
            return None
        else:
            # all good, file exists
            return fn


def pkg_app():
    """Package the DTGUI application into a pyz file

    Please see the documentation of the package.py file for more information on how this function works. It is called
    when package.py is run as a standalone file.
    """

    # create a temporary directory
    print('Create temporary directories... ', end='')
    outdir = tempfile.mkdtemp(prefix='dtgui_pkg_')
    os.mkdir(os.path.join(outdir, 'dtgui'))
    os.mkdir(os.path.join(outdir, 'dtgui', 'pyfdt'))
    print('OK!')

    # copy all python files over
    print('Copy DTGUI python files... ', end='')
    with os.scandir('.') as files:
        for entry in files:
            if entry.is_file() and entry.name.endswith('.py'):
                shutil.copyfile(entry.name, os.path.join(outdir, 'dtgui', entry.name))

    # rename the run.py file to __main__
    os.rename(os.path.join(outdir, 'dtgui', 'run.py'), os.path.join(outdir, 'dtgui', '__main__.py'))
    print('OK!')

    # copy pyfdt files over
    print('Copy pyfdt python files... ', end='')
    with os.scandir('pyfdt') as files:
        for entry in files:
            if entry.is_file() and entry.name.endswith('.py'):
                shutil.copyfile(os.path.join('pyfdt', entry.name), os.path.join(outdir, 'dtgui', 'pyfdt', entry.name))
    print('OK!')

    # generate the embedded resources variable/file
    KNOWN_RESOURCES = {}
    for resource in SAVED_RESOURCES:
        print('Read and parse resource %s... ' % resource, end='')
        with open(resource, 'rb') as fp:
            # compress the resources with bz2, encode the results in base64, and store the resultant string into the
            # KNOWN_RESOURCES object
            KNOWN_RESOURCES[resource] = base64.standard_b64encode(bz2.compress(fp.read())).decode('ascii')
        print('OK!')

    print('Write out packaged_resources... ', end='')
    # store the known resources variable into the file (we use repr() here because we know it will generate a safe
    # representation)
    my_pkgrs = packaged_resources_src % repr(KNOWN_RESOURCES)

    # write out the file
    with open(os.path.join(outdir, 'dtgui', 'packaged_resources.py'), 'w') as fp:
        fp.write(my_pkgrs)
    print('OK!')

    # generate the zipapp
    print('Output dtgui PYZ file... ', end='')
    try:
        zipapp.create_archive(os.path.join(outdir, 'dtgui'), target=AR_NAME, interpreter='/usr/bin/env python3',
                              compressed=True)
    except TypeError:
        print('Warning: your python version does not support exporting compressed files; the pyz may be larger as a '
              'result.')
        zipapp.create_archive(os.path.join(outdir, 'dtgui'), target=AR_NAME, interpreter='/usr/bin/env python3')
    print('OK!')

    # clear the temporary files
    print('Remove temporary directories... ', end='')
    # comment this next line out if you want to actually inspect the files that go into the pyz
    shutil.rmtree(outdir)
    print('OK!')

    print('Successfully output archive of DTGUI to %s!' % AR_NAME)


if __name__ == '__main__':
    # running this as a main script
    pkg_app()
