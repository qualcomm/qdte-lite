# Notes for maintainers

Hello, future maintainer!

## Resources for understanding

### User Manual

This document contains a user-level view of the features and capabilites of the DTGUI.
It is highly recommended to read and familiarize yourself with the contents of this document before proceeding further.

### This file

In this file I have listed some possible future expansions for the DTGUI software and how I would go about implementing them.
It is my hope that, through these specific examples, one may gain a general understanding of the thinking behind the layout of the code.

### The code

Each file should contain comments and pydoc describing what it does.
Although an effort has been made to add pydoc comments to each function, too, not all functions may have such documentation,
and some documentation may be stubs.

#### Files

* `assemble.py` - disassemeble and reassemble function entities which will call genxblcofnig.py  .
* `Autocmd.py` - cmd line executor.
* `controller.py` - Primary controller (event router, communication between other views, etc.) for the DTGUI application.
* `dbgutil.py` - Some debugging utilities.
* `dtwrapper.py` - Wrapper that consolidates all functions that interface with or modify the device tree into a single file.
* `editview.py` - GUI elements of the DeviceTree edit window, and smart inline editing.
* `findview.py` - Helper window that gets user optons for finding a given string in the DeviceTree.
* `flags.py` - Specification of various runtime flags that may be specified by the user.
* `hexview.py` - GUI elements of the DeviceTree hex viewer (raw view) window.
* `package.py` - Tool to package the DTGUI application into a single executable (pyz file) and also provides a helper function to extract resources from.
* `run.py` - Main entry point to the DTGUI application.
* `treeview.py` - GUI elements of the DeviceTree tree viewer/editor application.
* `settings.py` - GUI of all settings.
* `sign.py` - signature functions.
* `xblcfgint.py` - GUI of disassemble and reassemble XBLConfig ELFs.



### The Internet

Especially if not particularly familar with Python or Tkinter, searching up some questions online may be helpful.

---

## Future expansion ideas

Although these are specific examples, the goal is that they can serve as a general framework for other kinds of changes.

Also, in these examples, I use the words "should", "will", etc. These are just my suggestions to you, dear maintainer.
If you would like to completely rewrite everything, or start using your own way of organizing the code that makes more
sense to you, I am powerless to stop you.

### Generate/display DTB hash on demand

The logic parts of this feature (i.e. hashing) would be done in the `dtwrapper.py` file, and the GUI elements
would belong in `controller.py`. 

#### Exposing DTB hashing functionality in the DTWrapper

Currently, there is a top-level function named `_dtb_hash` in the `dtwrapper.py` file.
This function is not intended to be called by other portions of the program.
A new function should be added to the `DTWrapper` class that will call the `_dtb_hash` function and return the results.
This is because the `DTWrapper` class is the one that keeps track of the current DTB in the `dtb` instance variable,
so other places should not have access to the DTB and thus would not be able to call the `_dtb_hash` function on it).

#### Difference between controller.py and dtwrapper.py

 `Controller.py` acts as the primary controller and event router for the DTGUI application. It accepts input and calls functions in `dtwrapper.py` to obtain results. `dtwrapper.py` acts as the wrapper that contains all the functions that interact with the device tree. It accesses and/or modifies the device tree based on the functionality requested by the end user.

#### Importing pyfdt into controller.py for copy_node

The `copy_node` function in the `controller.py` copies a node recursively from one location in the device tree to another. This feature also enables the user to create a new path of nodes in the tree if the copied node is copied to a path in the tree that does not already exist. We need to find the exact point of the copied node path that does not exist in the existing tree and needs to be created. We find this path so that we can call `self._update_views` from that point in order to update GUI. If the path already exists in the tree, we call it for the new copied node that has been created.

Pyfdt was not required in other functions so far because in the other functions we are always certain what is the node that is being added. In this function, we are unsure whether the node being added at the highest level of the tree will be the copied node or one of its parents in the path. So we preemptively import the tree and check.

#### Adding a menu option to display the current DTB hash

The most intuitive option to display the current DTB hash would likely be a menu option, e.g. View -> DTB Hash.

Menu options are set up in the `controller.py` file in the `DTGUIController` class in the `_init_menus` function.
In particular, the View menu is a local variable named `view_menu` in this function.
By calling `view_menu.add_command()` in the `_init_menus` function, one can add new menu options to the View menu.
The `label` parameter is the string that will display, the `accelerator` parameter is the keyboard shortcut that will
display on the right
(**note that adding the accelerator variable will NOT bind the key; one must also add a key binding in `_init_key_bindings` for the shortcut to work**),
and `command` is the function that will be called when the menu item is clicked.
The `command` option should point to a new function whose implementation is described below:

#### Displaying the current DTB hash

In order to display the current DTB hash, a new function will need to be added to the `DTGUIController`.

This function should first call the newly implemented DTB hashing function located in the DTWrapper.
The controller's instance of the `DTWrapper` class can be accessed with the `self.dtw` variable.

Unfortunately, I am not aware of any builtin Tkinter dialogs that can display copiable text, so a new window may
need to be created. In either case, the handler function for the menu item should display the text returned by
the new `DTWrapper` function in some way to the user.

### Validate that phandles are unique in the DeviceTree

`dtwrapper.py` handles low-level interactions with the DeviceTree specification (which phandles would be considered a part of),
so phandles should be managed in that file.

