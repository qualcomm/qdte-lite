# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

from optparse import OptionParser
from tkFileDialog import askopenfilename
import tkFileDialog as filedialog
import os
import sys
import shutil
from shutil import copyfile
import ntpath
import elf_gen_tools
import elf_gen
from elf_gen import *
from Tkinter import *
from functools import partial
from elf_gen_tools import *
import tkMessageBox
import subprocess
import ConfigParser 
import json
import collections
from pprint import pprint

init_help_msg = 'Enter an input file to use the GUI. \n\nPress Quit to exit the program'
start_msg = 'This tool can be used to create, modify, and disintegrate ELF files \n\nTo continue with the tool, press Continue \n\nTo exit the tool, press Quit\n'
modify_help_msg = 'Press Modify ELF to modify an ELF file \n \nPress Disintegrate ELF to create binaries for headers and segments of the specified ELF file \n \nPress Create Elf to create a new ELF file from binaries \n'
disintegrate_help_msg = 'Change file by typing filename into textbox and pressing Input File \n\nPress Disintegrate to parse headers and segments. Binaries will be saved in drectory elf_files \n\nPress Quit to exit \n'
pflag_info = "This flag is a 3 bit number \n\n0x1 is value for 'execute'\n0x2 is value for 'write\n0x4 is value for 'read'\n\nThe sum of the bits is used as the p-flag value"
access_flag_info = "This flag is a 3 bit number \n\n0x0 = Read-Write=0\n0x1 = Read Only = 1\n0x2 = Reserved Zero Initialized\n0x3 = Not Used Segment\n0x4 = Shared Segment\n0x5, 0x6, 0x7 = Reserved"
segment_flag_info = "This flag is a 3 bit number\n\n0x0 = Kernel Segment\n0x1 = Normal (AMSS) Segment\n0x2 = Hash Segment\n0x3 = Boot Segment\n0x4 = Demand Paging BSP Segment\n0x5 = Demand Paging: Swapped Segment\n0x6 = Demand Paging: Swap Pool Segment\n0x7 = Not Used"

# Add path to elf_gen_tools
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                'sectools','sectools','features','isc','parsegen'))

#Class definitions
class fileStruct:
   def __init__(self, frame):
      self.input_file = Entry(frame)
      self.output_file = Entry(frame)

class entryStruct:
   def __init__(self, frame):
      self.entry_addr = Entry(frame)
      self.segalign = Entry(frame)

#********************* INITIALIZE GUI ***************************
#create the window
root = Tk()
for i in range (0, 12):
  root.rowconfigure(i, weight=1)
  root.columnconfigure(i, weight=1)
#modify window
root.title("ELF Generator")
root.geometry("1575x700")
root.grid()

frame_start = Frame(root, width=50, height=50)
frame2 = Frame(root)

rb_var1 = IntVar() #radiobutton variables - need to be global b/c of radiobutton bug (mouse hover)
rb_var2 = IntVar() 
      
#####################################################################################
# quit - Closes GUI
#####################################################################################
def quit():

  print "\n************** Program Ended **************\n" #needed here 
  exit()
  return

#####################################################################################
# load_directory - Loads directory path into the 'Output Path' field in GUI 
#####################################################################################
def load_directory(file_struct, grey_grid, seg_num, frame):
  directory = filedialog.askdirectory()
  file_struct.output_file.delete(0, 'end') 
  file_struct.output_file.insert(0, directory)
  print directory

  #If called by 'grey_grid', load 'path' entries with new output path
  if(grey_grid):
    for i in range (seg_num):
      e1 = Entry(frame)
      e1.insert(0, file_struct.output_file.get())
      e1.configure(state='readonly')
      e1.grid(row=i+6+1, column=11)

  return

#####################################################################################
# load_file - not used? Changes 'input_file' in file_struct variable to disintegrate
#####################################################################################
def load_file(file_struct, frame):
  new_file = filedialog.askopenfilename(filetypes =( ("All files", "*.*"), ("Binary", "*.bin"), ("Elf", "*.elf") ))
  if not os.path.isfile(new_file):
    return
  else:
    file_struct.input_file.delete(0, 'end')  #These lines not needed, since only the new file is passed back and not the file structure
    file_struct.input_file.insert(0, new_file)
    # new_file = ntpath.basename(file_struct.input_file.get())
    #Recreate Grid
    frame.grid_forget()    
    frame2 = Frame(root)
    frame2.grid(row=0, column=0)
    root.geometry("1570x700") #used to make smaller window larger after file input is given in GUI when script is called with no file argument
    call_gui(new_file, frame2)
    return

###################################################################################
# load_file_grey_grid - Calls 'grey_grid' with the newly specified input file. 
#                       Arguments are passed to preserve values from function that
#                       originally called 'grey_grid'
###################################################################################
def load_file_grey_grid (original_offset_list, frame2, val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, seg_added, seg_deleted, add_entry_list, add_val_list, file_struct, entry_struct, canvas, load_file_struct, seg_struct, initial_phdr_struct, phdr_struct):
  new_file = filedialog.askopenfilename(filetypes =( ("All files", "*.*"), ("Binary", "*.bin"), ("Elf", "*.elf") ))
  if not os.path.isfile(new_file):
    return
  else:
    load_file_struct.input_file.delete(0, 'end')  
    load_file_struct.input_file.insert(0, new_file)
    # new_file = ntpath.basename(file_struct.input_file.get())
    #Recreate Grid

    grey_grid(original_offset_list, frame2, val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, seg_added, seg_deleted, add_entry_list, add_val_list, file_struct, entry_struct, canvas, load_file_struct, seg_struct, initial_phdr_struct, phdr_struct)
  return

##############################################################################
# pop_up - Creates pop-up window with a message
##############################################################################
def pop_up(message):
  top = Toplevel()
  # top.geometry("300x200")
  top.title("Pop Up")

  msg = Message(top, text=message)
  msg.pack()

  button = Button(top, text="Dismiss", command=top.destroy)
  button.pack()
  return

##############################################################################
# pop_up_start - Opens pop-up window for 'help' button on initial tool window
##############################################################################
def pop_up_start(message):
  top = Toplevel()
  top.geometry("180x160")
  top.title("Help")

  msg = Message(top, text=message)
  msg.pack()

  button = Button(top, text="Dismiss", command=top.destroy)
  button.pack()
  return

##############################################################################
# pop_up_overlap - Opens pop-up window with address overlap error message
##############################################################################
def pop_up_overlap(message, seg1, seg2):
  top = Toplevel()
  top.title("Error")

  msg1 = Message(top, text=message)
  msg2 = Message(top, text=seg1)
  msg3 = Message(top, text=seg2)
  msg1.pack()
  msg2.pack()
  msg3.pack()

  button = Button(top, text="Dismiss", command=top.destroy)
  button.pack()
  return

##############################################################################
# raise_frame - Creates GUI with standard sized window, since input file
#               given to 'create_frame_start'
##############################################################################
def raise_frame(frame_new):
  frame2.grid_forget()
  frame_start.destroy()
  root.geometry("1570x700")
  frame_new.grid(row=0, column=0)
  return

###############################################################################
# raise_frame_start - Creates GUI window with smaller size, since no input file 
#                     given to 'create_frame_start'
###############################################################################
def raise_frame_start(frame_new):
  frame2.grid_forget()
  frame_start.destroy()
  root.geometry("1570x200")
  frame_new.grid(row=0, column=0)
  return

#####################################################################################################
# create_frame_start - Creates first (smaller) window. Argument determines whether an ELF file will
#                      automatically be loaded into GUI after 'continue' is pressed
#####################################################################################################
def create_frame_start(file_arg):
  root.geometry("400x300")
  Label(frame_start, text='ELF GENERATION TOOL (Qualcomm Copyright-2016)', height=8).pack()
  Label(frame_start, text='Please Make Sure the Following is Installed :', height=2).pack()
  # Label(frame_start, text='OS : Windows 7', width=30).pack()
  Label(frame_start, text='Python 2.7 or Higher', width=40).pack()
  
  if not file_arg:  #If file is given, make second frame full size - else make it smaller since no input given
    button_frame_cont = Button(frame_start, text = "Continue", command=lambda: raise_frame_start(frame2))
  else:
    button_frame_cont = Button(frame_start, text = "Continue", command=lambda: raise_frame(frame2))
  button_frame_cont.place(relx=.37, rely=.8, anchor="c")
  button_help = Button(frame_start, text = "Help", command=lambda: pop_up_start(start_msg))
  button_help.place(relx=.5, rely=.8, anchor="c")
  button_frame_quit = Button(frame_start, text = "Quit", command=lambda: quit())
  button_frame_quit.place(relx=.6, rely=.8, anchor="c")

  return

##############################################################################
# roundup - returns offset 'x' with aligment 'precision'
##############################################################################
def roundup(x, precision):
  if precision == 0:
    return x
  else:
    return x if x % precision == 0 else (x + precision - (x % precision)) 

##############################################################################
# scrollFunction - Used to enable scrollbar
##############################################################################
def scrollFunction(event, canvas):
    canvas.configure(scrollregion=canvas.bbox("all"),width=1570,height=700)
    return

#####################################################################################
# elf_error - Prints basic error message when error in GUI
#####################################################################################
def elf_error():
  print "\nFile NOT Created Due To Errors\n"
  return

#************************************************************* GUI CODE ****************************************************************************

###########################################################################################
# init_gui - Wait for an input file and initialize GUI with labels. Window will be smaller
###########################################################################################
def init_gui(frame):

  #Input/Output file code
  file_struct_new = fileStruct(frame2)
  file_struct_new.input_file.grid(row=1, column=1, columnspan=3, sticky='WE')
  button_input_file = Button(frame2, text = "Input File", command= partial(load_file, file_struct_new, frame2)) 
  button_input_file.grid(row=1, column=0)

  file_struct_new.output_file.grid(row=1, column=5, columnspan=3, sticky='WE')
  button_input_file = Button(frame2, text = "Output Path", state='disabled') 
  button_input_file.grid(row=1, column=4)

  #ELF HEADER CODE
  Label(frame2, text = "ELF Header").grid(row=0+2+1, column=0)    #Create labels for ELF header entries
  Label(frame2, text = "Class").grid(row=0+2+1, column=1)
  Label(frame2, text = "Type").grid(row=0+2+1, column=2)
  Label(frame2, text = "Entry Addr").grid(row=0+2+1, column=3)
  Label(frame2, text = "PH Start").grid(row=0+2+1, column=4)
  Label(frame2, text = "Segment Start").grid(row=0+2+1, column=5)
  Label(frame2, text = "ELF Header Size (bytes)").grid(row=0+2+1, column=6)
  Label(frame2, text = "PH Size (bytes)").grid(row=0+2+1, column=7)
  Label(frame2, text = "PH Num").grid(row=0+2+1, column=8)
  Label(frame2, text = "Section Header Offset").grid(row=0+2+1, column=9)
  Label(frame2, text = "SH Table Size").grid(row=0+2+1, column=10)
  Label(frame2, text = "Version").grid(row=0+2+1, column=11)

  #Labels for PHDR entries
  Label(frame2, text = "PHDR Entries").grid(row=2+1+2+2, column=0)
  Label(frame2, text = "Type").grid(row=2+1+2+2, column=1)
  Label(frame2, text = "Segment Offset").grid(row=2+1+2+2, column=2)
  Label(frame2, text = "Virt Addr").grid(row=2+1+2+2, column=3)
  Label(frame2, text = "Phys Addr").grid(row=2+1+2+2, column=4)
  Label(frame2, text = "File Size").grid(row=2+1+2+2, column=5)
  Label(frame2, text = "Mem Size").grid(row=2+1+2+2, column=6)
  Label(frame2, text = "Flags (RWE)").grid(row=2+1+2+2, column=8)
  Label(frame2, text = "Access Type").grid(row=2+1+2+2, column=9)
  Label(frame2, text = "Segment Type").grid(row=2+1+2+2, column=10)
  Label(frame2, text = "Address Alignment").grid(row=2+1+2+2, column=7)
  Label(frame2, text = "Path for Binary").grid(row=2+1+2+2, column=11)

  #RADIO BUTTONS
  rb_var1.set(1)    #default is 'modify ELF'
  rb_var2.set(1)    #default is 'Qualcomm ELF'
  rb1 = Radiobutton(frame2, text="Modify ELF", variable=rb_var1, value=1).grid(row=0, column=0)

  #LINE CODE - between radiobuttons and ELF header segment
  canvas_a = Canvas(frame2, width=1500, height=10)      #horizontal line above phdr
  canvas_a.grid(row=4+1, column=0, columnspan=12)
  canvas_a.create_line(20, 8, 1550, 8, width=1, dash=(4)) 
  canvas_b = Canvas(frame2, width=1500, height=10)      #horizontal line above elf header
  canvas_b.grid(row=2, column=0, columnspan=12)
  canvas_b.create_line(20, 8, 1550, 8, width=1, dash=(4))
  canvas_c = Canvas(frame2, width=1500, height=10)      #horizontal line under phdr
  canvas_c.grid(row=9, column=0, columnspan=12)
  canvas_c.create_line(20, 8, 1550, 8, width=1, dash=(4))

  #Create 'generate' button
  button_generate = Button(frame2, text = "Generate", width=16, state='disabled')
  button_generate.grid(row=0, column=9)
  # button_generate.grid(row=elf_header1.e_phnum+10, column=0)

  #Create 'help' button
  button_generate = Button(frame2, text = "Help", width=16, command=lambda: pop_up(init_help_msg))
  button_generate.grid(row=0, column=10)
 
  #Create 'quit' button
  button_generate = Button(frame2, text = "Quit", width=16, command=lambda: quit()) #disintegrates original ELF
  button_generate.grid(row=0, column=11) 
  root.mainloop()

  return

