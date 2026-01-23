# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
@file treeview.py
@description Initialize all of the GUI elements of the DeviceTree tree viewer/editor application
@author Dhamim Packer Ali, Michael Turney, Mason Xiao
References:
   http://hg.python.org/cpython/file/4e32c450f438/Lib/tkinter/ttk.py
   http://www.tcl.tk/man/tcl8.5/TkCmd/ttk_treeview.htm#M79
   http://svn.python.org/projects/python/branches/pep-0384/Demo/tkinter/ttk/dirbrowser.py

This file contains the code that initializes and handles events for the main tree view portion of the DTGUI application.

It is comprised of a single large TreeView class, which is the object-oriented class used to represent a DeviceTree Tree
View component. Inside the class, there are functions to initialize the ttk Treeview (which this component is mostly
a fancy wrapper around), catch events (e.g. double-clicking, deleting items, or highlighting) to pass to the main DTGUI
controller component (controller.py), and handle incoming events from the controller (e.g. property name/value has been
updated by the user or highlighting changed).

In general, the structure of this file is such that it handles incoming events from the user and passes them on to the
controller to handle; in general, the view does not speak with any other views directly. Notable exceptions to this rule
include when the user right clicks (the TreeView will only notify the controller when the user has used the right click
menu to decide upon an action) and when the user is using inline editing (the TreeView will only notify the controller
if an edit is actually made).

