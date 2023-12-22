from tkinter import *
from tkinter import ttk
from tkinter import filedialog #import necessary for calling file manager.
from tkinter import messagebox #import necessary for quitting program correctly.

from Disk import *
from Defrag import *

def openFile():
	global path
	global myDisk
	global progressBar
	defragButton['state'] = 'disabled' #Every time user click on open button, disable "Defrag" button again.

	path = filedialog.askopenfilename(initialdir = "C:/Users",title = "Choose FAT16 image Disk", filetypes = (("img files","*.img"),("all files","*.*")))
	fileNameToShow = ".." + path[len(path)//2:]
	filename.set(fileNameToShow)
	if len(path) > 4 and path[-4] == '.' and path[-3] == 'i' and path[-2] == 'm' and path[-1] == 'g':
		myDisk = Disk() #declaring a new Disk object every time user select another .img disk image to avoid malfunctioning.
		read(path, myDisk)
		if len(myDisk.content) > 1000:
			info(path, myDisk)
			if 'FAT16' in myDisk.fileSystemSTRING:
				if freeSpace(myDisk) == True:
					
					stringToPrint = "You can defrag! You have " + str(myDisk.SpacePercentage) + "% free space."
					Description.set(stringToPrint)
					defragButton['state'] = 'normal' #enable defrag button
					progressBar = ttk.Progressbar(frame, variable = step, length=250, maximum = (myDisk.sizeFAT *512))
					progressBar.grid(column = 0, row = 2)
					
				else:
					Description.set("You cannot defrag this disk! You have not enough free space.") 
			else:
				Description.set('Filesystem not valid. Please select another file image.')
		else:
			Description.set('Image Corrupted. Please select another file image.')
	else:
		Description.set('Disk Image not valid. Please select another file image.')

def Close():
	if messagebox.askokcancel("Quit", "Do you want to quit?\nAny process in execution will be aborted."):
		root.destroy()

def Start():
	for child in frame.winfo_children(): #Disable all buttons
		child.state(["disabled"])
	
	step.set(0)
	Progress.set('Progress 0/0')
	myDisk.startDefrag(progressBar, step, progressText, Progress)
	write(myDisk ,'Defragmented_image.img')
	
	Description.set("Defragmentation Completed.")

########################## ROOT #############################
root = Tk()
root.title("SupDefrag FAT16") #window title.
root.geometry("500x180") #set window size.
root.resizable(width=False, height=False)

########################## FRAME #############################
frame = ttk.Frame(root, padding = "5 5 10 10") #frame definition
frame.grid(column = 0, row = 0)

########################## ROW 0 #############################
filename = StringVar()
ttk.Entry(frame, width = 65, textvariable = filename, state='disabled').grid(row = 0)
ttk.Button(frame, text="Open", command = openFile).grid(column = 1, row = 0)

########################## ROW 1 #############################
Description = StringVar()
Description.set('Press "Open" and select an ".img" FAT16 disk image')
ttk.Label(frame, textvariable = Description).grid(row = 1)
#use "text" instead of "textvariable" to show string normal text.

########################## ROW 2 #############################
step = IntVar()
ttk.Progressbar(frame, variable = step, length=250).grid(column = 0, row = 2)

########################## ROW 3 #############################
Progress = StringVar()
progressText = ttk.Label(frame, textvariable = Progress)
progressText.grid(row = 3)

########################## ROW 4 #############################
defragButton = ttk.Button(frame, text="Defrag", command = Start , state='disabled')
defragButton.grid(column = 0, row = 4)
ttk.Button(frame, text="Close", command = Close).grid(column = 1, row = 4)

#######################################################
for child in frame.winfo_children(): child.grid_configure(padx = 5, pady = 5) #shortcut for setting all widgets padding children 
root.protocol("WM_DELETE_WINDOW", Close) #manage click on "x" to close window and show popup.
root.mainloop() 