##################################################################################################
# call_gui - Iniitalizes GUI with data from input ELF file. Called every time new file is chosen
##################################################################################################
def call_gui(elf_in_file_name1, frame1):
  # root.geometry("1570x700")

  #Scrollbar initialization
  canvas=Canvas(frame1, borderwidth=0, width=1570, height=700)
  frame2=Frame(canvas, width=1570, height=700)
  myscrollbar=Scrollbar(frame1,orient="vertical",command=canvas.yview)
  canvas.configure(yscrollcommand=myscrollbar.set)

  myscrollbar.pack(side="right",fill="y")
  canvas.pack(side="left")
  canvas.create_window((0,0),window=frame2,anchor='nw')
  frame2.bind("<Configure>",lambda event, arg=canvas: scrollFunction(event, arg))

  #Input/Output file code
  file_struct_new = fileStruct(frame2)
  file_struct_new.input_file.insert(0, elf_in_file_name1)
  file_struct_new.input_file.grid(row=1, column=1, columnspan=3, sticky='WE')
  button_input_file = Button(frame2, text = "Input File", command= partial(load_file, file_struct_new, frame2)) #, command=lambda: call_gui(file_struct_new.input_file.get(), is_elf1_64_bit))
  button_input_file.grid(row=1, column=0)

  file_struct_new.output_file.grid(row=1, column=5, columnspan=3, sticky='WE')
  file_struct_new.output_file.insert(0, os.getcwd())
  button_input_file = Button(frame2, text = "Output Path", command= partial(load_directory, file_struct_new, False, 0, frame2)) #, command=lambda: call_gui(file_struct_new.input_file.get(), is_elf1_64_bit))
  button_input_file.grid(row=1, column=4)


  [elf_header1, phdr_table1] = \
    elf_gen_tools.preprocess_elf_file(elf_in_file_name1) #creates headers

  elf_in_fp1 = elf_gen_tools.OPEN(elf_in_file_name1, "rb")  #input elf file pointer

  #Decode header to find class
  if elf_header1.e_ident[ELFINFO_CLASS_INDEX] == '\x01': #PUT INTO GREYGRID TOO
    is_out_elf_64_bit = False #32 bits
  elif elf_header1.e_ident[ELFINFO_CLASS_INDEX] == '\x02':
    is_out_elf_64_bit = True
  else:
    is_out_elf_64_bit = True
    pop_up('Invalid class for ELF File')
    return

  #populate GUI with PHDR data
  val_list = []
  add_entry_list = []
  add_val_list = []
  check_list = []
  original_offset_list = []
  entry_struct_new = entryStruct(frame2)
  blank_file_struct = fileStruct(frame2)
  seg_struct = segInfoStruct()
  phdr_struct = phdrStruct()
  initial_phdr_struct = phdrStruct()

  #ELF HEADER CODE
  Label(frame2, text = "ELF Header").grid(row=1+2+1, column=0)    #Create labels for ELF header entries
  Label(frame2, text = "Class").grid(row=0+2+1, column=1)
  Label(frame2, text = "Type").grid(row=0+2+1, column=2)
  Label(frame2, text = "Entry Addr").grid(row=0+2+1, column=3)
  Label(frame2, text = "PH Start").grid(row=0+2+1, column=4)
  Label(frame2, text = "Segment Start").grid(row=0+2+1, column=5)
  Label(frame2, text = "ELF Header Size (bytes)").grid(row=0+2+1, column=6)
  Label(frame2, text = "PH Size (bytes)").grid(row=0+2+1, column=7)
  Label(frame2, text = "PH Num").grid(row=0+2+1, column=8)
  Label(frame2, text = "Section Header Offset").grid(row=0+2+1, column=9)
  Label(frame2, text = "SH Table Size").grid(row=0+2+1, column=10)
  Label(frame2, text = "Version").grid(row=0+2+1, column=11)

  #Create entries for elf_header1
  e_class = Entry(frame2)
  e_type = Entry(frame2)
  # e_entryaddr = Entry(frame2)
  e_phdrstart = Entry(frame2)
  e_segstart = Entry(frame2)
  e_headersize = Entry(frame2)
  e_phsize = Entry(frame2)
  e_phnum = Entry(frame2)
  e_data = Entry(frame2) 
  e_flags = Entry(frame2)
  e_secoff = Entry(frame2)
  e_secsize = Entry(frame2)
  e_version = Entry(frame2)

  #Decode header type
  if elf_header1.e_type == 0 :
    etype = "None"
  elif elf_header1.e_type == 1 :
    etype = "Rel"
  elif elf_header1.e_type == 2 :
    etype = "Exec"
  elif elf_header1.e_type == 3 :
    etype = "Dyn"
  elif elf_header1.e_type == 4 :
    etype = "Core"
  elif elf_header1.e_type == 0xff00 :
    etype = "Loproc"
  elif elf_header1.e_type == 0xffff :
    etype = "Hiproc"
  else :
    etype = "Undefined"
  #Decode bit type
  if is_out_elf_64_bit :
    eclass = "ELF_64"
  else :
    eclass = "ELF_32"
  #Decode version  
  if(elf_header1.e_version == 0x1):
    version_var = 'Current'
  else:
    version_var = 'Invalid'

  #Insert ELF header values into entries ***************
  e_class.insert(0, eclass)
  e_type.insert(0, etype)
  entry_struct_new.entry_addr.insert(0, hex(elf_header1.e_entry))
  # e_entryaddr.insert(0, hex(elf_header1.e_entry)) #used in entryStruct now
  e_phdrstart.insert(0, hex(elf_header1.e_phoff))
  seg_start = roundup(elf_header1.e_phoff + elf_header1.e_phentsize*elf_header1.e_phnum, PAGE_SIZE) #aligned with 4096 page size
  e_segstart.insert(0, hex(seg_start))
  e_headersize.insert(0, hex(elf_header1.e_ehsize))
  e_phsize.insert(0, hex(elf_header1.e_phentsize*elf_header1.e_phnum))
  e_phnum.insert(0, hex(elf_header1.e_phnum))
  e_secoff.insert(0, hex(elf_header1.e_shoff)) 
  e_secsize.insert(0, hex(elf_header1.e_shentsize*elf_header1.e_shnum))
  e_version.insert(0, version_var)

  e_class.configure(state='readonly')
  e_type.configure(state='readonly')
  # e_entryaddr.configure(state='readonly') #editable
  e_phdrstart.configure(state='readonly')
  e_segstart.configure(state='readonly')
  e_headersize.configure(state='readonly')
  e_phsize.configure(state='readonly')
  e_phnum.configure(state='readonly')
  e_secoff.configure(state='readonly')
  e_secsize.configure(state='readonly')
  e_version.configure(state='readonly')

  #Insert ELF header entries into GUI
  e_class.grid(row=1+2+1, column=1)
  e_type.grid(row=1+2+1, column=2)
  entry_struct_new.entry_addr.grid(row=1+2+1, column=3)
  # e_entryaddr.grid(row=1+2+1, column=3)
  e_phdrstart.grid(row=1+2+1, column=4)
  e_segstart.grid(row=1+2+1, column=5)
  e_headersize.grid(row=1+2+1, column=6)
  e_phsize.grid(row=1+2+1, column=7)
  e_phnum.grid(row=1+2+1, column=8)
  e_secoff.grid(row=1+2+1, column=9)
  e_secsize.grid(row=1+2+1, column=10)
  e_version.grid(row=1+2+1, column=11)


  #'EXTRA SEGMENT' CODE
  #Labels for additional segment entry
  Label(frame2, text = "New Segment").grid(row=elf_header1.e_phnum+8, column=0)

  entvar=StringVar()
  #Create list for new entries (typed in)
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())
  add_val_list.append(StringVar())

  #Create list for current entries
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[0]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[1]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[2]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[3]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[4]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[5]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[6]))
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[7])) 
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[8])) 
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[9])) 
  add_entry_list.append(Entry(frame2, textvariable=add_val_list[10]))

  #insert list into grid
  add_entry_list[0].grid(row=elf_header1.e_phnum+2+2+2+2, column=1)
  add_entry_list[1].grid(row=elf_header1.e_phnum+2+2+2+2, column=2)
  add_entry_list[2].grid(row=elf_header1.e_phnum+2+2+2+2, column=3)
  add_entry_list[3].grid(row=elf_header1.e_phnum+2+2+2+2, column=4)
  add_entry_list[4].grid(row=elf_header1.e_phnum+2+2+2+2, column=5)
  add_entry_list[5].grid(row=elf_header1.e_phnum+2+2+2+2, column=6)
  add_entry_list[6].grid(row=elf_header1.e_phnum+2+2+2+2, column=7)
  add_entry_list[7].grid(row=elf_header1.e_phnum+2+2+2+2, column=8)
  add_entry_list[8].grid(row=elf_header1.e_phnum+2+2+2+2, column=9)
  add_entry_list[9].grid(row=elf_header1.e_phnum+2+2+2+2, column=10)
  add_entry_list[10].grid(row=elf_header1.e_phnum+2+2+2+2, column=11)


  #'PROGRAM HEADER TABLE' CODE
  #Segment alignment entry update
  entry_struct_new.segalign.insert(0, hex(4096))
  entry_struct_new.segalign.grid(row=2+1+2+1, column=1)
  Label(frame2, text = "Offset Alignment(nbytes)").grid(row=2+1+2+1, column=0) 
  #Labels for PHDR entries
  Label(frame2, text = "PHDR Entries").grid(row=2+1+2+2, column=0)
  Label(frame2, text = "Type").grid(row=2+1+2+2, column=1)
  Label(frame2, text = "Segment Offset").grid(row=2+1+2+2, column=2)
  Label(frame2, text = "Virt Addr").grid(row=2+1+2+2, column=3)
  Label(frame2, text = "Phys Addr").grid(row=2+1+2+2, column=4)
  Label(frame2, text = "File Size").grid(row=2+1+2+2, column=5)
  Label(frame2, text = "Mem Size").grid(row=2+1+2+2, column=6)
  # Label(frame2, text = "Flag (R)").grid(row=2+1+2+1, column=7)
  # Label(frame2, text = "Flag (W)").grid(row=2+1+2+1, column=8)
  # Label(frame2, text = "Flag (E)").grid(row=2+1+2+1, column=9)
  Label(frame2, text = "Address Alignment").grid(row=2+1+2+2, column=7)
  Label(frame2, text = "Path for Binary").grid(row=2+1+2+2, column=11)
  #FLAG LABELS ARE NOW BUTTONS THAT DISPLAY FLAG INFO WHEN PRESSED
  button_generate = Button(frame2, text = "Flags (RWE)", command=partial(pop_up, pflag_info))
  button_generate.grid(row=2+1+2+2, column=8)
  button_generate = Button(frame2, text = "Access Type", command=partial(pop_up, access_flag_info))
  button_generate.grid(row=2+1+2+2, column=9)
  button_generate = Button(frame2, text = "Segment Type", command=partial(pop_up, segment_flag_info))
  button_generate.grid(row=2+1+2+2, column=10)

  #DELETED CODE FOR INFO DISPLAYED WHEN MOUSE HOOVERED OVER LABEL (now button)
  # label_pflags = Label(frame2, text="Pflag Bits (RWE)")
  # label_pflags.bind("<Enter>", partial(pflag_info, label_pflags))
  # label_pflags.grid(row=2+1+2+1, column=7)

  #Create grid entries
  for i in range(elf_header1.e_phnum):
    Label(frame2, text = "Segment "+ str(i)).grid(row=i+2+1+1+2+2)

    entvar=StringVar() #doesn't need to be in loop?
    #Create list for new entries (typed in)
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())

    #Create structure for current entries
    phdr_struct.s_type.append(Entry(frame2, textvariable=val_list[i*11]))
    phdr_struct.offset.append(Entry(frame2, textvariable=val_list[i*11+1]))
    phdr_struct.vaddr.append(Entry(frame2, textvariable=val_list[i*11+2]))                                                                                                                                      
    phdr_struct.paddr.append(Entry(frame2, textvariable=val_list[i*11+3]))
    phdr_struct.fsize.append(Entry(frame2, textvariable=val_list[i*11+4]))
    phdr_struct.msize.append(Entry(frame2, textvariable=val_list[i*11+5]))
    phdr_struct.flags.append(Entry(frame2, textvariable=val_list[i*11+6]))
    phdr_struct.acc_bits.append(Entry(frame2, textvariable=val_list[i*11+7]))
    phdr_struct.seg_bits.append(Entry(frame2, textvariable=val_list[i*11+8]))
    phdr_struct.align.append(Entry(frame2, textvariable=val_list[i*11+9]))
    phdr_struct.binary.append(Entry(frame2, textvariable=val_list[i*11+10]))


    initial_phdr_struct.s_type.append(Entry(frame2))
    initial_phdr_struct.offset.append(Entry(frame2))
    initial_phdr_struct.vaddr.append(Entry(frame2))
    initial_phdr_struct.paddr.append(Entry(frame2))
    initial_phdr_struct.fsize.append(Entry(frame2))
    initial_phdr_struct.msize.append(Entry(frame2))
    initial_phdr_struct.flags.append(Entry(frame2))
    initial_phdr_struct.acc_bits.append(Entry(frame2))
    initial_phdr_struct.seg_bits.append(Entry(frame2))
    initial_phdr_struct.align.append(Entry(frame2))
    initial_phdr_struct.binary.append(Entry(frame2))


    #Decode phdr types and flags
    if (i < elf_header1.e_phnum):
      if phdr_table1[i].p_type == 0 :
        ptype = "null"
      elif phdr_table1[i].p_type == 1 :
        ptype = "load"
      elif phdr_table1[i].p_type == 2 :
        ptype = "dynamic"
      elif phdr_table1[i].p_type == 3 :
        ptype = "interp"
      elif phdr_table1[i].p_type == 4 :
        ptype = "note"
      elif phdr_table1[i].p_type == 5 :
        ptype = "shlib"
      elif phdr_table1[i].p_type == 6 :
        ptype = "phdr"
      elif phdr_table1[i].p_type == 0x70000000 :
        ptype = "loproc"
      elif phdr_table1[i].p_type == 0x7fffffff :
        ptype = "hiproc"
      else :
        ptype = "undefined"

      #DECODE FLAGS and Checkbox Code
      # rvar = IntVar()
      # wvar = IntVar()
      # evar = IntVar()
      # checkbox1 = Checkbutton(frame2, variable=rvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
      # checkbox2 = Checkbutton(frame2, variable=wvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
      # checkbox3 = Checkbutton(frame2, variable=evar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
      # checkbox1.var = rvar
      # checkbox2.var = wvar
      # checkbox3.var = evar
      # tmp_string = ""
      pflag_var = 0x0
      if(phdr_table1[i].p_flags & 0x4 == 4):
        # tmp_string += "R"
        pflag_var += 0x4 
        # rvar.set(1)
      if(phdr_table1[i].p_flags & 0x2 == 2):
        # tmp_string += "W"
        pflag_var += 0x2
        # wvar.set(1)
      if(phdr_table1[i].p_flags & 0x1 == 1):
        # tmp_string += "E"
        pflag_var += 0x1 
        # evar.set(1)
    # check_list.append(checkbox1)
    # check_list.append(checkbox2)
    # check_list.append(checkbox3)

    #MORE FLAG DECODING
    access_type_var = 0x0
    segment_type_var = 0x0
    if(phdr_table1[i].p_flags & 0x200000 == 0x200000):
      access_type_var += 0x1
    if(phdr_table1[i].p_flags & 0x400000 == 0x400000):
      access_type_var += 0x2
    if(phdr_table1[i].p_flags & 0x800000 == 0x800000):
      access_type_var += 0x4
    if(phdr_table1[i].p_flags & 0x1000000 == 0x1000000):
      segment_type_var += 0x1
    if(phdr_table1[i].p_flags & 0x2000000 == 0x2000000):
      segment_type_var += 0x2
    if(phdr_table1[i].p_flags & 0x4000000 == 0x4000000):
      segment_type_var += 0x4

    phdr_struct.s_type[i].insert(0, ptype)
    phdr_struct.offset[i].insert(0, hex(phdr_table1[i].p_offset))
    phdr_struct.vaddr[i].insert(0, hex(phdr_table1[i].p_vaddr))
    phdr_struct.paddr[i].insert(0, hex(phdr_table1[i].p_paddr))
    phdr_struct.fsize[i].insert(0, hex(phdr_table1[i].p_filesz))
    phdr_struct.msize[i].insert(0, hex(phdr_table1[i].p_memsz))
    phdr_struct.flags[i].insert(0, hex(pflag_var))
    phdr_struct.acc_bits[i].insert(0, hex(access_type_var))
    phdr_struct.seg_bits[i].insert(0, hex(segment_type_var))
    phdr_struct.align[i].insert(0, hex(phdr_table1[i].p_align))

    initial_phdr_struct.s_type[i].insert(0, ptype)
    initial_phdr_struct.offset[i].insert(0, hex(phdr_table1[i].p_offset))
    initial_phdr_struct.vaddr[i].insert(0, hex(phdr_table1[i].p_vaddr))
    initial_phdr_struct.paddr[i].insert(0, hex(phdr_table1[i].p_paddr))
    initial_phdr_struct.fsize[i].insert(0, hex(phdr_table1[i].p_filesz))
    initial_phdr_struct.msize[i].insert(0, hex(phdr_table1[i].p_memsz))
    initial_phdr_struct.flags[i].insert(0, hex(pflag_var))
    initial_phdr_struct.acc_bits[i].insert(0, hex(access_type_var))
    initial_phdr_struct.seg_bits[i].insert(0, hex(segment_type_var))
    initial_phdr_struct.align[i].insert(0, hex(phdr_table1[i].p_align))


    #insert structure into grid
    phdr_struct.s_type[i].grid(row=i+6+2, column=1)
    phdr_struct.offset[i].grid(row=i+6+2, column=2)
    phdr_struct.vaddr[i].grid(row=i+6+2, column=3)
    phdr_struct.paddr[i].grid(row=i+6+2, column=4)
    phdr_struct.fsize[i].grid(row=i+6+2, column=5)
    phdr_struct.msize[i].grid(row=i+6+2, column=6)
    phdr_struct.flags[i].grid(row=i+6+2, column=8)
    phdr_struct.acc_bits[i].grid(row=i+6+2, column=9)
    phdr_struct.seg_bits[i].grid(row=i+6+2, column=10)
    phdr_struct.align[i].grid(row=i+6+2, column=7)
    phdr_struct.binary[i].grid(row=i+6+2, column=11)

    original_offset_list.append(phdr_table1[i].p_offset)


  # #Checkboxes for 'Add' segment
  # rvar = IntVar()
  # wvar = IntVar()
  # evar = IntVar()
  # checkbox1 = Checkbutton(frame2, variable=rvar, onvalue=1, offvalue=0, borderwidth=0)
  # checkbox2 = Checkbutton(frame2, variable=wvar, onvalue=1, offvalue=0, borderwidth=0)
  # checkbox3 = Checkbutton(frame2, variable=evar, onvalue=1, offvalue=0, borderwidth=0)
  # checkbox1.var = rvar
  # checkbox2.var = wvar
  # checkbox3.var = evar
  # check_list.append(checkbox1)
  # check_list.append(checkbox2)
  # check_list.append(checkbox3)
  # checkbox1.grid(row=elf_header1.e_phnum+7+1, column=7, sticky='nesw')
  # checkbox2.grid(row=elf_header1.e_phnum+7+1, column=8, sticky='nesw')
  # checkbox3.grid(row=elf_header1.e_phnum+7+1, column=9, sticky='nesw')
  # print "initial checklist size", len(check_list)

  #populate segment structure
  seg_struct.oldseg_num = elf_header1.e_phnum 
  seg_struct.num_segs_added = 0 
  seg_struct.seg_num = elf_header1.e_phnum
  #DELETE buttons  
  for i in range(elf_header1.e_phnum):
    button_generate = Button(frame2, text = "Delete", width=4, command= partial(create_grid, original_offset_list, frame2, val_list, elf_in_fp1, elf_in_file_name1, elf_in_file_name1, is_out_elf_64_bit, elf_header1, phdr_table1, False, True, i, add_entry_list, add_val_list, file_struct_new, entry_struct_new, canvas, seg_struct, initial_phdr_struct, phdr_struct)) #modifies/disintegrates new ELF
    button_generate.grid(row=i+2+1+1+2+2, column=12)


  #RADIO BUTTONS
  rb_var1.set(1)    #default is 'modify ELF'
  rb_var2.set(1)    #default is 'Qualcomm ELF'
  rb1 = Radiobutton(frame2, text="Modify ELF", variable=rb_var1, value=1)
  rb1.grid(row=0, column=0)
  rb2 = Radiobutton(frame2, text="Disintegrate ELF", variable=rb_var1, value=2, command=partial(grey_grid, original_offset_list, frame2, val_list, elf_in_fp1, elf_in_file_name1, elf_in_file_name1, is_out_elf_64_bit, elf_header1, phdr_table1, False, False, add_entry_list, add_val_list, file_struct_new, entry_struct_new, canvas, blank_file_struct, seg_struct, initial_phdr_struct, phdr_struct))
  rb2.grid(row=0, column=1)
  rb3 = Radiobutton(frame2, text="Create ELF", variable=rb_var1, value=3).grid(row=0, column=2)

  #LINE CODE - between radiobuttons and ELF header segment
  canvas_a = Canvas(frame2, width=1500, height=10)      #horizontal line above phdr
  canvas_a.grid(row=4+1, column=0, columnspan=12)
  canvas_a.create_line(20, 8, 1550, 8, width=1, dash=(4)) 
  canvas_b = Canvas(frame2, width=1500, height=10)      #horizontal line above elf header
  canvas_b.grid(row=2, column=0, columnspan=12)
  canvas_b.create_line(20, 8, 1550, 8, width=1, dash=(4))
  canvas_c = Canvas(frame2, width=1500, height=10)      #horizontal line under phdr
  canvas_c.grid(row=elf_header1.e_phnum+9, column=0, columnspan=12)
  canvas_c.create_line(20, 8, 1550, 8, width=1, dash=(4))

  #Create 'add' button                                                                                     
  button_generate = Button(frame2, text = "Add", width=4, command= partial(create_grid, original_offset_list, frame2, val_list, elf_in_fp1, elf_in_file_name1, elf_in_file_name1, is_out_elf_64_bit, elf_header1, phdr_table1, True, False, 0, add_entry_list, add_val_list, file_struct_new, entry_struct_new, canvas, seg_struct, initial_phdr_struct, phdr_struct)) #modifies/disintegrates new ELF
  button_generate.grid(row=elf_header1.e_phnum+8, column=12, sticky='w')

  #Create 'generate' button
  button_generate = Button(frame2, text = "Generate", width=16, command=lambda: update_grid(val_list, original_offset_list, elf_in_file_name1, elf_in_file_name1, is_out_elf_64_bit, frame2, elf_header1, phdr_table1, False, file_struct_new, entry_struct_new, seg_struct, initial_phdr_struct, phdr_struct)) #modifies/disintegrates new ELF
  button_generate.grid(row=0, column=9)
  # button_generate.grid(row=elf_header1.e_phnum+10, column=0)

  #Create 'help' button
  button_generate = Button(frame2, text = "Help", width=16, command=lambda: pop_up(modify_help_msg))
  button_generate.grid(row=0, column=10)
 
  #Create 'quit' button
  button_generate = Button(frame2, text = "Quit", width=16, command=lambda: quit()) #disintegrates original ELF
  button_generate.grid(row=0, column=11) 



  #event loop
  root.mainloop()
  elf_in_fp1.close() #originally above
  
  return 0