The decision to make inline editing work solely within the TreeView was difficult, since doing so means that the
TreeView will interface with the DtbSmartEntry (editview.py). However, doing so is also able to simplify the code a lot.
Most importantly, the DtbSmartEntry is placed at a specific location on the screen in order to overlay the value cell
in the TreeView, but one important concept behind the controller in this project is that it should not need to know the
details of exactly where components on the screen are, and only be informed when events occur. Thus, since the TreeView
is the only component that knows where the DtbSmartEntry should go, it is also the component that creates and interfaces
with the Entry, even though doing so somewhat breaks the previously established rules.
"""

# tkinter library
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import tkinter.colorchooser

# fdt interface
import dtwrapper as dt

# configuration, debug, etc.
from flags import flags as gf

# custom inline editor
from editview import DtbSmartEntry


class TreeView(tk.Frame):
    style = None
    editPopup = None
    editPopupRow = None
    lastEditRow = None
    update_last_column = False

    def __init__(self, parent, controller):
        """Initializer for TreeView component

        Initializes some local variables and calls _create_treeview() to set up all of the subcomponents that make up
        the DTGUI TreeView (scrollbars, ttk treeview, etc.)

        :param parent: The root tk.Tk() instance
        :param controller: The DTGUIController that this TreeView is inside of
        """

        # we are actually a child of a frame, so initialize our parent first
        tk.Frame.__init__(self, parent)

        # set up variables
        self._controller = controller
        self._root = parent
        self.treeMappings = {}

        # set up custom styling for the top label row of the treeview
        self.style = ttk.Style(parent)
        self.style.configure("mystyle.Treeview.Heading", font=('Calibri', 11, 'bold'))  # Modify heading font
        self.style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove borders
        self.style.map('mystyle.Treeview', foreground=self.fixed_map('foreground'),
                       background=self.fixed_map('background'))

        # create the actual treeview components
        self._create_treeview()

    def _create_treeview(self):
        """Internal function to set up all of the parts that make up the TreeView component

        This function sets up all of the parts that make up the TreeView component. First, there is `self` (a Tkinter
        Frame). Inside of `self` there is another frame `f` filling it entirely. Inside of `f`, there is a grid system.
        Row 0 column 0 is the ttk Treeview `self.tree`. Row 0 column 1 is the vertical scrollbar `ysb`. Row 1 column 0
        is the horizontal scrollbar `xsb`. Row 1 column 1 is empty.

        This function also registers the event handlers for various ttk Treeview events.
        """

        # create the wrapper frame
        f = tk.Frame(self)
        f.pack(side='top', fill='both', expand='y')

        # create the tree and scrollbars
        self.dataCols = ('fullpath', 'item type', 'data type', 'value')
        self.tree = ttk.Treeview(f, height=30, style="mystyle.Treeview", columns=self.dataCols,
                                 displaycolumns=('item type', 'data type', 'value'))

        ysb = tk.Scrollbar(f, orient='vertical', command=self.tree.yview)
        xsb = tk.Scrollbar(f, orient='horizontal', command=self.tree.xview)
        self.tree['yscroll'] = ysb.set
        self.tree['xscroll'] = xsb.set

        # setup column headings text and default widths
        self.tree.heading('#0', text='device tree layout', anchor='w')
        self.tree.column('#0', width=500)
        self.tree.heading('item type', text='Item Type', anchor='w')
        self.tree.column('item type', stretch=0, width=150)
        self.tree.heading('data type', text='Data Type', anchor='w')
        self.tree.column('data type', stretch=0, width=150)
        # TODO: uncommenting this line will display whether the values are currently hex or decimal. since we currently
        # display hex values with 0x____ this is not really necessary.
        # self.tree.heading('value', text='Value (%s)' % ('Hex' if gf['viewAsHex'] else 'Decimal'), anchor='w')
        self.tree.heading('value', text='Value(s)', anchor='w')
        self.tree.column('value', width=300)

        # add tree and scrollbars to frame
        self.tree.grid(in_=f, row=0, column=0, sticky='nsew')
        ysb.grid(in_=f, row=0, column=1, sticky='ns')
        xsb.grid(in_=f, row=1, column=0, sticky='ew')

        # set frame resizing priorities (scrollbars do not resize, but the main ttk tree view does)
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        # treeview interactions
        self.tree.bind('<Button-1>', self.on_click)
        self.tree.bind('<Double-Button-1>', self.expand_item)
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<<TreeviewOpen>>',self.set_update_last_column_flag)
        self.tree.bind('<<TreeviewClose>>',self.set_update_last_column_flag)
        self.tree.bind('<ButtonRelease-1>',self.update_last_column_width)
        # inline editing
        self.tree.bind('<Tab>', self.tab_pressed)
        self.tree.bind('<Shift-Tab>', self.shifttab_pressed)
        try:
            # on Linux only, this is Shift+Tab
            self.tree.bind('<ISO_Left_Tab>', self.shifttab_pressed)
        except tk.TclError:
            # above key combination is only for Linux
            pass
        self.tree.bind("<Configure>", self.window_resize)
        # TODO: may need to bind Button-4 and Button-5 on Linux to catch scroll
        self.tree.bind("<MouseWheel>", self.on_scroll)

    def _populate_tree(self, path='/', parents=None):
        """Internal call to add new elements to the tree view

        This function adds new items to the Ttk tree view. It is the only function that does so. It supports adding a
        single property (add property operation), single node (add node operation), or a node and all of its children
        (undoing a deletion of a node that had children or initial open of a DTB). This method calls into the
        DTWrapper's node resolving and walking functionality in order to support these functionalities.

        :param path: Path to the base to start adding new nodes at. Default is '/', which means to reset all existing
                     items in the tree and add new ones.
        :param parents: Dictionary storing information on which paths have which row ID's as parents. This is necessary
                        in order to properly add new items as children of the correct node. Default is None, which will
                        cause issues if the path is not also the default of '/' since the code will try to look up the
                        parent of the path in the dictionary and will be unable to find it.
        """

        if self.editPopup is not None:
            # opened a new file or something like that, but an inline editing box was still open. it's too late to save
            # now, so we just discard the changes.
            self.editPopup.destroy()
            self.editPopup = None
        if not self._controller.dtw.has_file():
            # no file open
            return

        if path == '/':  # reset everything
            # insert root node at top of tree
            # 'values' = column values: fullpath, type, propertytype, value
            # expand root node by default
            tree_root = self.tree.insert('', 'end', text=path, values=[path, 'Node', '', ''],open=True)

            # note the different format of the parents and self.treeMappings variables, which prevents us from being
            # able to simply share a set of variables.
            parents = {'': tree_root}
            self.treeMappings = {'/': tree_root}
        else:  # we only want to populate a specific part of the tree
            # we have to add the node itself first because the DTWrapper walk() won't walk to this node
            parent_node = path.rsplit('/', 1)[0]
            # note that we get the parent index here, too, so that if we are undoing an operation, we don't add to the
            # end of the treeview/dtb and instead add to the correct place it was before
            elem, elem_idx = self._controller.dtw.resolve_path(path, want_parent_idx=True)

            if elem.is_property():
                r = self.tree.insert(parents[parent_node], elem_idx, text=path, values=[path, 'Property',
                                                                                        elem.get_type(),
                                                                                        elem.to_pretty()])
                self.treeMappings[path] = r
            elif elem.is_node():
                # when adding nodes, we always want to store the row id of it in case it has children that will need
                # this info later
                parents[path] = self.tree.insert(parents[parent_node], elem_idx, text=path, values=[path, 'Node', '',
                                                                                                    ''])
                self.treeMappings[path] = parents[path]

        node = self._controller.dtw.resolve_path(path)
        if not node.is_node():
            # cannot walk; this is a property. we have already added it, so we are done here
            return
        for (path, item) in node.walk():
            # get the parent of this node
            parent_node = path.rsplit('/', 1)[0]
            if item.is_property():
                r = self.tree.insert(parents[parent_node], 'end', text=path, values=[path, 'Property', item.get_type(),
                                                                                     item.to_pretty()])
                self.treeMappings[path] = r
            elif item.is_node():
                # when adding nodes, we always want to store the row id of it in case it has children that will need
                # this info later
                parents[path] = self.tree.insert(parents[parent_node], 'end', text=path, values=[path, 'Node', '', ''])
                self.treeMappings[path] = parents[path]

    def fixed_map(self, option):
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        return [elm for elm in self.style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]

    def update_fdt(self, path=None):
        """Update the tree view based on changes made to the DeviceTree

        When changes occur to the FDT, this function is called to notify the TreeView of any changes. Either the entire
        TreeView can be updated, which will clear everything and repopulate the tree, or a specific path can be updated,
        which will preserve existing state (i.e. scroll position, which items are expanded/collapsed) while updating
        the path by adding/deleting/changing the appropriate rows in the tree view.

        :param path: Path to the portion of the DeviceTree that needs updating. Defaults to None, which means that the
                     entire TreeView will be reset.
        """

        if path is None or not self._controller.dtw.has_file():
            # we don't know what to update, so we have to reset everything
            self.tree.delete(*self.tree.get_children())
            self._populate_tree()
            return

        # check if the item is in the devicetree
        item = self._controller.dtw.resolve_path(path)
        path_parent = path.rsplit('/', 1)[0]
        parent = self.treeMappings.get(path_parent if len(path_parent) > 0 else '/', None)
        parents = {path_parent: parent}
  
        if item is None:
            # the path no longer exists in the DeviceTree, so we want to delete this item
            row = self.treeMappings.pop(path, None)

            if row is None:
                # not in the mapping anyways, so skip
                return

            children = self.tree.get_children(row)
            if len(children) > 0:
                self.tree.delete(*children)
            self.tree.delete(row)
        elif item.is_property():
            # this is a property, so we are either updating its value or adding it
            row = self.treeMappings.get(path, None)

            if row is not None:
                # updating existing property
                self.tree.item(row, values=[path, 'Property', item.get_type(), item.to_pretty()])
            else:
                # adding new property
                self._populate_tree(path, parents)
        elif item.is_node():
            # this is a node, so it may have children that we have to update, too
            self._populate_tree(path, parents)

        # update highlights
        self.clear_highlights()
        self.update_highlights()
        self.set_update_last_column_flag(None)
        self.update_last_column_width(None)

    def traverse_tree(self,tree,parent = "",column = 0):
        item_text = ''
        item_text_length = 0
        for item in tree.get_children(parent):
            if len(self.tree.item(item)['values'])>=3 and tree.bbox(item)!='':
                item_text_length = tkFont.Font(family='Calibri',size=11).measure(str(self.tree.item(item)['values'][column]).strip())
                if item_text_length > self.max_column_length:
                    self.max_column_length = item_text_length
            self.traverse_tree(tree,item,column)

    
    def update_last_column_width(self,event=None):
        """Update last column width when visible item was changed 
        When the visible item changed (like expand/collapse/modify))

        """
        column = 3
        self.max_column_length = 0
        if self.update_last_column:
            self.update_last_column =  False
        else:
            return
        self.traverse_tree(self.tree,None,column)
        if self.max_column_length != 0 and self.max_column_length >100:
            self.tree.column(column,width = ( self.max_column_length))

    def set_update_last_column_flag(self, event=None):
        self.update_last_column = True

    def update_viewstyle(self):
        """Callback when the view style has been updated (hex/decimal change)

        When the view style changes from hex to decimal or vice versa, all of the properties' values in the tree view
        need to be synced with the current user preference. This function does the updating.
        """

        # TODO: uncommenting this line will display whether the values are currently hex or decimal. since we currently
        # display hex values with 0x____ this is not really necessary.
        #self.tree.heading('value', text='Value (%s)' % ('Hex' if gf['viewAsHex'] else 'Decimal'), anchor='w')

        # loop through all of the items in the tree
        for path, item in self._controller.dtw.resolve_path().walk():
            # ... if the item is a property ...
            if item.is_property():
                # ... get the corresponding row in the tree view
                row = self.treeMappings.get(path, None)
                if row is not None:
                    # and if it isn't none, update the item with the new view style
                    self.tree.item(row, values=[path, 'Property', item.get_type(), item.to_pretty()])

    def _get_item_at_pos(self, y):
        """Get the row of the tree view corresponding to a given y-position in the tree view

        This is an internal helper function that gets the row of the tree view that is at the given y coordinate. It is
        used to get the node to edit/modify when handling mouse events (right click, double click, etc.).

        :param y: The y position of the item in question. Should be taken from an Tkinter mouse event.
        :return: Tuple of 3 items: first, the corresponding row ID; second, the path corresponding to that row; and
                 finally, the Fdt item at that path. If there is no item at that position (e.g. tree view has not been
                 expanded and user is clicking on empty space), then the tuple will still have 3 items, but they will
                 all be None.
        """

        # ask the tree view for the row; this returns the row ID if successful
        row_id = self.tree.identify_row(y)
        if row_id == '':
            # tree view did not find a row at this coordinate, so return None
            return None, None, None
        # get the path for this row
        row_text = self.tree.item(row_id, 'text')
        # return the row id, path, and resolved corresponding FdtItem
        return row_id, row_text, self._controller.dtw.resolve_path(row_text)

    def highlight(self, path, bg_color, fg_color):
        """Highlight an item in the tree view of the DeviceTree

        This is the function called by the controller to notify the tree view of a single new highlight. The controller
        will tell the TreeView to highlight a path with a background and foreground color (the controller is the one
        that decides the foreground color depending on if it is a darker or lighter background). This function will
        create a new (unique) tag for the highlight in the tree view and then tag all of the DeviceTree items matching
        that path with the new tag.

        :param path: Path to highlight. Can point to node or item. Pointing to a node will highlight all of the node's
                     children, too.
        :param bg_color: desired background color as a hex color string (e.g. '#FFFFFF')
        :param fg_color: desired foreground color as a hex color string (e.g. '#000000')
        """

        # decide on a nice tag name that (ideally) should be unique
        tag_name = 'HL_%s_%d' % ('_'.join(path.split('/')), len(self._controller.knownHighlights))
        # create the tag with the given foreground and background colors
        self.tree.tag_configure(tag_name, background=bg_color, foreground=fg_color)

        if path not in self.treeMappings:
            # path not found in the tree mappings - maybe this highlight has been deleted?
            # dtlogger.info('Failed to highlight in TreeView; mapping not found for %s' % path)
            return

        # get the row corresponding to this path using the mappings
        my_row = self.treeMappings[path]

        # sometimes the row is in the mappings but the row itself has been deleted, so we need to catch and ignore
        # those cases, too
        try:
            # set the row itself to have the tag
            self.tree.item(my_row, tags=tag_name)
        except tk.TclError:
            # dtlogger.info('Failed to highlight in TreeView; mapping not found for %s' % path)
            return

        # also set the tag on all of the row's children
        self._setprop_all_children(row=my_row, tags=tag_name)

    def clear_highlights(self):
        """Remove all highlights

        This function clears (resets) all of the highlights in the tree view.
        """

        # clear all existing highlights by clearing all of the tags
        self._setprop_all_children(tags=())

    def update_highlights(self):
        """Re-synchronize highlights with controller's list

        This function pulls the list of all known highlights from the controller and re-highighlights (using the
        highlight() function) all of them. It should called whenever the tree view has had any of its elements changed.

        Note that this function does not clear existing highlights by itself. You will need to call clear_highlights()
        to do so.
        """

        # update all of the highlights from controller
        for highlight in self._controller.knownHighlights:
            # unpack the highlight information into the highlight() function call
            self.highlight(*highlight)

    def show_context_menu(self, event):
        """Event handler to display the right-click context menu when the user right-clicks

        This is the event handler that is called when the user right clicks in the tree view. It will attempt to
        determine if the user is right clicking on a tree view item, and if so, display the appropriate context menu
        depending on the item that is right clicked (for example, only nodes have the ability to add children to them).

        This function is also where all of the preset highlight colors are set up.

        :param event: The tkinter event object containing information on the right click mouse event
        """

        if self.editPopup is not None:
            # close the inline edit popup if it's open
            self.editPopup.on_return()
            self.editPopup = None

        # determine the corresponding item in tree that the user has right clicked on
        selected_row, selected_path, selected_item = self._get_item_at_pos(event.y)
        if selected_path is None:
            # right click was not on a known area
            return

        event.widget.focus()
        # open menu
        rmenu = tk.Menu(None, tearoff=0)

        # always allowed to highlight
        # note that all of the highlight functions here call the controller and do not call the treeview's highlight
        # function, to alow the controller to be the central managing place of all highlight information.
        hmenu = tk.Menu(rmenu, tearoff=0)
        hmenu.add_command(label='Red', command=lambda: self._controller.highlight(selected_path, '#ff0000'))
        hmenu.add_command(label='Orange', command=lambda: self._controller.highlight(selected_path, '#ff9600'))
        hmenu.add_command(label='Yellow', command=lambda: self._controller.highlight(selected_path, '#ffff00'))
        hmenu.add_command(label='Green', command=lambda: self._controller.highlight(selected_path, '#00d400'))
        hmenu.add_command(label='Blue', command=lambda: self._controller.highlight(selected_path, '#007dd4'))
        hmenu.add_command(label='Purple', command=lambda: self._controller.highlight(selected_path, '#7d00ff'))
        hmenu.add_command(label='Pink', command=lambda: self._controller.highlight(selected_path, '#ff00ff'))
        hmenu.add_command(label='White', command=lambda: self._controller.highlight(selected_path, '#ffffff'))
        hmenu.add_command(label='Custom...', command=lambda: self._controller.highlight(selected_path,
                                                                                        tk.colorchooser.askcolor(
                                                                                            title='Custom '
                                                                                                  'highlight'
                                                                                                  ' color',
                                                                                            parent=self)[1]))

        rmenu.add_cascade(label='Highlight...', menu=hmenu, underline=0)

        # only show this if the hex view is showing
        if self._controller.hexViewShowing.get():
            rmenu.add_command(label='Show in Raw View',
                              command=lambda: self._controller.hexview_showpath(selected_path))

        # allowed to delete if the node isn't the root node
        if selected_path != '/':
            rmenu.add_command(label='Delete', command=lambda: self._controller.delete_item(selected_path))

        # not always allowed to edit (have to be non-node)
        if selected_item.is_property():
            rmenu.add_command(label='Edit...', command=lambda: self._controller.edit_item(selected_path))
        else:
            # item is node, so add various options to add child nodes/properties
            amenu = tk.Menu(rmenu, tearoff=0)
            amenu.add_command(label='Node', command=lambda: self._controller.add_node(selected_path))
            ctmenu = tk.Menu(amenu, tearoff=0)
            ctmenu.add_command(label='EMPTY', command=lambda: self._controller.add_property(selected_path,
                                                                                            dt.FdtPropertyType.EMPTY))
            ctmenu.add_command(label='BYTES', command=lambda: self._controller.add_property(selected_path,
                                                                                            dt.FdtPropertyType.BYTES))
            ctmenu.add_command(label='STRINGS', command=lambda: self._controller.add_property(selected_path,
                                                                                              dt.FdtPropertyType.
                                                                                              STRINGS))
            ctmenu.add_command(label='WORDS', command=lambda: self._controller.add_property(selected_path,
                                                                                            dt.FdtPropertyType.WORDS))
            amenu.add_cascade(label='Property of Type...', menu=ctmenu, underline=0)
            rmenu.add_cascade(label='Add New Child...', menu=amenu, underline=0)
            if selected_path != '/':
                rmenu.add_command(label='Copy Node', command=lambda: self._controller.copy_node(selected_path))

        # display the menu where the user right clicks
        rmenu.tk_popup(event.x_root, event.y_root)

    def expand_item(self, event):
        """Event handler for when the user double (left) clicks in the tree view

        This function handles the double-left-click event from Tkinter. If the double-clicked item is a node, no special
        code is run (the Ttk tree view automatically handles double click to expand a node). However, if the double-
        clicked item is a property, then the TreeView tells the controller to pop up an edit dialog at the given
        path.

        :param event: Tkinter event object containing information on the double click event
        """

        # determine corresponding item in tree
        selected_row, selected_path, selected_item = self._get_item_at_pos(event.y)
        if selected_path is not None and selected_item.is_property():
            # only allowed to edit non-nodes
            self._controller.edit_item(selected_path)

    def edit_item_popup_done(self, rid=None, path=None, item=None):
        """Callback for when inline editing has completed on a property in the tree view

        This function is called when the user finishes inline editing a property in the tree view. It fetches the result
        from the inline edit DtbSmartEntry, clears the state information stored in the TreeView class, and if there was
        a successful (modified) result, notifies the controller (through the edit_item_inline_cb() call) that an inline
        edit has occurred. The controller will then proceed to update the TreeView (and HexView) appropriately once the
        value change has passed through to the DTWrapper.

        :param rid: Row ID of the row that was edited inline
        :param path: Path to the item that was edited inline
        :param item: The DTWrapper object FdtItem that was edited (unused)
        """

        result = self.editPopup.result
        self.editPopup = None
        if rid is not None and result is not None:
            self.lastEditRow = rid
            self._controller.edit_item_inline_cb(path, result)

    def edit_item_popup(self, selected_row, selected_path, selected_item):
        """ Helper function to pop up a DtbSmartEntry (inline editing field) at a given row

        This function pops up a DtbSmartEntry (a regular Tkinter entry, but augmented in the sense that it can perform
        on-the-fly validation of the user's input) over top of a given row's value cell. It is one of the few examples
        where the TreeView communicates directly with other components, but it is necessary to do it this way because
        the controller may not be aware of the same coordinate system that the tree view uses.

        :param selected_row: The row to display the inline editing popup field over top of
        :param selected_path: The path corresponding to this row
        :param selected_item: The DTWrapper FdtItem object at the path
        :return: Whether a new editPopup has appeared successfully (True if yes, False if some error has prevented this
                 from occurring)
        """

        if selected_path is None or not selected_item.is_property():
            # only allowed to edit properties
            return False

        # get the bounding box (x,y coords and width+height) of the value cell of this row
        self.editPopupRow = selected_row
        r = self.tree.bbox(self.editPopupRow, '#3')
        if len(r) == 0:
            # if bbox returns 0, then the item is not visible
            return False

        # unpack r (the bounding box info returned by bbox)
        x, y, width, height = r

        # create a new DtbSmartEntry
        self.editPopup = DtbSmartEntry(self._controller, self.tree, width, self.edit_item_popup_done,
                                       self.edit_ipop_next, self.edit_ipop_prev)
        # note how we change the value we set the DtbSmartEntry to depending on whether we are viewing as hex or dec
        self.editPopup.set_value(selected_row, selected_path, selected_item, 'hex' if gf['viewAsHex'] else 'dec')
        # place the DtbSmart entry over top of the cell's bounding box that we determined earlier
        # note that we don't actually deal with the height because the font size is the same. if the font size was
        # different, we would also need to specify that.
        self.editPopup.place(x=x, y=y, width=width)

        return True

    def get_visible(self):
        """Helper function to get all of the currently visible(*) properties

        This function is called by the tab handlers to determine the next property to jump to when the user presses
        tab or shift+tab. It does a depth-first search of the tree to determine all of the nodes that are expanded,
        and adding all of the expanded node's child properties to a large list. If the expanded node has any child
        nodes, it will also search all of the child nodes to see if they are expanded, and if yes, do the same thing
        (add the child properties to the list, scan child nodes, etc.).

        (*) tkinter defines "visible" as (and has functions to return) solely the items currently on the user's screen
            (e.g. scrolling changes the visible items). However, the user generally expects that tab presses will take
            them through all expanded properties and not just currently visible ones. so, we want to return the items
            that are expanded but off the view of the screen for now. This function builds a list of visible nodes that
            fit that property.

        :return: An (in order from top to bottom of the tree view) list of all of the row ID's that are (1.) properties
        and (2.) currently visible (i.e., all of their parent nodes are expanded).
        """

        # start with searching the root node
        visible_parents = [self.tree.get_children()]
        # this list is the one keeping track of all of the visible properties and returning the results
        visible_props = []

        # we traverse the list in this strange way because we modify it during each iteration and thus don't want to
        # cause any strange behaviour because of that
        while len(visible_parents) > 0:
            # get the last item in the visible_parents list; doing so means we are effectively doing a depth-first
            # search, from the bottom of the tree to top (this is sort of different from a typical depth-first search
            # which normally goes from top to bottom)
            e = visible_parents.pop()

            if self.tree.item(e, 'values')[1] == 'Property':
                # properties are always visible if they're here
                visible_props.append(e)
            elif self.tree.item(e)['open']:
                # if not a property, it's a node, so it must be visible for us to add all of its children to the
                # visible parents list
                visible_parents.extend(self.tree.get_children(e))

        # because of the way that we did the search (bottom to top), we need to reverse the list here to get the order
        # we desire
        visible_props.reverse()
        return visible_props

    def edit_ipop_offset(self, offset=1):
        """Function to fetch the next item to edit and pop up the DtbSmartEntry in the appropriate row

        This function will fetch the currently visible properties, walk the devicetree to determine which order the
        properties should be in (unfortunately, because of tree view weirdness, there is not always a guarantee to the
        order that get_visible() returns if properties have been added later (e.g. deleted, then operation undone)),
        and pop up the DtbSmartEntry at a given offset away from the most recently edited row.

        :param offset: Offset from the current element to the next element to edit (i.e. 1 to edit the next item, -1 to
                       edit the previous item, and 0 to not change). If there was no previously edited item, then the
                       offset will be computed from the first visible property.
        """

        # get the visible elements (properties) first
        visible_elems = set(self.get_visible())
        curr_row = self.lastEditRow

        if len(visible_elems) == 0:
            # no elements visible, so do nothing
            return

        visible_sorted = []
        idx = 0
        # walk the entire tree
        for (path, item) in self._controller.dtw.resolve_path().walk():
            r = self.treeMappings[path]

            if r == curr_row:
                # we found the row we most recently edited in the tree, so keep track of which index we found it at
                idx = len(visible_sorted)
                if r not in visible_elems:
                    # only care about tabbing to edit visible properties
                    # however, we want to adjust the offset so we don't double-hop
                    if offset == 1:
                        offset -= 1
                    # elif offset == -1:
                    #     offset = 0
                    continue
            elif r not in visible_elems:
                # only care about tabbing to edit visible properties and this property isn't visible
                continue

            # path is visible, so add it to the sorted visible
            visible_sorted.append(r)

        # offset and wrap around
        idx = (idx + offset) % len(visible_elems)

        # now edit this element!
        # fetch existing row text
        row_text = self.tree.item(visible_sorted[idx], 'text')
        # modify the user's selection so they are now selecting the item that they are editing
        self.tree.selection_set((visible_sorted[idx],))
        # scroll to this item
        self.tree.see(visible_sorted[idx])

        # sometimes there are issues with the bounding box for the next element not appearing
        # until after the see() call if it wants to scroll too far, so we fix this by waiting a tick to let the program
        # actually scroll to have the item in view and get updated before popping up the inline edit DtbSmartEntry
        self._root.after(1, lambda: self.edit_item_popup(visible_sorted[idx], row_text,
                                                         self._controller.dtw.resolve_path(row_text)))

    def edit_ipop_next(self, _=None, default_same=False):
        """Callback to pop up inline editing DtbSmartEntry at the next editable line

        This function is called when the user pressed tab to tell edit_ipop_offset() to edit the next editable item in
        the tree view.

        :param _: ignored
        :param default_same: default to editing the same row, when possible
        """

        sel = self.tree.selection()
        if len(sel) == 0:
            # edit the first available element in the tree
            self.lastEditRow = self.tree.get_children()[0]
            self.edit_ipop_offset(0)
        else:
            # edit whatever element comes next (or the same element if default_same is True)
            self.lastEditRow = sel[0]
            self.edit_ipop_offset(0 if default_same else 1)

    def edit_ipop_prev(self, _=None, default_same=False):
        """Callback to pop up inline editing DtbSmartEntry at the previous editable item

        This function is called when the user pressed shift+tab to tell edit_ipop_offset() to edit the previous editable
        item in the tree view.

        :param _: ignored
        :param default_same: ignored
        """

        sel = self.tree.selection()
        if len(sel) == 0:
            # edit the first available element in the tree
            self.lastEditRow = self.tree.get_children()[0]
            self.edit_ipop_offset(0)
        else:
            # edit whatever element comes before
            self.lastEditRow = sel[0]
            self.edit_ipop_offset(-1)

    def tab_pressed(self, _=None):
        """Event handler for when shift+tab is pressed

        This is the event handler called when the user presses shift+tab in the *tree view* (as opposed to the
        DtbSmartEntry). This function will only be called if there is not currently a DtbSmartEntry open, so it will
        simply call edit_ipop_next to pop up the previously edited element again.

        :param _: ignored
        """

        # edit the next item, defaulting to the same element
        self.edit_ipop_next(default_same=True)

    def shifttab_pressed(self, _=None):
        """Event handler for when shift+tab is pressed

        This is the event handler called when the user presses shift+tab in the *tree view* (as opposed to the
        DtbSmartEntry). This function will only be called if there is not currently a DtbSmartEntry open, so it will
        simply call edit_ipop_next to pop up the previously edited element again.

        :param _: ignored
        """

        # edit the previous item, defaulting to the same element
        self.edit_ipop_prev(default_same=True)

    def on_click(self, event):
        """Single-click event handler to close inline edit popup or display a new one

        This function will close an existing inline edit popup window if the user clicks outside of the popup, and will
        pop up a new DtbSmartEntry if the user clicks on a row that they have previously selected.

        :param event: Tkinter mouse click event containing the coordinates of where the click occurred
        """

        # close the existing popup if we click anywhere outside of it (if we catch this event, we have clicked outside
        # of it - if we click inside the DtbSmartEntry, since it appears over top of us, we won't get the event)
        if self.editPopup is not None:
            self.editPopup.on_return()
            self.editPopup = None

        # figure out what column was clicked
        column = self.tree.identify_column(event.x)

        if column != '#3':
            # only the 3rd column (value) can be single-click edited
            return

        # it makes a little bit more sense if single-clicking the current row when it is already selected
        # will edit, and not always
        selected_row, selected_path, selected_item = self._get_item_at_pos(event.y)
        if selected_row in self.tree.selection():
            # only if we are clicking on a selected row do we give it to edit_item
            self.edit_item_popup(selected_row, selected_path, selected_item)

    def _setprop_all_children(self, row=None, **kwargs):
        """Internal helper function to set properties on all children of a given row

        This function is a commonly-used and powerful helper function that is able to set various properties on all of
        the children of a node in the tree. For example, it can be used to tag a specific node and all of its children
        (i.e., highlighting the node), or set the "open" property to True on all nodes in the tree (including the root
        node; i.e. expanding all nodes).

        :param row: The row whose children to modify. Defaults to None, which will set the properties on all of the
                    items/rows in the tree view.
        :param kwargs: The arguments passed to the tree.item() call.
        """

        children = [self.tree.get_children(row)]
        # similarly with other times when we modify the list as we iterate through it, we have to use a slighly stranger
        # way to loop here
        while len(children) > 0:
            itm = children.pop()
            for child in itm:
                # apply whatever to this row
                self.tree.item(child, **kwargs)

                # try to fetch all children of this row
                tmp = self.tree.get_children(child)
                if len(tmp) > 0:
                    # deal with the children later
                    children.append(tmp)

    def expand_all_items(self, _=None):
        """Expand all items in the tree view

        This function is a simple public wrapper around the internal _setprop_all_children() to set the "open" property
        of all items in the tree view to True, which has the effect of expanding all nodes.

        :param _: ignored
        """

        self._setprop_all_children(open=True)

    def collapse_all_items(self, _=None):
        """Collapse all items in the tree view

        This function is a simple public wrapper around the internal _setprop_all_children() to set the "open" property
        of all items in the tree view to False, which has the effect of collapsing all nodes.

        :param _: ignored
        """

        self._setprop_all_children(open=False)

    def window_resize(self, _=None):
        """Handler for window resize events

        This function handles window resize events. It updates the position of and resizes the inline edit popup
        DtbSmartEntry, if one is visible at the moment, to the new dimensions of the tree view container.

        :param _: ignored (sometimes it is the Tkinter window resize event callback)
        """

        # resize the edit popup, if applicable
        if self.editPopup is None:
            return

        # fetch the updated width
        r = self.tree.bbox(self.editPopupRow, '#3')
        if len(r) == 0:
            # if bbox returns 0, then the item is not visible. we could close the popup if we wanted, but I think it's
            # nicer to the user if we don't.
            return

        # unpack r
        x, y, width, height = r

        # update the positioning of the inline editing box
        self.editPopup.config(width=width)
        self.editPopup.place(x=x, y=y, width=width)

    def on_scroll(self, event):
        """Handler for mouse scroll events

        This function handles mouse scroll events. Ideally, it should update the position of the inline edit popup
        DtbSmartEntry when the user scrolls, but the code that does so right now seems buggy so it has been disabled.

        :param event: Tkinter mouse scroll event
        """

        # TODO: add handling for moving the editPopup when scrolling
        # # if self.editPopup is None:
        #     return
        #
        # # fetch the updated width
        # dtlogger.info(self.editPopupRow)
        # r = self.tree.bbox(self.editPopupRow, '#3')
        # if len(r) == 0:
        #     # if bbox returns 0, then the item is not visible anymore
        #     return
        #
        # # unpack r
        # x, y, width, height = r
        #
        # # update the positioning of the resize box
        # self.editPopup.config(width=width)
        # self.editPopup.place(x=x, y=y, width=width)
        self.update_last_column = True
        self.update_last_column_width()
        pass

    def show_path(self, path):
        """Display and focus a path in the tree view

        This function ensures that a given path is visible in the tree view and highlights and scrolls to it. It is used
        to draw the user's attention to the row e.g. when it has been modified by an undo/redo, or it contains the next
        occurrence of the user's search query.

        :param path: Path to highlight in the tree view
        :return: True if the path has been shown, or False if the path was not found in the tree view
        """

        if path not in self.treeMappings:
            # invalid requested path
            return False

        # get the element
        elem = self.treeMappings[path]
        # first expand everything to see it
        self.tree.see(elem)
        # then focus on it
        self.tree.focus(elem)
        # and select it
        self.tree.selection_set((elem,))

        # successfully showed the path
        return True

    def get_selection(self):
        """Get the current user selection in the tree view as a list of paths

        This function gets the user's current selection in the tree view as a list of paths. Normally, the return from
        the tree view selection() function is the row ID, but this function converts the result into DeviceTree paths.
        It is used by the find_next() function in the controller to determine where the user is currently selecting,
        in order to know which nodes to search next.

        :return: List of currently selected paths, the first item in the tree view if no item is currently selected,
                 or an empty array if no items are currently in the tree view.
        """

        selected_paths = []
        # get current user selection
        selected_rows = self.tree.selection()
        if len(selected_rows) == 0:
            # nothing is currently selected, so try to just return the first item in the tree view, i.e. search "from
            # the top"
            children = self.tree.get_children()
            if len(children) == 0:
                # there are currently no items in the tree view, so just return an empty list
                return []
            # just get the first item in the tree view
            selected_rows = [children[0]]
        else:
            # ??? why is this here
            self.lastEditRow = selected_rows[0]

        for row in selected_rows:
            # convert the row id to DeviceTree path
            selected_paths.append(self.tree.item(row, 'values')[0])
        return selected_paths
