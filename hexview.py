# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
@file hexview.py
@description Initialize all of the GUI elements of the DeviceTree hex viewer (raw view) window
@author Michael Turney, Mason Xiao

This file contains the code that controls and displays the raw (hex) view of the DeviceTree blob.

The code in this file is primarily taken up by the HexWindow class, which is the object-oriented class used to represent
a raw view window. Inside the class, there are functions to initilize the view, handle highlighting of specific paths,
and generate a hex dump from the raw DTB file. The main DTGUI controller (controller.py) has an instance of the
HexWindow class when there is a raw view window open and can call the highlighting and hex-dumping functions when
appropriate (i.e., when the user highlights a path in the tree view and when a modification has been made to the
DeviceTree that would change the DTB, respectively).
"""

# tkinter libraries
import tkinter as tk
import tkinter.scrolledtext
import tkinter.font


# group() / join() / hexdump() from: http://code.activestate.com/recipes/579064-hex-dump/
# original hexdump used print(), changed to use scrolledtext widget
def group(a, *ns):
    for n in ns:
        a = [a[i:i + n] for i in range(0, len(a), n)]
    return a


def join(a, *cs):
    return [cs[0].join(join(t, *cs[1:])) for t in a] if cs else a


# hex view window
class HexWindow(tk.Toplevel):
    data = None
    data_mapping = None

    def __init__(self, parent, controller, close_cb=None):
        # create a new window
        super().__init__(parent)

        # set title
        self.title('devicetree DTB viewer/editor : raw view')

        # set various variables
        self._parent = parent
        self._controller = controller
        self.close_cb = close_cb
        self.nosel = []

        # initialize ui components
        self._init_ui()

        # catch window close
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def _init_ui(self):
        # determine font size
        font = tk.font.nametofont('TkFixedFont')
        char_width = font.measure("w")
        win_width = char_width * 80 + 20  # for scrollbar
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        # window size is 660x120
        self.geometry('%dx120+%d+%d' % (win_width,(screenwidth-win_width)/2,(screenheight-120)/2))
        # minimum size is 660x20 (width cannot be decreased)
        self.minsize(win_width, 20)
        # so we can resize
        self.resizable(False, True)


        # the core of this window is a scrolled text view
        self.t = tk.scrolledtext.ScrolledText(self, font=font)
        self.update_view()
        # we disable the view so that the user cannot edit contents
        self.t.configure(state='disabled')
        self.t.pack(side='top', fill='both', expand=True)
        self.t.tag_config('sel', background='#000', foreground='#fff')
        # TODO: Add right click context menu to do something like 'expand in device tree' or 'highlight'
        # self.t.bind('<Button-1>', lambda _: self.t.focus_set())

    def on_close(self):
        # call the close callback before we close
        # (this is so that we can uncheck the checkbox next to "raw view" in the main window
        if self.close_cb is not None:
            self.close_cb()
        self.destroy()

    def range_to_textranges(self, start, end, highlight_bytes=True, highlight_text=True):
        # takes in a [start, end) range as a tuple
        # returns a tuple of two arrays, each with tuples of strings, representing the ranges that
        # need to be highlighted in order to highlight the given bytes
        # (first one corresponds to the left side of bytes, and the second item in the tuple corresponds to the right
        # side with the characters displayed)

        # input validation
        if self.data is None or start >= end or start >= len(self.data) or end > len(self.data) or start < 0 or end < 0:
            # invalid input
            return None, None

        # arrays to return
        hl_byte = []
        hl_text = []

        def hl_helper(dr_lcol, dr_rcol, bytes_per_row, cols_per_byte):
            ret = []
            # calculate the whole and fractional portions of a row
            start_row = start // bytes_per_row
            end_row = end // bytes_per_row

            # need to account for the extra space in the middle (at byte 8)
            start_col = (start % bytes_per_row)
            if start_col >= 8:
                # move over by 1 due to the padding in between bytes 8 and 9
                start_col = start_col * cols_per_byte + 1
            else:
                start_col = start_col * cols_per_byte

            # need to account for the extra space in the middle (at byte 8)
            end_col = (end % bytes_per_row)
            if end_col > 8:
                # move over by 1 due to the padding in between bytes 8 and 9
                end_col = end_col * cols_per_byte + 1
            elif cols_per_byte != 1 and end_col == 8:
                # if we end just at the 8th one, we might over-highlight the padding. avoid this.
                end_col = end_col * cols_per_byte - 1
            else:
                end_col = end_col * cols_per_byte

            # offset by the number of bytes taken up for padding & byte number, etc.
            start_col = start_col + dr_lcol
            end_col = end_col + dr_lcol

            # now we keep adding tuples until we are done
            current_row = start_row
            current_col = start_col
            while current_row < end_row:
                # add full rows
                ret.append(('%d.%d' % (current_row + 1, current_col), '%d.%d' % (current_row + 1, dr_rcol)))

                # reset values when we move down
                current_row += 1
                current_col = dr_lcol

            # we add the last one here
            ret.append(('%d.%d' % (current_row + 1, current_col), '%d.%d' % (end_row + 1, end_col)))

            return ret

        if highlight_bytes:
            # bytes starts at col 12 and ends at col 60, has 16 bytes per row, and every 3 columns = 1 byte
            hl_byte = hl_helper(12, 60, 16, 3)

        if highlight_text:
            # bytes starts at col 62 and ends at col 79, has 16 bytes per row, and every column = 1 byte
            hl_text = hl_helper(62, 79, 16, 1)

        return hl_byte, hl_text

    def _highlight_range(self, start, end, bg_color, fg_color='#fff', n=-1, highlight_bytes=True, highlight_text=True):
        if n == -1:
            n = len(self._controller.knownHighlights)
        tag_name = 'HL_%d_%d_%d' % (start, end, n)

        # call the helper function to get the ranges
        hl_byte, hl_text = self.range_to_textranges(start, end, highlight_bytes, highlight_text)
        if hl_byte is None or hl_text is None:
            # invalid input somehow
            return

        # iterate through all of the ranges
        hls = hl_byte + hl_text
        for hl in hls:
            # and add the tag for each one
            self.t.tag_add(tag_name, *hl)

        # configure the color
        self.t.tag_config(tag_name, background=bg_color, foreground=fg_color)

        # reset the selection priority
        self.t.tag_raise('sel')
        self.t.tag_raise('nosel')

    def highlight(self, path, bg_color, fg_color, nbr=-1):
        # callback for the controller to highlight something
        if path not in self.data_mapping:
            # print('Could not highlight in HexView; mapping not found for %s' % path)
            return False

        # the way mappings are stored are path -> (start byte, end byte) so we unpack it here
        hls, hle = self.data_mapping[path]
        self._highlight_range(hls, hle, bg_color, fg_color, n=nbr)

        # also, scroll to this highlight in the view
        self.show_path(path)
        return True

    def update_highlights(self):
        # clear old highlights
        for tag in self.t.tag_names():
            self.t.tag_delete(tag)

        # block selection in the side bar area
        for itm in self.nosel:
            self.t.tag_add('nosel', *itm)
        self.t.tag_config('nosel', background='#FFF', foreground='#000')

        # update from controller
        for idx, highlight in enumerate(self._controller.knownHighlights):
            self.highlight(*highlight, nbr=idx)

    def show_path(self, path):
        if path not in self.data_mapping:
            print('Could not scroll to path; mapping not found for %s' % path)
            return False

        start, end = self.data_mapping[path]

        # start is in bytes, we want to convert it to rows... easy fix, divide by 16!
        row = start // 16

        # scroll to the corresponding row (add 1 because rows start at 1)
        self.t.see('%d.0' % (row+1))

        return True

    def update_view(self):
        if self._controller.dtw is None:
            # no point updating if there is no file open
            return

        # fetch the dtb & mappings again
        self.data = self._controller.dtw.dtb
        self.data_mapping = self._controller.dtw.dtb_mappings

        # save the current position in the textbox
        current_pos = self.t.yview()

        # need to enable the textbox in order for updates to appear
        self.t.configure(state='normal')
        # clear old data
        self.t.delete('1.0', tk.END)

        # check if a file is open
        if self.data is None:
            # disable the field again and we're done since no file is open
            self.t.configure(state='disabled')
            return

        # perform the hexdump - code from from: http://code.activestate.com/recipes/579064-hex-dump/
        make = lambda f, *msep: join(group(list(map(f, self.data)), 8, 2), *msep)
        hs = make(lambda d: '{:02X}'.format(d), '  ', ' ')
        cs = make(lambda d: chr(d) if 32 <= d < 127 else '.', ' ', '')
        dd = 0
        self.nosel = []
        for i, (h, c) in enumerate(zip(hs, cs)):
            hexline = '{:010X}: {:48}  {:16}\n'.format(i * 16, h, c)
            self.t.insert(tk.INSERT, hexline)
            self.nosel.append(('%d.0' % (i+1), '%d.12' % (i+1)))
            dd += 16
        self.t.insert(tk.END, '')

        # restore all known highlights
        self.update_highlights()

        # scroll back to the original position
        self.t.yview_moveto(current_pos[0])

        # re-disable the textbox to prevent user changes, etc.
        self.t.configure(state='disabled')