In the `dtwrapper.py` file, there are various DTOperations. The code to apply (and possibly undo) add, remove, edit value,
and rename operations will all need to check if the property they are operating on is a phandle, and if yes, somehow
keep track and ensure that the values are unique.
If the uniqueness check fails, then the apply/undo functions can throw a ValueError (or similar exception) and
the `DTGUIController` will catch the error and display an error dialog box to the user.

#### Keeping track of phandles

I am not actually quite sure how to do this.
Most likely, I would create a new class in the `dtwrapper.py` file that has a dictionary to keep track of all
of the current phandle values and their corresponding paths, as well as the reverse mapping (paths to phandles).

This new class would likely need to be passed to the `apply()` and `undo()` functions of all of the `DTOperation`s
so that they could update the class as appropriate (e.g., when phandle values change or
when a property is renamed to `phandle`)

#### Side effect: looking up phandles

If the `DTWrapper` class exposed a new function to call into the class that keeps track of phandles and look up
a phandle by its number, it could be possible to add a right-click context menu option in the TreeView to display
the phandle in tree (e.g. "Jump to Phandle"). The right-click context menu is built in `treeview.py` class `TreeView`
in the `show_context_menu` function. There is currently a check for if the `selected_item.is_property()` in the code.
In this logic branch, an additional check could be added to detect if the `selected_item` is a `WORDS` type,
only has a single value, and points to a known phandle. If yes, one could add an additional menu option to call the
`TreeView` `show_path` function on the path corresponding to the phandle.

### Add a checkbox to toggle detailed console window in XBLConfig Helper window

Currently, the user must specify the `--detailed_console` flag in order for detailed console output to display.
It may be desirable to have this be an option that can be modified at runtime.
This is a change to the XBLConfig integration behavior, so changes should be going in the `xblcfgint.py` file.

#### Placement of the checkbox
The UI components of the XblCfgGUI are initialized in the `init_components()` function.
A grid layout is currently in use for the dialog; the grid has 5 rows and 2 columns (although currently all items
are configured with a colspan of 2). The first column will expand its width as the window is resized, and the
second column will maintain its width. A checkbox could be placed in the 3rd row with the Reassemble button,
in a different column (which would also require reduing the column span of the reassemble button).
Another possible option could be to place the checkbox in a new 6th row.

#### Handling checkbox value updates
In order to detect when the value of the checkbox is changed, a Tkinter BooleanVar needs to be set up, and a `trace`
function handler added to it. Examples of such tracing can be seen with the `hexViewShowing`
variable in the `DTGUIController` in `controller.py`. Once the event handler has been called, it is possible
to toggle a variable to `True` or `False` as necessary.

#### Making the change
In order to update the console view, the `gf['detailedConsole']` value needs to be updated to `True` or `False` to display
detailed console messages or hide them, respectively.

#### Notes
The code that logs the lines to the XblCfgGUI console is the `logline` function in the `XblCfgGUI` class.
Please consult the code to understand why changing the `gf['detailedConsole']` value works.

### Persist user settings to disk

Currently, there is not a proper "settings" system. Most "settings" are really just flags that are set with defaults.
In any case, these flags are currently handled in the `flags.py` file.
Other files usually import the `flags` dict in `flags.py` as `gf` and then access and modify the flags as necessary.
If a proper preferences pane were to be added, renaming this file may help with understanding the usage of the file.
Even if not, it would be possible to store the `flags` dict in `flags.py` to disk.

#### Deciding which flags to save

In `flags.py`, there are two objects. Firstly is the `config` dict, which describes the command-line flags and how they are configured.
This dict is passed in to the argument parser. Note that the keys here use snake_case. The other dict is the `flags` one,
which, in the file, contains some additional flags with their default values. The user does not have any command-line flags that will
set these directly (although they may be changed as a side effect; e.g. `flags['debug']` will be set if the tool is run with the `--test` flag).
Note that the keys here use camelCase. When the program is run, all of the parsed arguments will be added to the `flags` dict in camelCase, too.

An important note is that, as it currently stands, if there is a duplicate key already in `flags`, it will be overwritten by any call to `flags.store()`.
To change this behaviour, one would need to modify the loop in that function that scans `for arg in config` and add an extra line to first check if
the current value is default, and if it is, and a value for that argument already exists in `flags`, to not overwrite the existing value.

#### Picking where to save

I leave this question to the reader. A temporary directory is commonly used in this program, but for things to persist,
a different directory will need to be used. One hint that I may offer is that persistent directories vary depending on the user
operating system. In `controller.py` class `DTGUIController` function `open_manual`, there is some code that determines the currently
running operating system. This snippet may be useful.

#### Loading and saving flags

The `flags.store()` function is called exactly once at the start of every run, so it would be safe to put code to read in a pickled/JSON/etc. version
of the previous run's `flags` variable, and then parse arguments to overwrite any flags where appropriate.

There is currently no nice way to save flags, since various programs currently directly access the `flags` dict and reda/modify its values. One possible way to
fix this is to change `flags` to a custom dict that still supports the Python `__setitem__` and `__getitem__` calls, but would add some special code to
save the flags when `__setitem__` is called. Another possible way is to change the current behaviour to no longer directly access the `flags` dict and instead
call into a new `flags.py` function to get and/or set flags.

### Aside - How to write a Python binding to a C library

The `ctypes` library in Python deals with interfacing with `.dll` and `.so` libraries.