###########################################################################################
# grey_grid - Used for 'Disintegrate' feature. Greys out grid based on input file chosen.
#             Not based on previous modified ELF
###########################################################################################
def grey_grid (original_offset_list, frame2, val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, seg_added, seg_deleted, add_entry_list, add_val_list, file_struct, entry_struct, canvas, load_file_struct, seg_struct, initial_phdr_struct, phdr_struct):

  if not os.path.isfile(file_struct.input_file.get()):  #make sure file is valid
    pop_up('File does not exist')
    return

  #Recreate Grid
  frame2.grid_forget()
  canvas.delete("all")
  frame1 = Frame(root)
  frame1.grid(row=0, column=0)

  canvas=Canvas(frame1, borderwidth=0, width=1570, height=700)
  frame2=Frame(canvas, width=1570, height=700)
  myscrollbar=Scrollbar(frame1,orient="vertical",command=canvas.yview)
  canvas.configure(yscrollcommand=myscrollbar.set)

  myscrollbar.pack(side="right",fill="y")
  canvas.pack(side="left")
  canvas.create_window((0,0),window=frame2,anchor='nw')
  frame2.bind("<Configure>",lambda event, arg=canvas: scrollFunction(event, arg))

  new_entry_list = []
  new_val_list = []
  new_check_list = []
  blank_list = []
  new_phdr_struct = phdrStruct()

  #Input/Output file code
  file_struct_new = fileStruct(frame2)
  if not load_file_struct.input_file.get():
    file_struct_new.input_file.insert(0, file_struct.input_file.get())
  else:
    file_struct_new.input_file.insert(0, load_file_struct.input_file.get())
  file_struct_new.input_file.grid(row=1, column=1, columnspan=3, sticky='WE')

  #Create New Header Structures
  [new_elf_header, new_phdr_table] = \
    elf_gen_tools.preprocess_elf_file(file_struct_new.input_file.get()) 

  # button_input_file = Button(frame2, text = "Input File", command=partial(load_file, file_struct_new))
  button_input_file = Button(frame2, text = "Input File", command=partial(load_file_grey_grid, original_offset_list, frame2, val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, seg_added, seg_deleted, add_entry_list, add_val_list, file_struct, entry_struct, canvas, load_file_struct, seg_struct, initial_phdr_struct, phdr_struct))
  button_input_file.grid(row=1, column=0)

  if file_struct.output_file.get():
    file_struct_new.output_file.insert(0, file_struct.output_file.get())
  else: 
    file_struct_new.output_file.insert(0, os.getcwd())
  file_struct_new.output_file.grid(row=1, column=5, columnspan=3, sticky='WE')
  button_input_file = Button(frame2, text = "Output Path", command= partial(load_directory, file_struct_new, True, new_elf_header.e_phnum, frame2)) #, command=lambda: call_gui(file_struct_new.input_file.get(), is_elf1_64_bit))
  button_input_file.grid(row=1, column=4)


  #Decode header to find class
  if new_elf_header.e_ident[ELFINFO_CLASS_INDEX] == '\x01': #PUT INTO GREYGRID TOO
    arch_64_bit = False #32 bits
  elif new_elf_header.e_ident[ELFINFO_CLASS_INDEX] == '\x02':
    arch_64_bit = True
  else:
    arch_64_bit = True
    pop_up('Invalid class for ELF File')
    return

  #RADIO BUTTON CODE
  rb_var1.set(2)    #default is 'modify ELF'
  rb_var2.set(1)    #default is 'Qualcomm ELF'
  rb1 = Radiobutton(frame2, text="Modify ELF", variable=rb_var1, value=1, command=partial(create_grid, original_offset_list, frame2, val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, False, False, 0, blank_list, blank_list, file_struct_new, entry_struct, canvas, seg_struct, initial_phdr_struct, phdr_struct))
  rb1.grid(row=0, column=0)

  rb2 = Radiobutton(frame2, text="Disintegrate ELF", variable=rb_var1, value=2)
  rb2.grid(row=0, column=1)

  rb3 = Radiobutton(frame2, text="Create ELF", variable=rb_var1, value=3)
  rb3.grid(row=0, column=2)

  #ELF HEADER CODE
  Label(frame2, text = "ELF Header").grid(row=1+2+1, column=0)    #Create labels for ELF header entries
  Label(frame2, text = "Class").grid(row=0+2+1, column=1)
  Label(frame2, text = "Type").grid(row=0+2+1, column=2)
  Label(frame2, text = "Entry Addr").grid(row=0+2+1, column=3)
  Label(frame2, text = "PH Start").grid(row=0+2+1, column=4)
  Label(frame2, text = "Segment Start").grid(row=0+2+1, column=5)
  Label(frame2, text = "ELF Header Size (bytes)").grid(row=0+2+1, column=6)
  Label(frame2, text = "PH Size (bytes)").grid(row=0+2+1, column=7)
  Label(frame2, text = "PH Num").grid(row=0+2+1, column=8)
  Label(frame2, text = "Section Header Offset").grid(row=0+2+1, column=9)
  Label(frame2, text = "SH Table Size").grid(row=0+2+1, column=10)
  Label(frame2, text = "Version").grid(row=0+2+1, column=11)

  #Create entries for elf_header1
  e_class = Entry(frame2)
  e_type = Entry(frame2)
  e_entryaddr = Entry(frame2)
  e_phdrstart = Entry(frame2)
  e_segstart = Entry(frame2)
  e_headersize = Entry(frame2)
  e_phsize = Entry(frame2)
  e_phnum = Entry(frame2)
  e_data = Entry(frame2) 
  e_flags = Entry(frame2)
  e_secoff = Entry(frame2)
  e_secsize = Entry(frame2)
  e_version = Entry(frame2)

  #Decode header type
  if new_elf_header.e_type == 0 :
    etype = "None"
  elif new_elf_header.e_type == 1 :
    etype = "Rel"
  elif new_elf_header.e_type == 2 :
    etype = "Exec"
  elif new_elf_header.e_type == 3 :
    etype = "Dyn"
  elif new_elf_header.e_type == 4 :
    etype = "Core"
  elif new_elf_header.e_type == 0xff00 :
    etype = "Loproc"
  elif new_elf_header.e_type == 0xffff :
    etype = "Hiproc"
  else :
    etype = "Undefined"
  #Decode bit type
  if arch_64_bit:
    eclass = "ELF_64"
  else:
    eclass = "ELF_32"
  #Decode version  
  if(new_elf_header.e_version == 0x1):
    version_var = 'Current'
  else:
    version_var = 'Invalid'

  #Insert ELF header values into entries
  e_class.insert(0, eclass)
  e_type.insert(0, etype)
  e_entryaddr.insert(0, hex(new_elf_header.e_entry))
  e_phdrstart.insert(0, hex(new_elf_header.e_phoff))
  seg_start = roundup(new_elf_header.e_phoff + new_elf_header.e_phentsize*new_elf_header.e_phnum, PAGE_SIZE) 
  e_segstart.insert(0, hex(seg_start))
  e_headersize.insert(0, hex(new_elf_header.e_ehsize))
  e_phsize.insert(0, hex(new_elf_header.e_phentsize*new_elf_header.e_phnum))
  e_phnum.insert(0, new_elf_header.e_phnum)
  e_secoff.insert(0, hex(new_elf_header.e_shoff)) 
  e_secsize.insert(0, hex(new_elf_header.e_shentsize*new_elf_header.e_shnum))
  e_version.insert(0, version_var)

  e_class.configure(state='readonly')
  e_type.configure(state='readonly')
  e_entryaddr.configure(state='readonly') 
  e_phdrstart.configure(state='readonly') 
  e_segstart.configure(state='readonly')
  e_headersize.configure(state='readonly')
  e_phsize.configure(state='readonly')
  e_phnum.configure(state='readonly')
  e_secoff.configure(state='readonly')
  e_secsize.configure(state='readonly')
  e_version.configure(state='readonly')

  #Insert ELF header entries into GUI
  e_class.grid(row=1+2+1, column=1)
  e_type.grid(row=1+2+1, column=2)
  e_entryaddr.grid(row=1+2+1, column=3)
  e_phdrstart.grid(row=1+2+1, column=4)
  e_segstart.grid(row=1+2+1, column=5)
  e_headersize.grid(row=1+2+1, column=6)
  e_phsize.grid(row=1+2+1, column=7)
  e_phnum.grid(row=1+2+1, column=8)
  e_secoff.grid(row=1+2+1, column=9)
  e_secsize.grid(row=1+2+1, column=10)
  e_version.grid(row=1+2+1, column=11)


  #'PROGRAM HEADER TABLE' CODE
  #Labels for PHDR entries
  Label(frame2, text = "PHDR Entries").grid(row=2+1+2+1, column=0)
  Label(frame2, text = "Type").grid(row=2+1+2+1, column=1)
  Label(frame2, text = "Segment Offset").grid(row=2+1+2+1, column=2)
  Label(frame2, text = "Virt Addr").grid(row=2+1+2+1, column=3)
  Label(frame2, text = "Phys Addr").grid(row=2+1+2+1, column=4)
  Label(frame2, text = "File Size").grid(row=2+1+2+1, column=5)
  Label(frame2, text = "Mem Size").grid(row=2+1+2+1, column=6)
  Label(frame2, text = "Flags (RWE)").grid(row=2+1+2+1, column=8)
  Label(frame2, text = "Access Type").grid(row=2+1+2+1, column=9)
  Label(frame2, text = "Segment Type").grid(row=2+1+2+1, column=10)
  # Label(frame2, text = "Flag (R)").grid(row=2+1+2+1, column=7)
  # Label(frame2, text = "Flag (W)").grid(row=2+1+2+1, column=8)
  # Label(frame2, text = "Flag (E)").grid(row=2+1+2+1, column=9)
  Label(frame2, text = "Address Alignment").grid(row=2+1+2+1, column=7)
  Label(frame2, text = "Path for Binary").grid(row=2+1+2+1, column=11)

  #Create grid entries
  for i in range(new_elf_header.e_phnum):
    Label(frame2, text = "Segment "+ str(i)).grid(row=i+2+1+1+2+1)

    entvar=StringVar() #doesn't need to be in loop?

    #Create list for current entries
    new_phdr_struct.s_type.append(Entry(frame2))
    new_phdr_struct.offset.append(Entry(frame2))
    new_phdr_struct.vaddr.append(Entry(frame2))
    new_phdr_struct.paddr.append(Entry(frame2))
    new_phdr_struct.fsize.append(Entry(frame2))
    new_phdr_struct.msize.append(Entry(frame2))
    new_phdr_struct.flags.append(Entry(frame2))
    new_phdr_struct.acc_bits.append(Entry(frame2))
    new_phdr_struct.seg_bits.append(Entry(frame2))
    new_phdr_struct.align.append(Entry(frame2))
    new_phdr_struct.binary.append(Entry(frame2))

    #Decode phdr types and flags
    if (i < new_elf_header.e_phnum):
      if new_phdr_table[i].p_type == 0 :
        ptype = "null"
      elif new_phdr_table[i].p_type == 1 :
        ptype = "load"
      elif new_phdr_table[i].p_type == 2 :
        ptype = "dynamic"
      elif new_phdr_table[i].p_type == 3 :
        ptype = "interp"
      elif new_phdr_table[i].p_type == 4 :
        ptype = "note"
      elif new_phdr_table[i].p_type == 5 :
        ptype = "shlib"
      elif new_phdr_table[i].p_type == 6 :
        ptype = "phdr"
      elif new_phdr_table[i].p_type == 0x70000000 :
        ptype = "loproc"
      elif new_phdr_table[i].p_type == 0x7fffffff :
        ptype = "hiproc"
      else :
        ptype = "undefined"

    #   #Checkboxes - Decode flags
    #   rvar = IntVar()
    #   wvar = IntVar()
    #   evar = IntVar()
    #   checkbox1 = Checkbutton(frame2, variable=rvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    #   checkbox2 = Checkbutton(frame2, variable=wvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    #   checkbox3 = Checkbutton(frame2, variable=evar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    #   checkbox1.var = rvar
    #   checkbox2.var = wvar
    #   checkbox3.var = evar
    #   if(new_phdr_table[i].p_flags & 0x4 == 4):
    #     rvar.set(1)
    #   if(new_phdr_table[i].p_flags & 0x2 == 2):
    #     wvar.set(1)
    #   if(new_phdr_table[i].p_flags & 0x1 == 1):
    #     evar.set(1)
    # new_check_list.append(checkbox1)
    # new_check_list.append(checkbox2)
    # new_check_list.append(checkbox3)

    #Decode Flags
    pflag_var = 0x0
    access_type_var = 0x0
    segment_type_var = 0x0
    if(new_phdr_table[i].p_flags & 0x4 == 4):
      pflag_var += 0x4 
    if(new_phdr_table[i].p_flags & 0x2 == 2):
      pflag_var += 0x2
    if(new_phdr_table[i].p_flags & 0x1 == 1):
      pflag_var += 0x1 
    if(new_phdr_table[i].p_flags & 0x200000 == 0x200000):
      access_type_var += 0x1
    if(new_phdr_table[i].p_flags & 0x400000 == 0x400000):
      access_type_var += 0x2
    if(new_phdr_table[i].p_flags & 0x800000 == 0x800000):
      access_type_var += 0x4
    if(new_phdr_table[i].p_flags & 0x1000000 == 0x1000000):
      segment_type_var += 0x1
    if(new_phdr_table[i].p_flags & 0x2000000 == 0x2000000):
      segment_type_var += 0x2
    if(new_phdr_table[i].p_flags & 0x4000000 == 0x4000000):
      segment_type_var += 0x4

    #Insert data into PHDR entries
    new_phdr_struct.s_type[i].insert(0, ptype)
    new_phdr_struct.offset[i].insert(0, hex(new_phdr_table[i].p_offset))
    new_phdr_struct.vaddr[i].insert(0, hex(new_phdr_table[i].p_vaddr))
    new_phdr_struct.paddr[i].insert(0, hex(new_phdr_table[i].p_paddr))
    new_phdr_struct.fsize[i].insert(0, hex(new_phdr_table[i].p_filesz))
    new_phdr_struct.msize[i].insert(0, hex(new_phdr_table[i].p_memsz))
    new_phdr_struct.flags[i].insert(0, hex(pflag_var))
    new_phdr_struct.acc_bits[i].insert(0, hex(access_type_var))
    new_phdr_struct.seg_bits[i].insert(0, hex(segment_type_var))
    new_phdr_struct.align[i].insert(0, hex(new_phdr_table[i].p_align))
    new_phdr_struct.binary[i].insert(0, file_struct_new.output_file.get())


    new_phdr_struct.s_type[i].configure(state='readonly')
    new_phdr_struct.offset[i].configure(state='readonly')
    new_phdr_struct.vaddr[i].configure(state='readonly')
    new_phdr_struct.paddr[i].configure(state='readonly')
    new_phdr_struct.fsize[i].configure(state='readonly')
    new_phdr_struct.msize[i].configure(state='readonly')
    new_phdr_struct.flags[i].configure(state='readonly')
    new_phdr_struct.acc_bits[i].configure(state='readonly')
    new_phdr_struct.seg_bits[i].configure(state='readonly')
    new_phdr_struct.align[i].configure(state='readonly')
    new_phdr_struct.binary[i].configure(state='readonly')
    # # checkbox1.configure(state='disabled')
    # # checkbox2.configure(state='disabled')
    # # checkbox3.configure(state='disabled')

    new_phdr_struct.s_type[i].grid(row=i+7, column=1)
    new_phdr_struct.offset[i].grid(row=i+7, column=2)
    new_phdr_struct.vaddr[i].grid(row=i+7, column=3)
    new_phdr_struct.paddr[i].grid(row=i+7, column=4)
    new_phdr_struct.fsize[i].grid(row=i+7, column=5)
    new_phdr_struct.msize[i].grid(row=i+7, column=6)
    new_phdr_struct.flags[i].grid(row=i+7, column=8)
    new_phdr_struct.acc_bits[i].grid(row=i+7, column=9)
    new_phdr_struct.seg_bits[i].grid(row=i+7, column=10)
    new_phdr_struct.align[i].grid(row=i+7, column=7)
    new_phdr_struct.binary[i].grid(row=i+7, column=11)
    # checkbox1.grid(row=i+6+1, column=7, sticky='nesw')
    # checkbox2.grid(row=i+6+1, column=8, sticky='nesw')
    # checkbox3.grid(row=i+6+1, column=9, sticky='news')

    #create delete buttons                                                        
    button_generate = Button(frame2, text = "Delete", width=4, state='disabled') #modifies/disintegrates new ELF
    button_generate.grid(row=i+2+1+1+2+1, column=12)
  
  #LINE CODE - between radiobuttons and ELF header segment
  canvas_a = Canvas(frame2, width=1500, height=10)      #horizontal line above phdr
  canvas_a.grid(row=4+1, column=0, columnspan=12)
  canvas_a.create_line(20, 8, 1550, 8, width=1, dash=(4)) 
  canvas_b = Canvas(frame2, width=1500, height=10)      #horizontal line above elf header
  canvas_b.grid(row=2, column=0, columnspan=12)
  canvas_b.create_line(20, 8, 1550, 8, width=1, dash=(4))
  canvas_c = Canvas(frame2, width=1500, height=10)      #horizontal line under phdr
  canvas_c.grid(row=new_elf_header.e_phnum+9, column=0, columnspan=12)
  canvas_c.create_line(20, 8, 1550, 8, width=1, dash=(4))
  new_elf_fp = elf_gen_tools.OPEN(file_struct_new.input_file.get(), "rb")

  #Create 'disintegrate' Button                                                                     
  button_generate = Button(frame2, text = "Disintegrate", width=16, command=lambda: disassemble_elf(new_elf_fp, new_elf_header, arch_64_bit, file_struct_new, new_phdr_struct))
  button_generate.grid(row=0, column=9)
  # button_generate.grid(row=new_elf_header.e_phnum+10, column=0)

  #Create 'help' button
  button_generate = Button(frame2, text = "Help", width=16, command=lambda: pop_up(disintegrate_help_msg))
  button_generate.grid(row=0, column=10)
 
  #Create 'quit' button
  button_generate = Button(frame2, text = "Quit", width=16, command=lambda: quit()) #disintegrates original ELF
  button_generate.grid(row=0, column=11) 


  #event loop
  root.mainloop()
  elf_fp.close() #originally above
  return 

  
