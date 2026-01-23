# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
@file findview.py
This file contains a helper window class called FindWindow that talks with the DTGUIController to get user options for
finding a given string in the DeviceTree. Note that all of the actual finding logic is in the controller and that this
file simply collects that information and passes it on to the controller as appropriate.
"""

# tkinter library
import tkinter as tk


class FindWindow(tk.Toplevel):
    """Main class for the find window

    Note that this is one of the few classes that intentionally uses class variables (as opposed to instance variables),
    since we want the user's find options to persist across different appearances of this window in a single launch of
    the program (i.e. if the user checks "search names" to yes and closes the find window, it should still be checked
    yes if the user reopens the find window).

    This class is a child of the tk.Toplevel class, which means that it should appear as its own separate window.
    """

    e1 = None
    searchNames = None
    searchValues = None
    matchCase = None
    findStr = None

    def __init__(self, parent, controller, find_next_cb, close_cb):
        """Initialize the FindWindow

        This function initializes the FindWindow and all of the variables associated with it, then calls the _init_ui()
        function to initialize the UI components.

        :param parent: Root tk.Tk() object
        :param controller: Reference to the main DTGUIController
        :param find_next_cb: Function to call when the user presses the "find next" button. This function will be called
                             with a single object argument containing the "options" for the search.
        :param close_cb: Function to call when the user cancels or closes the find window.
        """

        # create a new window
        super().__init__(parent)

        # set title
        self.title('Find')

        # set various variables
        self.parent = parent
        self.controller = controller
        self.find_next_cb = find_next_cb
        self.close_cb = close_cb
        
        # set default configuration if it is not yet set up (note the static access here)
        if FindWindow.searchNames is None:
            FindWindow.searchNames = tk.BooleanVar()
            FindWindow.searchNames.set(True)
        if FindWindow.searchValues is None:
            FindWindow.searchValues = tk.BooleanVar()
            FindWindow.searchValues.set(False)
        if FindWindow.matchCase is None:
            FindWindow.matchCase = tk.BooleanVar()
            FindWindow.matchCase.set(True)
        if FindWindow.findStr is None:
            FindWindow.findStr = tk.StringVar()
            FindWindow.findStr.set('')

        # initialize ui components
        self._init_ui()

        # catch close
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        # focus self
        self.after(1, lambda: self.focus_force())

    def _init_ui(self):
        """Initialize UI components of the FindWindow

        This function sets up the components in the FindWindow. The main layout is a grid of two columns and 3 rows.
        The first row's columns are the label and input for the text to search. The second row's columns are the label
        for the options and a packed frame containing three checkboxes for the user to change the options of the search.
        The final row's columns are two buttons, the first being to cancel the find and the other being to find the next
        result. Pressing the cancel button or pressing the "X" on the window frame will close the dialog. Pressing
        enter in the main text entry has the same effect as pressing the "find next" button (tell the find next callback
        to find the next item).
        """

        # window minimum size is 470x60
        self.minsize(470, 60)
        # we can resize the width but not the height
        self.resizable(True, False)
        

        # labels with information (left side)
        tk.Label(self, text='Find what : ', justify='left', width=20, borderwidth=2,
                 relief='groove').grid(row=0)
        tk.Label(self, text='Options   : ', justify='left', width=20, borderwidth=2,
                 relief='groove').grid(row=1)

        # text entry for the actual string to find
        self.e1 = tk.Entry(self, justify='left', width=50, textvariable=FindWindow.findStr)
        self.e1.grid(row=0, column=1, sticky='nesw')
        self.e1.focus()

        # Options for the find
        f = tk.Frame(self)
        tk.Checkbutton(f, text='Search in Names', variable=FindWindow.searchNames).pack(side=tk.LEFT, anchor=tk.W,
                                                                                        expand=tk.YES)
        tk.Checkbutton(f, text='Search in Values', variable=FindWindow.searchValues).pack(side=tk.LEFT, anchor=tk.W,
                                                                                          expand=tk.YES)
        tk.Checkbutton(f, text='Match Case', variable=FindWindow.matchCase).pack(side=tk.LEFT, anchor=tk.W,
                                                                                 expand=tk.YES)
        f.grid(row=1, column=1, sticky='nesw')

        # buttons to find next/cancel
        tk.Button(self, text='Cancel', justify='right', width=20, command=self.on_close).grid(row=2)
        tk.Button(self, text='Find Next', justify='right', width=40, command=self.find_next).grid(row=2, column=1,
                                                                                                  sticky='nesw')

        # expand to fill
        tk.Grid.columnconfigure(self, 1, weight=1)

        # key binding enter press = save
        self.bind('<Return>', self.find_next)

    def find_next(self, _=None):
        """Callback to find the next item in the DeviceTree

        This function is called when the user presses the "find next" button in the UI. It gathers all of the search
        options that the user has configured (including the query itself) and passes that information on to the
        DTGUIController through the find next callback; the DTGUIController is what actually does the "finding".

        :param _: ignored
        """

        # get a list of all of the options
        opts = {
            'str': FindWindow.findStr.get(),
            'searchNames': FindWindow.searchNames.get(),
            'searchValues': FindWindow.searchValues.get(),
            'matchCase': FindWindow.matchCase.get()
        }
        self.find_next_cb(opts)
        pass

    def on_close(self):
        """Handler for when the Find window is closed

        This function is called when the Find window is closed or when the user presses the cancel button in the window.
        It calls the close callback function to notify the controller that the window has closed and then destroys the
        window itself.
        """

        # call the close callback before we close
        if self.close_cb is not None:
            self.close_cb()
        self.destroy()
