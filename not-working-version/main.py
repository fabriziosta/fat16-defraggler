from tkinter import *
from tkinter import ttk
from tkinter import filedialog #this import is necessary to call file manager.

def openFile():
	path = filedialog.askopenfilename(initialdir = "C:/Users",title = "Choose FAT16 image Disk", filetypes = (("img files","*.img"),("all files","*.*")))
	fileNameToShow = "..." + path[len(path)//2:]
	filename.set(fileNameToShow)
	if path[-4] == '.' and path[-3] == 'i' and path[-2] == 'm' and path[-1] == 'g':
		Description.set('File .img fully loaded. Checking free space...')
		#avviare qui controllo spazio libero
	else:
		Description.set('Disk Image not valid. Please select another file image.')
	
	return path

def Close():
	root.destroy()
	
def disable_buttons(parent):
	for child in parent.winfo_children():
		child.state(["disabled"])

def startDefrag():
	disable_buttons(frame)

########################## ROOT #############################
root = Tk()
root.title("SupDefrag FAT16") #window title.
root.geometry("500x180") #set window size.
#root.resizable(width=False, height=False)

########################## FRAME #############################
frame = ttk.Frame(root, padding = "5 5 10 10") #frame definition
frame.grid(column = 0, row = 0)

########################## ROW 0 #############################
filename = StringVar()
textBox = ttk.Entry(frame, width = 65, textvariable = filename, state='disabled') 
textBox.grid(row = 0)
#textBox.focus()
ttk.Button(frame, text="Open", command = openFile).grid(column = 1, row = 0)

########################## ROW 1 #############################
Description = StringVar()
Description.set('Press "Open" and select an ".img" FAT16 disk image')
ttk.Label(frame, textvariable = Description).grid(row = 1)
#textvariable = Description DA INSERIRE AL POSTO DELL'ATTRIBUTO TEXT PER FAR SPUNTARE UNA NUOVA STRINGA TRAMITE BOTTONE.

########################## ROW 2 #############################
progressBar = ttk.Progressbar(frame, orient="horizontal", length=250, mode="determinate")
progressBar.grid(column = 0, row = 2)
progressBar.start()

########################## ROW 3 #############################
Progress = 'Progress: 0/0'
ttk.Label(frame, textvariable = Progress).grid(column = 0, row = 3)
#use "text" instead of "textvariable" to show string normal text.

########################## ROW 4 #############################
defragButton = ttk.Button(frame, text="Defrag", command = startDefrag , state='disabled').grid(column = 0, row = 4)
closeButton = ttk.Button(frame, text="Close", command = Close).grid(column = 1, row = 4)

for child in frame.winfo_children(): child.grid_configure(padx = 5, pady = 5) #shortcut for setting all widgets padding children 
root.mainloop()