#################################################################################
# create_grid - Recreates grid. Called after segments added or deleted, or when   
#               switching from 'Disintegrate' to 'Modify'
#################################################################################
def create_grid (original_offset_list, frame1, val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, seg_added, seg_deleted, num_deleted, add_entry_list, add_val_list, file_struct, entry_struct, canvas, seg_struct, initial_phdr_struct, phdr_struct):

  #ADDED SEGMENT ARGUMENT CHECK
  if(seg_added == True):
    if not (os.path.isfile(add_val_list[10].get())):     #make sure binary exists
      pop_up('Binary does not exist in added segment. \n\nFile must be in working directory')
      return                                            #make sure other fields have input
    for i in range (1,7):
      try: 
        int(add_val_list[i].get(), 16)
      except:
        pop_up('Invalid hex value for added segment')
        return
    if not (add_val_list[0].get() == 'load' or add_val_list[0].get() == 'null' or add_val_list[0].get() == 'dynamic' or add_val_list[0].get() == 'interp' or add_val_list[0].get() == 'note' or add_val_list[0].get() == 'shlib' or add_val_list[0].get() == 'phdr' or add_val_list[0].get() == 'loproc' or add_val_list[0].get() == 'hiproc'): 
      pop_up('Invalid Type for added segment. \n\nDefault Type will be load')
      
  frame1.grid_forget()
  canvas.delete("all")
  frame1 = Frame(root)
  frame1.grid(row=0, column=0)

  canvas=Canvas(frame1, borderwidth=0, width=1570, height=700)
  frame2=Frame(canvas, width=1570, height=700)
  myscrollbar=Scrollbar(frame1,orient="vertical",command=canvas.yview)
  canvas.configure(yscrollcommand=myscrollbar.set)

  myscrollbar.pack(side="right",fill="y")
  canvas.pack(side="left")
  canvas.create_window((0,0),window=frame2,anchor='nw')
  frame2.bind("<Configure>",lambda event, arg=canvas: scrollFunction(event, arg))

  new_check_list = []
  new_val_list = []
  new_add_entry_list = []
  new_add_val_list = []
  blank_list = []
  old_seg_num = seg_struct.seg_num
  seg_struct.old_seg_num = seg_struct.seg_num
  segment_added = False
  flag_var = 0
  entry_struct_new = entryStruct(frame2)
  blank_file_struct = fileStruct(frame2)
  new_phdr_struct = phdrStruct()

  # print "\nseg added", seg_added
  # print "seg deleted: ", seg_deleted
  # print "number deleted: ", num_deleted, "\n"

  #Input/Output file code
  file_struct_new = fileStruct(frame2)
  file_struct_new.input_file.insert(0, elf_filename)
  file_struct_new.input_file.grid(row=1, column=1, columnspan=3, sticky='WE')
  button_input_file = Button(frame2, text = "Input File", command= partial(load_file, file_struct_new, frame2))
  button_input_file.grid(row=1, column=0)

  file_struct_new.output_file.insert(0, file_struct.output_file.get())
  file_struct_new.output_file.grid(row=1, column=5, columnspan=3, sticky='WE')
  button_input_file = Button(frame2, text = "Output Path", command= partial(load_directory, file_struct_new, False, 0, frame2)) #, command=lambda: call_gui(file_struct_new.input_file.get(), is_elf1_64_bit))
  button_input_file.grid(row=1, column=4)


  #'EXTRA SEGMENT' CODE ************************************************
  #Labels for additional segment entry
  tmp_seg_num = seg_struct.seg_num
  if(seg_deleted):
    tmp_seg_num-=1
  if(seg_added):
    tmp_seg_num+=1

  Label(frame2, text = "New Segment").grid(row=tmp_seg_num+8, column=0)
  entvar=StringVar()
  #Create list for new entries (typed in)
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())
  new_add_val_list.append(StringVar())

  #Create list for current entries
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[0]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[1]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[2]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[3]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[4]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[5]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[6]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[7]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[8]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[9]))
  new_add_entry_list.append(Entry(frame2, textvariable=new_add_val_list[10]))

  #insert list into grid
  new_add_entry_list[0].grid(row=tmp_seg_num+8, column=1)
  new_add_entry_list[1].grid(row=tmp_seg_num+8, column=2)
  new_add_entry_list[2].grid(row=tmp_seg_num+8, column=3)
  new_add_entry_list[3].grid(row=tmp_seg_num+8, column=4)
  new_add_entry_list[4].grid(row=tmp_seg_num+8, column=5)
  new_add_entry_list[5].grid(row=tmp_seg_num+8, column=6)
  new_add_entry_list[6].grid(row=tmp_seg_num+8, column=7)
  new_add_entry_list[7].grid(row=tmp_seg_num+8, column=8)
  new_add_entry_list[8].grid(row=tmp_seg_num+8, column=9)
  new_add_entry_list[9].grid(row=tmp_seg_num+8, column=10)
  new_add_entry_list[10].grid(row=tmp_seg_num+8, column=11)

  #SEGMENT DELETED ****************************************************************
  if(seg_deleted == True):
    # print "segnum ", seg_struct.seg_num
    # print "num deleted ", num_deleted
    # print "segs added", seg_struct.num_segs_added
    del phdr_table[num_deleted]
    del original_offset_list[num_deleted]

    if (num_deleted > seg_struct.seg_num-1 - seg_struct.num_segs_added): #check if we deleted an added segment
      # print "bin index deleted", num_deleted-(seg_struct.seg_num-seg_struct.num_segs_added)
      seg_struct.num_segs_added -= 1
    seg_struct.seg_num -= 1

  #SEGMENT ADDED - update phdr, entry lists ****************************************
  #Find the program header offset (needed to append phdr)
  file_offset = elf_header.e_phoff
  elf_fp.seek(file_offset)
  if(seg_added == True):
    #Update PHDR for added segment
    if(is_out_elf_64_bit): 
      phdr_table.append(elf_gen_tools.Elf64_Phdr(elf_fp.read(elf_header.e_phentsize))) #append PHDR for 64 byte
    else:
      phdr_table.append(elf_gen_tools.Elf32_Phdr(elf_fp.read(elf_header.e_phentsize))) #append PHDR for 32 byte
    #Decode 'type'
    if(Entry.get(add_entry_list[0]) == 'null'):     
      phdr_table[seg_struct.seg_num].p_type  = 0
    elif (Entry.get(add_entry_list[0]) == 'load'):
      phdr_table[seg_struct.seg_num].p_type  = 1
    elif (Entry.get(add_entry_list[0]) == 'dynamic'):
      phdr_table[seg_struct.seg_num].p_type  = 2
    elif (Entry.get(add_entry_list[0]) == 'interp'):
      phdr_table[seg_struct.seg_num].p_type  = 3
    elif (Entry.get(add_entry_list[0]) == 'note'):
      phdr_table[seg_struct.seg_num].p_type  = 4
    elif (Entry.get(add_entry_list[0]) == 'shlib'):
      phdr_table[seg_struct.seg_num].p_type  = 5
    elif (Entry.get(add_entry_list[0]) == 'phdr'):
      phdr_table[seg_struct.seg_num].p_type  = 6
    elif (Entry.get(add_entry_list[0]) == 'loproc'):
      phdr_table[seg_struct.seg_num].p_type  = 0x70000000
    elif (Entry.get(add_entry_list[0]) == 'hiproc'):
      phdr_table[seg_struct.seg_num].p_type  = 0x7fffffff

    #Decode flags
    pflags_var = int(add_entry_list[6].get(), 16) #bottom 3 bits - no need to decode
    access_type_var = 0x0
    segment_type_var = 0x0
    if( int(Entry.get(add_entry_list[7]), 16) & 0x1 == 0x1): #check first bit
      access_type_var += 0x200000
    if( int(Entry.get(add_entry_list[7]), 16) & 0x2 == 0x2): #check first bit
      access_type_var += 0x400000
    if( int(Entry.get(add_entry_list[7]), 16) & 0x4 == 0x4): #check first bit
      access_type_var += 0x800000
    if( int(Entry.get(add_entry_list[8]), 16) & 0x1 == 0x1): #check first bit
      segment_type_var += 0x1000000
    if( int(Entry.get(add_entry_list[8]), 16) & 0x2 == 0x2): #check first bit
      segment_type_var += 0x2000000
    if( int(Entry.get(add_entry_list[8]), 16) & 0x4 == 0x4): #check first bit
      segment_type_var += 0x4000000

    #Update PHDR with new segment values
    phdr_table[seg_struct.seg_num].p_flags = (pflags_var + access_type_var + segment_type_var)
    phdr_table[seg_struct.seg_num].p_offset  = int(Entry.get(add_entry_list[1]), 16)  #offset
    phdr_table[seg_struct.seg_num].p_vaddr  = int(Entry.get(add_entry_list[2]), 16)  #vaddr
    phdr_table[seg_struct.seg_num].p_paddr  = int(Entry.get(add_entry_list[3]), 16)  #paddr
    phdr_table[seg_struct.seg_num].p_filesz  = int(Entry.get(add_entry_list[4]), 16)  #filesz
    phdr_table[seg_struct.seg_num].p_memsz = int(Entry.get(add_entry_list[5]), 16)  #memsz
    phdr_table[seg_struct.seg_num].p_align  = int(Entry.get(add_entry_list[6]), 16)  #align

    entvar=StringVar()
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())
    val_list.append(StringVar())

    #Populate structure with current entries
    phdr_struct.s_type.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11]))
    phdr_struct.offset.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+1]))
    phdr_struct.vaddr.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+2]))                                                                                                                                      
    phdr_struct.paddr.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+3]))
    phdr_struct.fsize.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+4]))
    phdr_struct.msize.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+5]))
    phdr_struct.flags.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+6]))
    phdr_struct.acc_bits.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+7]))
    phdr_struct.seg_bits.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+8]))
    phdr_struct.align.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+9]))
    phdr_struct.binary.append(Entry(frame2, textvariable=val_list[seg_struct.seg_num*11+10]))

    #Add entries in lists
    entvar=StringVar()
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())

    #Add new entries in structure
    new_phdr_struct.s_type.append(Entry(frame2, textvariable=new_val_list[0]))
    new_phdr_struct.offset.append(Entry(frame2, textvariable=new_val_list[1]))
    new_phdr_struct.vaddr.append(Entry(frame2, textvariable=new_val_list[2]))
    new_phdr_struct.paddr.append(Entry(frame2, textvariable=new_val_list[3]))
    new_phdr_struct.fsize.append(Entry(frame2, textvariable=new_val_list[4]))
    new_phdr_struct.msize.append(Entry(frame2, textvariable=new_val_list[5]))
    new_phdr_struct.flags.append(Entry(frame2, textvariable=new_val_list[6]))
    new_phdr_struct.acc_bits.append(Entry(frame2, textvariable=new_val_list[7]))
    new_phdr_struct.seg_bits.append(Entry(frame2, textvariable=new_val_list[8]))
    new_phdr_struct.align.append(Entry(frame2, textvariable=new_val_list[9]))
    new_phdr_struct.binary.append(Entry(frame2, textvariable=new_val_list[10]))

    seg_struct.num_segs_added += 1 #used when ELF is generated so number of segments to add from binaries is known
    seg_struct.seg_num += 1


  #'ELF HEADER' CODE ********************************************************
  #Create labels for ELF header entries
  Label(frame2, text = "ELF Header").grid(row=1+2+1, column=0)
  Label(frame2, text = "Class").grid(row=0+2+1, column=1)
  Label(frame2, text = "Type").grid(row=0+2+1, column=2)
  Label(frame2, text = "Entry Addr").grid(row=0+2+1, column=3)
  Label(frame2, text = "PH Start").grid(row=0+2+1, column=4)
  Label(frame2, text = "Segment Start").grid(row=0+2+1, column=5)
  Label(frame2, text = "ELF Header Size (bytes)").grid(row=0+2+1, column=6)
  Label(frame2, text = "PH Size (bytes)").grid(row=0+2+1, column=7)
  Label(frame2, text = "PH Num").grid(row=0+2+1, column=8)
  Label(frame2, text = "Section Header Offset").grid(row=0+2+1, column=9)
  Label(frame2, text = "SH Table Size").grid(row=0+2+1, column=10)
  Label(frame2, text = "Version").grid(row=0+2+1, column=11)

  #Create entries for elf_header
  e_class = Entry(frame2)
  e_type = Entry(frame2)
  # e_entryaddr = Entry(frame2)
  e_phdrstart = Entry(frame2)
  e_segstart = Entry(frame2)
  e_headersize = Entry(frame2)
  e_phsize = Entry(frame2)
  e_phnum = Entry(frame2)
  e_secoff = Entry(frame2)
  e_secsize = Entry(frame2)
  e_version = Entry(frame2)

  #Decode header type
  if elf_header.e_type == 0 :
    etype = "None"
  elif elf_header.e_type == 1 :
    etype = "Rel"
  elif elf_header.e_type == 2 :
    etype = "Exec"
  elif elf_header.e_type == 3 :
    etype = "Dyn"
  elif elf_header.e_type == 4 :
    etype = "Core"
  elif elf_header.e_type == 0xff00 :
    etype = "Loproc"
  elif elf_header.e_type == 0xffff :
    etype = "Hiproc"
  else :
    etype = "Undefined"
  #Decode bit type
  if is_out_elf_64_bit :
    eclass = "ELF_64"
  else :
    eclass = "ELF_32"
  #Decode version
  if(elf_header.e_version == 0x1):
    version_var = 'Current'
  else:
    version_var = 'Invalid'

  #Insert ELF header values into entries
  e_class.insert(0, eclass)
  e_type.insert(0, etype)
  # tmp_addr = entry_address.get()  #use address from GUI input for 'entry_address'
  tmp_addr = entry_struct.entry_addr.get()
  if tmp_addr[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
    tmp_addr = tmp_addr[:-1]
  elf_header.e_entry = int(tmp_addr, 16)
  entry_struct_new.entry_addr.insert(0, tmp_addr)
  # e_entryaddr.insert(0, tmp_addr)
  e_phdrstart.insert(0, hex(elf_header.e_phoff))
  seg_start = roundup(elf_header.e_phoff + elf_header.e_phentsize*elf_header.e_phnum, PAGE_SIZE) 
  e_segstart.insert(0, hex(seg_start))
  # e_segstart.insert(0, hex(elf_header.e_phoff+(elf_header.e_phentsize*seg_num)))  #elf header fields being used remain consistent through execution
  e_headersize.insert(0, hex(elf_header.e_ehsize))
  e_phsize.insert(0, hex(elf_header.e_phentsize*seg_struct.seg_num))
  e_phnum.insert(0, hex(seg_struct.seg_num))
  e_secoff.insert(0, hex(elf_header.e_shoff)) 
  e_secsize.insert(0, hex(elf_header.e_shentsize*elf_header.e_shnum))
  e_version.insert(0, version_var)
  e_class.configure(state='readonly')
  e_type.configure(state='readonly')
  # e_entryaddr.configure(state='readonly')
  e_phdrstart.configure(state='readonly')
  e_segstart.configure(state='readonly')
  e_headersize.configure(state='readonly')
  e_phsize.configure(state='readonly')
  e_phnum.configure(state='readonly')
  e_secoff.configure(state='readonly')
  e_secsize.configure(state='readonly')
  e_version.configure(state='readonly')


  #Insert ELF header entries into GUI
  e_class.grid(row=1+2+1, column=1)
  e_type.grid(row=1+2+1, column=2)
  entry_struct_new.entry_addr.grid(row=1+2+1, column=3)
  # e_entryaddr.grid(row=1+2+1, column=3)
  e_phdrstart.grid(row=1+2+1, column=4)
  e_segstart.grid(row=1+2+1, column=5)
  e_headersize.grid(row=1+2+1, column=6)
  e_phsize.grid(row=1+2+1, column=7)
  e_phnum.grid(row=1+2+1, column=8)
  e_secoff.grid(row=1+2+1, column=9)
  e_secsize.grid(row=1+2+1, column=10)
  e_version.grid(row=1+2+1, column=11)


  #'PROGRAM HEADER' CODE **************************************************
  #Segment alignment entry update
  entry_struct_new.segalign.insert(0, entry_struct.segalign.get())
  entry_struct_new.segalign.grid(row=6, column=1)
  Label(frame2, text = "Offset Alignment(nbytes)").grid(row=6, column=0) 
  #Labels for PHDR entries
  Label(frame2, text = "PHDR Entries").grid(row=7, column=0)
  Label(frame2, text = "Type").grid(row=7, column=1)
  Label(frame2, text = "Segment Offset").grid(row=7, column=2)
  Label(frame2, text = "Virt Addr").grid(row=7, column=3)
  Label(frame2, text = "Phys Addr").grid(row=7, column=4)
  Label(frame2, text = "File Size").grid(row=7, column=5)
  Label(frame2, text = "Mem Size").grid(row=7, column=6)
  # Label(frame2, text = "Pflag Bits (RWE)").grid(row=7, column=7)
  # Label(frame2, text = "Access Type Bits").grid(row=7, column=8)
  # Label(frame2, text = "Segment Type Bits").grid(row=7, column=9)
  Label(frame2, text = "Address Alignment").grid(row=7, column=7)
  Label(frame2, text = "Path for Binary").grid(row=7, column=11)
  #FLAG LABELS ARE NOW BUTTONS THAT DISPLAY FLAG INFO WHEN PRESSED
  button_generate = Button(frame2, text = "Flags (RWE)", command=partial(pop_up, pflag_info))
  button_generate.grid(row=7, column=8)
  button_generate = Button(frame2, text = "Access Type", command=partial(pop_up, access_flag_info))
  button_generate.grid(row=7, column=9)
  button_generate = Button(frame2, text = "Segment Type", command=partial(pop_up, segment_flag_info))
  button_generate.grid(row=7, column=10)

  #Create grid entries
  i=0
  for x in range(seg_struct.old_seg_num): #dont use seg_num since the 'continue' will skip an iteration based on number of remaining segments
    if(seg_deleted == True and x == num_deleted):  #skip over deleted segment
      # print "num deleted: ", num_deleted
      continue
    Label(frame2, text = "Segment "+ str(i)).grid(row=i+8)

    #Create list for new entries (typed in)
    entvar=StringVar()
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())
    new_val_list.append(StringVar())

    #Create list for current entries
    if(seg_added == True): #if seg added, new_val_list will have already been appeneded once (above in code)
      new_phdr_struct.s_type.append(Entry(frame2, textvariable=new_val_list[(i+1)*11]))
      new_phdr_struct.offset.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+1]))
      new_phdr_struct.vaddr.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+2]))
      new_phdr_struct.paddr.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+3]))
      new_phdr_struct.fsize.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+4]))
      new_phdr_struct.msize.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+5]))
      new_phdr_struct.flags.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+6]))
      new_phdr_struct.acc_bits.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+7]))
      new_phdr_struct.seg_bits.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+8]))
      new_phdr_struct.align.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+9]))
      new_phdr_struct.binary.append(Entry(frame2, textvariable=new_val_list[(i+1)*11+10]))
    else:
      new_phdr_struct.s_type.append(Entry(frame2, textvariable=new_val_list[(i)*11]))
      new_phdr_struct.offset.append(Entry(frame2, textvariable=new_val_list[(i)*11+1]))
      new_phdr_struct.vaddr.append(Entry(frame2, textvariable=new_val_list[(i)*11+2]))
      new_phdr_struct.paddr.append(Entry(frame2, textvariable=new_val_list[(i)*11+3]))
      new_phdr_struct.fsize.append(Entry(frame2, textvariable=new_val_list[(i)*11+4]))
      new_phdr_struct.msize.append(Entry(frame2, textvariable=new_val_list[(i)*11+5]))
      new_phdr_struct.flags.append(Entry(frame2, textvariable=new_val_list[(i)*11+6]))
      new_phdr_struct.acc_bits.append(Entry(frame2, textvariable=new_val_list[(i)*11+7]))
      new_phdr_struct.seg_bits.append(Entry(frame2, textvariable=new_val_list[(i)*11+8]))
      new_phdr_struct.align.append(Entry(frame2, textvariable=new_val_list[(i)*11+9]))
      new_phdr_struct.binary.append(Entry(frame2, textvariable=new_val_list[(i)*11+10]))

    # #Update checkbox list
    # rvar = IntVar()
    # wvar = IntVar()
    # evar = IntVar()
    # checkbox1 = Checkbutton(frame2, variable=rvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    # checkbox2 = Checkbutton(frame2, variable=wvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    # checkbox3 = Checkbutton(frame2, variable=evar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    # checkbox1.var = rvar
    # checkbox2.var = wvar
    # checkbox3.var = evar
    # if(check_list[x*3].var.get() == 1):
    #   rvar.set(1)
    # if(check_list[x*3+1].var.get() == 1):
    #   wvar.set(1)
    # if(check_list[x*3+2].var.get()== 1):
    #   evar.set(1)
    # new_check_list.append(checkbox1)
    # new_check_list.append(checkbox2)
    # new_check_list.append(checkbox3)


    #copy old data into new list (cant use seg_num, because it might be incremented from 'add' checkbox)
    if (i < seg_struct.seg_num): #ALSO BREAKS HERE **************************
      e1 = Entry.get(phdr_struct.s_type[x])
      e2 = Entry.get(phdr_struct.offset[x])
      e3 = Entry.get(phdr_struct.vaddr[x])
      e4 = Entry.get(phdr_struct.paddr[x])
      e5 = Entry.get(phdr_struct.fsize[x])
      e6 = Entry.get(phdr_struct.msize[x])
      e7 = Entry.get(phdr_struct.flags[x])
      e8 = Entry.get(phdr_struct.acc_bits[x])
      e9 = Entry.get(phdr_struct.seg_bits[x])
      e10 = Entry.get(phdr_struct.align[x])
      e11 = Entry.get(phdr_struct.binary[x])

      new_phdr_struct.s_type[i].insert(0, e1)
      new_phdr_struct.offset[i].insert(0,e2)
      new_phdr_struct.vaddr[i].insert(0, e3)
      new_phdr_struct.paddr[i].insert(0, e4)
      new_phdr_struct.fsize[i].insert(0, e5)
      new_phdr_struct.msize[i].insert(0, e6)
      new_phdr_struct.flags[i].insert(0, e7)
      new_phdr_struct.acc_bits[i].insert(0, e8)
      new_phdr_struct.seg_bits[i].insert(0, e9)
      new_phdr_struct.align[i].insert(0, e10)
      new_phdr_struct.binary[i].insert(0, e11)

      i+=1

  #Additional List Editing for Added Segment ******************************
  if(seg_added == True):
    e1 = Entry.get(add_entry_list[0])
    e2 = Entry.get(add_entry_list[1])
    e3 = Entry.get(add_entry_list[2])
    e4 = Entry.get(add_entry_list[3])
    e5 = Entry.get(add_entry_list[4])
    e6 = Entry.get(add_entry_list[5])
    e7 = Entry.get(add_entry_list[6])
    e8 = Entry.get(add_entry_list[7])
    e9 = Entry.get(add_entry_list[8])
    e10 = Entry.get(add_entry_list[9])
    e11 = Entry.get(add_entry_list[10])

    new_phdr_struct.s_type[seg_struct.seg_num-1].insert(0, e1)
    new_phdr_struct.offset[seg_struct.seg_num-1].insert(0,e2)
    new_phdr_struct.vaddr[seg_struct.seg_num-1].insert(0, e3)
    new_phdr_struct.paddr[seg_struct.seg_num-1].insert(0, e4)
    new_phdr_struct.fsize[seg_struct.seg_num-1].insert(0, e5)
    new_phdr_struct.msize[seg_struct.seg_num-1].insert(0, e6)
    new_phdr_struct.flags[seg_struct.seg_num-1].insert(0, e7)
    new_phdr_struct.acc_bits[seg_struct.seg_num-1].insert(0, e8)
    new_phdr_struct.seg_bits[seg_struct.seg_num-1].insert(0, e9)
    new_phdr_struct.align[seg_struct.seg_num-1].insert(0, e10)
    new_phdr_struct.binary[seg_struct.seg_num-1].insert(0, e11)

    #Change 'offset' field to be the sum of previous 'offset' and 'file size'
    c = 0
    original_offset_list.append(c)
    Label(frame2, text = "Segment "+ str(i)).grid(row=i+8)  

    # #CHECKBOX FOR ADDED SEGMENT
    # rvar = IntVar()
    # wvar = IntVar()
    # evar = IntVar()
    # checkbox1 = Checkbutton(frame2, variable=rvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    # checkbox2 = Checkbutton(frame2, variable=wvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    # checkbox3 = Checkbutton(frame2, variable=evar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
    # checkbox1.var = rvar
    # checkbox2.var = wvar
    # checkbox3.var = evar
    # if(check_list[seg_struct.old_seg_num*3].var.get() == 1):
    #   rvar.set(1)
    # if(check_list[seg_struct.old_seg_num*3+1].var.get() == 1):
    #   wvar.set(1)
    # if(check_list[seg_struct.old_seg_num*3+2].var.get()== 1):
    #   evar.set(1)
    # new_check_list.append(checkbox1)
    # new_check_list.append(checkbox2)
    # new_check_list.append(checkbox3)


  # #APPEND CHECKBOX ROW AT END OF LIST FOR EXTRA SEGMENT
  # #Checkboxes
  # rvar = IntVar()
  # wvar = IntVar()
  # evar = IntVar()
  # checkbox1 = Checkbutton(frame2, variable=rvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
  # checkbox2 = Checkbutton(frame2, variable=wvar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
  # checkbox3 = Checkbutton(frame2, variable=evar, onvalue=1, offvalue=0, borderwidth=0, padx=-3)
  # checkbox1.var = rvar
  # checkbox2.var = wvar
  # checkbox3.var = evar
  # new_check_list.append(checkbox1)
  # new_check_list.append(checkbox2)
  # new_check_list.append(checkbox3)    
  # new_check_list[seg_struct.seg_num*3].grid(row=seg_struct.seg_num+6+1, column=7, sticky='nesw')
  # new_check_list[seg_struct.seg_num*3+1].grid(row=seg_struct.seg_num+6+1, column=8, sticky='nesw')
  # new_check_list[seg_struct.seg_num*3+2].grid(row=seg_struct.seg_num+6+1, column=9, sticky='nesw')
    
  for i in range(seg_struct.seg_num):
    #Keep all other fields the same, even if user input entered
    new_phdr_struct.s_type[i].grid(row=i+8, column=1) 
    new_phdr_struct.offset[i].grid(row=i+8, column=2)
    new_phdr_struct.vaddr[i].grid(row=i+8, column=3)
    new_phdr_struct.paddr[i].grid(row=i+8, column=4)
    new_phdr_struct.fsize[i].grid(row=i+8, column=5)
    new_phdr_struct.msize[i].grid(row=i+8, column=6)
    new_phdr_struct.flags[i].grid(row=i+8, column=8)
    new_phdr_struct.acc_bits[i].grid(row=i+8, column=9)
    new_phdr_struct.seg_bits[i].grid(row=i+8, column=10)
    new_phdr_struct.align[i].grid(row=i+8, column=7)
    new_phdr_struct.binary[i].grid(row=i+8, column=11)

    #create delete buttons      
    button_generate = Button(frame2, text = "Delete", width=4, command= partial(create_grid, original_offset_list, frame2, new_val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, False, True, i, new_add_entry_list, new_add_val_list, file_struct_new, entry_struct_new, canvas, seg_struct, initial_phdr_struct, new_phdr_struct)) #modifies/disintegrates new ELF
    button_generate.grid(row=i+8, column=12)

  #RADIO BUTTON CODE
  rb1 = Radiobutton(frame2, text="Modify ELF", variable=rb_var1, value=1)
  rb1.grid(row=0, column=0)
  rb2 = Radiobutton(frame2, text="Disintegrate ELF", variable=rb_var1, value=2, command=partial(grey_grid, original_offset_list, frame2, val_list, elf_fp, elf_filename, elf_filename, is_out_elf_64_bit, elf_header, phdr_table, False, False, blank_list, blank_list, file_struct_new, entry_struct_new, canvas, blank_file_struct, seg_struct, initial_phdr_struct, new_phdr_struct))
  rb2.grid(row=0, column=1)
  rb3 = Radiobutton(frame2, text="Create ELF", variable=rb_var1, value=3).grid(row=0, column=2)

  #LINE CODE - between radiobuttons and ELF header segment
  canvas_a = Canvas(frame2, width=1500, height=10)      #horizontal line above phdr
  canvas_a.grid(row=4+1, column=0, columnspan=12)
  canvas_a.create_line(20, 8, 1550, 8, width=1, dash=(4)) 
  canvas_b = Canvas(frame2, width=1500, height=10)      #horizontal line above elf header
  canvas_b.grid(row=2, column=0, columnspan=12)
  canvas_b.create_line(20, 8, 1550, 8, width=1, dash=(4))
  canvas_c = Canvas(frame2, width=1500, height=10)      #horizontal line under phdr
  canvas_c.grid(row=seg_struct.seg_num+9, column=0, columnspan=12)
  canvas_c.create_line(20, 8, 1550, 8, width=1, dash=(4))


  #Create 'add' button   
  button_generate = Button(frame2, text = "Add", width=4, command= partial(create_grid, original_offset_list, frame2, new_val_list, elf_fp, elf_filename, original_elf_filename, is_out_elf_64_bit, elf_header, phdr_table, True, False, 0, new_add_entry_list, new_add_val_list, file_struct_new, entry_struct_new, canvas, seg_struct, initial_phdr_struct, new_phdr_struct)) #modifies/disintegrates new ELF
  button_generate.grid(row=seg_struct.seg_num+8, column=12)

  #Create 'generate' button                                                                        val_list*, initial_list, phdr_num, check_list, elf_filename*, seg_start_offset*, is_out_elf_64_bit*, frame2
  button_generate = Button(frame2, text = "Generate", width=16, command=lambda: update_grid(new_val_list, original_offset_list, elf_filename, original_elf_filename, is_out_elf_64_bit, frame2, elf_header, phdr_table, seg_added, file_struct_new, entry_struct_new, seg_struct, initial_phdr_struct, new_phdr_struct)) #modifies/disintegrates new ELF
  button_generate.grid(row=0, column=9)
  # button_generate.grid(row=seg_num+10, column=0)

  #Create 'help' button                                                                        
  button_generate = Button(frame2, text = "Help", width=16, command=lambda: pop_up(modify_help_msg))
  button_generate.grid(row=0, column=10)

  #Create 'quit' button
  button_generate = Button(frame2, text = "Quit", width=16, command=lambda: quit()) #disintegrates original ELF
  button_generate.grid(row=0, column=11) 
  return 

#Called after 'Generate' is pressed. Checks for GUI entry validity, then updates lists, then calls 'generate_modified_elf' to create a new ELF file with GUI entries
#############################################################################################
# update_grid - Called after 'Generate' is pressed
#               Does error checking and updates entry values (offset shifts, alignment)
#               Calls 'generate_modified_elf'
#############################################################################################
def update_grid(val_list, original_offset_list, elf_filename, original_elf_filename, is_out_elf_64_bit, frame2, elf_header, phdr_table, segment_added, file_struct, entry_struct, seg_struct, initial_phdr_struct, phdr_struct):

  num_segs_added = seg_struct.num_segs_added
  phdr_num = seg_struct.seg_num

  #ERROR CHECKING ************************************************************************
  hash_counter = 0
  entry_addr_valid = False

  #MAKE SURE GUI ENTRIES ARE HEX
  for i in range (phdr_num):
    try: 
      int(val_list[i*11 + 1].get(), 16)
      int(val_list[i*11 + 4].get(), 16)
      int(val_list[i*11 + 5].get(), 16)
      int(val_list[i*11 + 6].get(), 16)
      int(val_list[i*11 + 7].get(), 16)
      int(val_list[i*11 + 8].get(), 16)
      int(val_list[i*11 + 9].get(), 16)
      if val_list[i*11+2].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
        vaddr = val_list[i*11+2].get()[:-1]
      else: 
        vaddr = val_list[i*11+2].get()
      if val_list[i*11+3].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
        paddr = val_list[i*11+3].get()[:-1]
      else: 
        paddr = val_list[i*11+3].get()
      int(vaddr, 16)
      int(paddr,16)
    except:
      # print i
      pop_up('ERROR: Invalid hex value given')
      elf_error()
      return
    #Count all hash segments. Only one should be present
    if(int(val_list[i*11+8].get(), 16) == 0x2):
      hash_counter += 0x1 
  #Exit out if more than one hash segment is seen
  if(hash_counter > 0x1):
    pop_up('ERROR: Only one hash segment can be used. \n\nThe hash segment is identified with value 0x2 in the Segment Type Bits field')
    elf_error()
    return
  #CHECK FOR VALID HEX ENTRY ADDRESS - must make sure it's hex before making sure it's valid (in range)
  if entry_struct.entry_addr.get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
    tmp_addr = entry_struct.entry_addr.get()[:-1]
    entry_struct.entry_addr.delete(0, 'end')
    entry_struct.entry_addr.insert(0, tmp_addr)
  try:
    int(entry_struct.entry_addr.get(), 16)
  except:
    pop_up('ERROR: Entry address must be a valid hex number')
    elf_error()
    return

  #CHECK TYPE, ENTRY ADDRESS VALIDITY WITH VADDRS, AND ORIGINAL SEGMENT BINARY VALIDITY
  for i in range(phdr_num):
    #Type check
    if not (val_list[i*11].get() == 'load' or val_list[i*11].get() == 'null' or val_list[i*11].get() == 'dynamic' or val_list[i*11].get() == 'interp' or val_list[i*11].get() == 'note' or val_list[i*11].get() == 'shlib' or val_list[i*11].get() == 'phdr' or val_list[i*11].get() == 'loproc' or val_list[i*11].get() == 'hiproc'): 
      pop_up('WARNING: Invalid Type for some segment \n\nDefault Type will be load')
    #Entry point address check - must be between vaddr and filessize for at least ONE of the segments
    if val_list[i*11+2].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
      vaddr = int(val_list[i*11+2].get()[:-1], 16)
    else: 
      vaddr = int(val_list[i*11+2].get(), 16)
    filesz = int(val_list[i*11+4].get(), 16)
    if (int(entry_struct.entry_addr.get(), 16) >= vaddr and int(entry_struct.entry_addr.get(), 16) < filesz + vaddr):
      entry_addr_valid = True
  if(entry_addr_valid == False):
    pop_up('ERROR: Invalid entry point address. \n\nMust be between a virutal address and file size')
    elf_error()
    return

  #BINARY CHECK FOR SEGMENTS - make sure binaries exist and are valid
  for i in range(num_segs_added):
    #BINARY VALIDITY FOR ORIGINAL SEGMENTS
    if(i <= phdr_num - num_segs_added): #BINARY VALIDITY FOR ORIGINAL SEGMENTS
      if (val_list[i*11+10].get()):  #if binary given in original segment, check if binary is valid
        if not (os.path.isfile(val_list[i*11+10].get())):
          pop_up('ERROR: Binary does not exist in some segment. \n\nFile must be in working directory')
          elf_error()
          return
    #BINARY VALIDITY FOR ADDED SEGMENTS
    else:
      path_idx = (phdr_num - num_segs_added + i)*11
      if not (val_list[path_idx+10].get()):
        pop_up('ERROR: Binary not given in an added segment')
        elf_error()
        return
      else: #binary given, make sure it's valid
        if not (os.path.isfile(val_list[path_idx+10].get())):
          pop_up('ERROR: Binary does not exist for some added segment')
          elf_error()
          return

  #ADDRESS OVERLAP CHECK
  for i in range(phdr_num):  #iterate through segments to compare
    for j in range (phdr_num):
      if val_list[i*11+2].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
        vaddr_start = int(val_list[i*11+2].get()[:-1], 16)
      else: 
        vaddr_start = int(val_list[i*11+2].get(), 16)
      if val_list[i*11+3].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
        paddr_start = int(val_list[i*11+3].get()[:-1], 16)
      else: 
        paddr_start = int(val_list[i*11+3].get(), 16)
      if val_list[j*11+2].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
        tmp_vaddr_start = int(val_list[j*11+2].get()[:-1], 16)
      else: 
        tmp_vaddr_start = int(val_list[j*11+2].get(), 16)
      if val_list[j*11+3].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
        tmp_paddr_start = int(val_list[j*11+3].get()[:-1], 16)
      else: 
        tmp_paddr_start = int(val_list[j*11+3].get(), 16)

      # vaddr_start = roundup(vaddr_start, int(val_list[i*11+9].get(), 16))       #vaddr is aligned
      # paddr_start = roundup(paddr_start, int(val_list[i*11+9].get(), 16))       #paddr is aligned
      # tmp_vaddr_start = roundup(tmp_vaddr_start, int(val_list[j*11+9].get(), 16))   #tmp_vaddr is aligned
      # tmp_paddr_start = roundup(tmp_paddr_start, int(val_list[j*11+9].get(), 16))   #tmp_paddr is aligned
      memsize = int(val_list[i*11 + 5].get(), 16)
      filesz = int(val_list[i*11 + 4].get(), 16)
      tmp_memsize = int(val_list[j*11 + 5].get(), 16)
      tmp_filesz = int(val_list[j*11 + 4].get(), 16)
      vaddr_end = vaddr_start + memsize             #Should only consider mem size, not file
      # vaddr_end = vaddr_start + memsize + filesz
      paddr_end = paddr_start + memsize
      # paddr_end = paddr_start + memsize + filesz
      tmp_vaddr_end = tmp_vaddr_start + tmp_memsize
      # tmp_vaddr_end = tmp_vaddr_start + tmp_memsize + tmp_filesz
      tmp_paddr_end = tmp_paddr_start + tmp_memsize
      # tmp_paddr_end = tmp_paddr_start + tmp_memsize + tmp_filesz
      if not(i == j): #THERE CAN BE OVERLAP AS LONG AS NOT 'BEING USED' AT THE SAME TIME??
        if((vaddr_start < tmp_vaddr_end and vaddr_start >= tmp_vaddr_start) or (vaddr_end < tmp_vaddr_end and vaddr_end > tmp_vaddr_start) or (vaddr_start >= tmp_vaddr_start and vaddr_end < tmp_vaddr_end) or (vaddr_start <= tmp_vaddr_start and vaddr_end > tmp_vaddr_end)): # FIND OVERLAP LOGIC
          pop_up_overlap('ERROR: Virtual address and mem size overlaps with segments', i, j)
          # print "y1", hex(vaddr_start)
          # print "y2", hex(vaddr_end)
          # print "x1", hex(tmp_vaddr_start)
          # print "x2", hex(tmp_vaddr_end), "\n"
          elf_error()
          return  
        if((paddr_start < tmp_paddr_end and paddr_start >= tmp_paddr_start) or (paddr_end < tmp_paddr_end and paddr_end > tmp_paddr_start) or (paddr_start >= tmp_paddr_start and paddr_end < tmp_paddr_end) or (paddr_start <= tmp_paddr_start and paddr_end > tmp_paddr_end)): # FIND OVERLAP LOGIC
          pop_up_overlap('ERROR: Physical address and mem size overlaps with segments', i, j)
          # print "y1", hex(paddr_start)
          # print "y2", hex(paddr_end)
          # print "x1", hex(tmp_paddr_start)
          # print "x2", hex(tmp_paddr_end), "\n"
          elf_error()
          return


  #GUI, LIST, SOME ELF HEADER UPDATING ****************************************************************
  # file pointer for ELF 
  elf_fp = elf_gen_tools.OPEN(elf_filename, "rb")
  seg_num = phdr_num
  old_seg_num = phdr_num #used to check indexes since seg_num changes in this function
  change_var = False
  i=0
  for i in range(phdr_num):

    #UPDATE ENTRY LIST WITH GUI VALUES
    tmp_type = val_list[i*11].get()
    phdr_struct.s_type[i].delete(0, 'end')  
    phdr_struct.s_type[i].insert(0, tmp_type)        #type

    #offset change
    if(change_var == False):
      tmp_offset = int(val_list[i*11+1].get(), 16)
      tmp_offset = roundup(tmp_offset, int(entry_struct.segalign.get(), 16)) #BYTE ALIGN THE OFFSET
      # tmp_offset = roundup(tmp_offset, SEGMENT_ALIGN) #16 BYTE ALIGN
      phdr_struct.offset[i].delete(0, 'end')  
      phdr_struct.offset[i].insert(0, hex(tmp_offset))  #offset
    else:
      # val_list[i*11+1] = shift_offset
      phdr_struct.offset[i].delete(0, 'end')  
      phdr_struct.offset[i].insert(0, hex(shift_offset))  #offset
    cur_offset = int(phdr_struct.offset[i].get(), 16)   #MUST be assigned after current offset has been set above
    cur_filesz = int(val_list[i*11+4].get(), 16)   

    #VADDR CHECK
    if val_list[i*11+2].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers  VADDR IS ALIGNED WITH PHDR 'ALIGNMENT' FIELD ********************
      # tmp_vaddr = roundup(int(val_list[i*11+2].get()[:-1], 16), int(val_list[i*11+9].get(), 16))  #ALIGN ADDRESSS
      tmp_vaddr = val_list[i*11+2].get()[:-1]
    else: 
      # tmp_vaddr = roundup(int(val_list[i*11+2].get(), 16), int(val_list[i*11+9].get(), 16)) #ALIGN ADDRESSS
      tmp_vaddr = val_list[i*11+2].get()
    phdr_struct.vaddr[i].delete(0, 'end')   
    if tmp_vaddr[-1] == "L":  #check for 'L' bug after address alignment
      tmp_vaddr = tmp_vaddr[:-1]
    phdr_struct.vaddr[i].insert(0, tmp_vaddr)  #vaddr
    
    #PADDR CHECK
    if val_list[i*11+3].get()[-1] == "L":    #fixes Python bug - trailing found 'L' in large hex numbers
      # tmp_paddr = roundup(int(val_list[i*11+3].get()[:-1], 16), int(val_list[i*11+9].get(), 16))  #ALIGN ADDRESSS
      tmp_paddr = val_list[i*11+3].get()[:-1]
    else: 
      # tmp_paddr = roundup(int(val_list[i*11+3].get(), 16), int(val_list[i*11+9].get(), 16))  #ALIGN ADDRESSS
      tmp_paddr = val_list[i*11+3].get()
    phdr_struct.paddr[i].delete(0, 'end')  
    if tmp_paddr[-1] == "L":    #check for 'L' bug after address alignment
      tmp_paddr = tmp_paddr[:-1]
    phdr_struct.paddr[i].insert(0, tmp_paddr)  #paddr

    tmp_size = int(val_list[i*11+4].get(), 16)  
    phdr_struct.fsize[i].delete(0, 'end')  
    phdr_struct.fsize[i].insert(0, hex(tmp_size))  #filesize* convert input from entry (string) into hex value 

    tmp_msize = int(val_list[i*11+5].get(), 16)
    phdr_struct.msize[i].delete(0, 'end')  
    phdr_struct.msize[i].insert(0, hex(tmp_msize))  #memsize

    tmp_pflag = int(val_list[i*11+6].get(), 16)
    phdr_struct.flags[i].delete(0, 'end')  
    phdr_struct.flags[i].insert(0, hex(tmp_pflag)) #pflag bits

    tmp_abits = int(val_list[i*11+7].get(), 16)
    phdr_struct.acc_bits[i].delete(0, 'end')  
    phdr_struct.acc_bits[i].insert(0, hex(tmp_abits)) #access type bits 

    tmp_sbits = int(val_list[i*11+8].get(), 16)
    phdr_struct.seg_bits[i].delete(0, 'end')  
    phdr_struct.seg_bits[i].insert(0, hex(tmp_sbits)) #segment type bits 

    tmp_align = int(val_list[i*11+9].get(), 16)
    phdr_struct.align[i].delete(0, 'end')  
    phdr_struct.align[i].insert(0, hex(tmp_align))  #align

    tmp_bin = val_list[i*11+10].get()
    phdr_struct.binary[i].delete(0, 'end')  
    phdr_struct.binary[i].insert(0, tmp_bin)  #binary

    #Logic for offset changes
    if(i < phdr_num-1): #index before the last row
      next_offset = int(phdr_struct.offset[(i+1)].get(), 16)
      # print "i ", i   
      # print "cur offset", hex(cur_offset)
      # print "cur filesz ", hex(cur_filesz)
      # print "next offset", hex(next_offset), "\n"
      if(cur_offset + cur_filesz > next_offset): #must shift offsets down
        change_var = True
        shift_offset = cur_offset + cur_filesz
        shift_offset = roundup(shift_offset, int(entry_struct.segalign.get(), 16)) #VARIABLE BYTE ALIGN 
        # shift_offset = roundup(shift_offset, SEGMENT_ALIGN) #16 BYTE ALIGN
      else:
        change_var = False

  #Update ELF header's Entry Address and update GUI

  tmp_addr = int(entry_struct.entry_addr.get(), 16)
  elf_header.e_entry = tmp_addr
  entry_struct.entry_addr.delete(0, 'end')
  entry_struct.entry_addr.insert(0, hex(tmp_addr))

  #Update Segment Alignment with GUI value
  tmp_segalign = int(entry_struct.segalign.get(), 16)
  entry_struct.segalign.delete(0, 'end')
  entry_struct.segalign.insert(0, hex(tmp_segalign))



  #CALL FUNCTION TO CREATE MODIFIED ELF
  elf_gen.create_modifided_elf(original_offset_list, elf_fp, phdr_table, elf_header, is_out_elf_64_bit, segment_added, val_list, original_elf_filename, file_struct, entry_struct, seg_struct, initial_phdr_struct, phdr_struct)
                                                                                              #segment_added
  elf_fp.close()
  return  

#############################################################################################
# disassemble_elf - Parses an ELF file and places sections of file into different binaries
#                    Called by 'grey_grid'
#############################################################################################
def disassemble_elf(elf_fp, elf_header, is_out_elf_64_bit, file_struct, phdr_struct):
  elf_info_out_json = None #let elg_gen.disassemble_elf_raw use default out json
  elf_gen.disassemble_elf_raw(elf_fp, file_struct.input_file.get(), elf_info_out_json, file_struct.output_file.get())
  return 0

##############################################################################
# main - Parses script arguments and runs elf_gen tool
##############################################################################
if __name__ == "__main__":
  if sys.version_info < MINIMUM_SUPPORTED_PYTHON_VERSION:
    print("Must use Python " + str(MINIMUM_SUPPORTED_PYTHON_VERSION) + " or greater")
    sys.exit(1)
  #parse arguments
  parser = OptionParser(usage='usage: %prog [options] arguments')

  parser.add_option("-f", "--first_filepath",
                    action="store", type="string", dest="elf_input",
                    help="First ELF file to merge.")

  parser.add_option("-c", "--cfg",
                    action="store", type="string", dest="json_file",
                    help="JSON file to create ELF from")

  parser.add_option("-t", "--tools_path",
                    action="store", type="string", dest="tools_path",
                    help="Path to tools directory containing dependent *.py scripts.")

  (options, args) = parser.parse_args()

  # Dependent Tools (elf_gen, elf_gen_tools.py etc.) path directory 
  if options.tools_path and os.path.isdir(options.tools_path):
    options.tools_path = os.path.abspath(options.tools_path)
  else:
    options.tools_path = os.getcwd()
  
  if options.json_file: #Make a new ELF with data from config file
    # parse json_file and create ELF file
    elf_gen.config_parser(options.json_file, True) 
    frame2.grid(row=0, column=0)
    Label(frame2, text='2')
    frame2.grid_forget()
    frame_start.pack(side='top', fill='both', expand=True)
    Label(frame_start, text='3')
    config_file = elf_gen.findConfigFile(options.json_file)
    create_frame_start(config_file)
    if os.path.isfile(options.json_file):
      call_gui(config_file, frame2)
  else:
    frame2.grid(row=0, column=0)
    Label(frame2, text='2')
    frame2.grid_forget()
    frame_start.pack(side='top', fill='both', expand=True)
    Label(frame_start, text='3')
    create_frame_start(options.elf_input)
    if not options.elf_input:
      init_gui(frame2) #function to create GUI
    else:
      call_gui(options.elf_input, frame2) #function to create GUI
  
  exit(0)