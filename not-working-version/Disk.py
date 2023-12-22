class Disk():
	def __init__(self):
		self.content = [] # this will contain all bytes of my Disk.
		self.freeSpace = 0 #total free/empty cluster inside my image disk
		
		self.fileSystemSTRING = "" #this will contain file system name.
		
		self.imgDimBytes = 0 #image size in bytes
		self.imgDimKB = 0 #image size in kilobytes
		
		self.bytesPerSector = 0 #read 0x0b and 0x0c from boot block. 0x0b is the least significant byte
		self.totalSECTORS = 0 #store total sectors of my disk
		
		self.SectorPerCluster = 0 #number of sector for each cluster
		self.clusterSize = 0 #size of each cluster. 
		
		self.sizeBOOT = 0 #size of boot block. check 0x0e and 0x0f
		self.endBOOT = 0 #where boot block ends.
		
		self.nrFAT = 0 #number of file allocation table. Usually they are at least 2. Check 0x10 on boot block.
		self.sizeFAT = 0 #size of a single FAT copy
		self.startFAT = 0 #where FAT starts. Usually sector 1
		self.endFAT = 0 #where last FAT ends.
		
		self.totalENTRIES = 0 #number of directory the disk can have statically inside root directory 
		self.sizeROOT = 0
		self.startROOT = 0 #where root starts.
		self.endROOT = 0 #where root ends.
		self.totalClusters = 0 #total number of clusters
		
		self.sizeDATA = 0
		self.startDATA = 0 #where area data starts.
		self.endDATA = 0 #where area data ends.

		self.constantValue = 0 #it's a constant mandatory to find in which cluster are stored file fragments. This is necessary because cluster 0 and 1 don't exist.
		self.FATentry = 0 #this is used to count which entry of FATtable I'm checking. Each entry in FAT table use 2bytes to store the pointer to a cluster.
		
	def mediaDescriptor(self, index): #print different Output for few disk types.
		HEXvalue = hex(self.content[index])
		print("Media Descriptor: ", HEXvalue)
		if HEXvalue == "0xfc" or HEXvalue == "0xfd" or HEXvalue == "0xfe" or HEXvalue == "0xfb" or HEXvalue == "0xf9" or HEXvalue == "0xf0":
			print('Type of media: floppy disk')
		elif HEXvalue == "0xfa":
			print('Type of media: RAMdisk')
		elif HEXvalue == "0xf8":
			print('Type of media: Hard Disk - DOS Version 2.0')
	
	#This useful method will be used to convert groups of hex values to an integer. This will be used often inside all the program!
	def HEXstringToDEC(self, start, stop, step): #convert HEX value to DEC value to find the position inside content list.
		catResult = ""
		for x in range (start, stop, step):
			cleanHEX = hex(self.content[x])[2:].zfill(2) #clean HEX from '0x' AND adding zero until I reach minimum width using .ZFILL(2)
			catResult += cleanHEX
		return int(catResult, 16) #HEX to DEC
	
	#This method will be used to clean HEXvalues. I need to have hex values with 2 digits. I.E. 0x00 must be '00' 
	def cleanHEX (self, hexValue):
		return hexValue[2:].zfill(2)
		
	#I'll use this method to add +1 to hex value because I need to search in FAT table the next cluster piece.
	def concatenateHEXandADDone(self, least, most): #This method will receive clean HEX. This means numbers without '0x' part and padded with 0 on the left.
		concatenate = str(most) + str(least) #1. concatenate them
		integer = int(concatenate, 16) #2. converting hexValue into integer
		integer += 1 #3. summing 1 to int value
		hexResult = hex(integer)[2:].zfill(4) #4. converting it to hex again
		#print ("least", hexResult[2:])
		#print ("most", hexResult[0:2])
		return hexResult[2:], hexResult[0:2] #least, most
	
	def splitDECintoHEXandConvertToDEC(self, DECvalue):
		convertHEX = hex(DECvalue)[2:].zfill(4)
		splitHEXandConvertDEC1 = int(convertHEX[2:], 16)
		splitHEXandConvertDEC2 = int(convertHEX[:2], 16)
		return  splitHEXandConvertDEC1, splitHEXandConvertDEC2		#least, most
		

	#This method read hex values and copy values to a list. This will be useful when I have to move a cluster to another position.
	def cutCluster(self, firstByte, clusterContent): #cut cluster content and I'm ready to paste it in another cluster position.
		clusterContent[:] = []
		for x in range(firstByte, firstByte + (self.bytesPerSector * self.SectorPerCluster)):
			clusterContent.append(self.content[x])
			self.content[x] = 0
		return clusterContent
		
	def pasteCluster(self, firstByte, clusterContent): #startingByte is the first byte in which I have to copy all the cluster.
		for element in clusterContent:
			self.content[firstByte] = element
			firstByte += 1

	#This method will be used to find in which position we are inside FAT. content works with positions, but we don't know in which position is a cluster number..
	def indexFATtable(self, x):
		pass
	
	#This method will be used to check inside FAT table for free spaces and to decide if I have to move fragmented files.
	def readFATtable (self, leastSignificant, mostSignificant):
		freeFATspace = False #this becomes true if I find empty space in FAT table. And I'll use that space to defrag and sort my files.
		nextLeastSignificant, nextMostSignificant =  self.concatenateHEXandADDone (leastSignificant, mostSignificant)
		
		#this "for" check ALL FAT table, from first group of bytes to last one. Step 2 because FAT table is made up of groups of 2 bytes!
		for x in range((((self.startFAT+1)* 512) - 512), (self.startFAT + 1 + self.sizeFAT)* 512 - 512 ,2): 
			#from now I need to count how many "00" values I find BEFORE finding next cluster fragment... in this way I can decide if I need to move file or not.
			if hex(self.content[x])[2:].zfill(2) == '00' and hex(self.content[x+1])[2:].zfill(2) == '00' and freeFATspace == False:
				freeFATspace = True
			elif hex(self.content[x])[2:].zfill(2) == nextLeastSignificant and hex(self.content[x+1])[2:].zfill(2) == nextMostSignificant and freeFATspace == True:
				print("Si può spostare il file prima di questa posizione attuale.")
				
				
				self.defragFILE()
				print("Spostato.")
				break
	
	def tryMoveFirstCluster(self, leastSignificant, mostSignificant, clusterValueDEC):
		#I.E. cluster 0x07. I don't need to check all FAT table, but my "for" loop must stop to search '00 00' free spaces if I go over the offset 0x10.
		self.FATentry = 0
		copyCluster = []
		
		#this "for" check ALL FAT table, from first group of bytes to last one. Step 2 because FAT table is made up of groups of 2 bytes!
		for x in range((((self.startFAT+1)* 512) - 512), (self.startFAT + 1 + self.sizeFAT)* 512 - 512 ,2): 
			self.FATentry += 1
			if self.FATentry >= clusterValueDEC: #In this case file cannot be moved. 
				return 0, 0 #in this way I avoid to spend resources to search all FAT table when it is not needed.
			
			#If there is a cluster number inside FAT table equal to '00 00' then I can move my file there.
			if self.content[x] == 0 and self.content[x+1] == 0 and self.content[x+2] == 0 and self.content[x+3] == 0: #simple case. File can be moved.
				
				 #+1 because my list starts at index 0. *512 to find all bytes and -512 because first list position is 0.
				firstBytefirstCluster = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
				copyCluster = self.cutCluster(firstBytefirstCluster , copyCluster) #read all the first cluster. Now I am ready to move it if needed.
				
				#print(copyCluster[:16]) #COPY CLUSTER HA PRESO IL FILE CORRETTAMENTE.
				print(self.content[x])
				print(self.content[x+1])
				
				self.content[x] = 255 #FF
				self.content[x+1] = 255 #FF
				
				firstBytefirstCluster = ((((self.FATentry * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512 
				self.pasteCluster(firstBytefirstCluster, copyCluster) #write cluster in the new position.
				
				leastUpdated, mostUpdated = self.splitDECintoHEXandConvertToDEC(self.FATentry) #convert DEC value to HEX and split hex in two parts to write it on FAT table.
				return leastUpdated, mostUpdated
				
			#Hard case. File can be moved. This condition means that we have a free cluster and after that there is another file. So we have to move it and defrag.
			elif self.content[x] == 0 and self.content[x+1] == 0 and self.content[x+2] != 255 and self.content[x+3] != 255 and self.content[x+2] != 0 and self.content[x+3] != 0: 
				
				

	def tryMoveOtherCluster(self,  leastSignificant, mostSignificant, clusterValueDEC):
		pass
	
	def defragFILE(self): #move all fragments of a file and update FAT table.
		pass

	#This method will be used to clone first FAT. I.E. if a filesystem has more of 1 FAT table, I need to copy values to the others table in order to not break FS.
	def cloneFAT (self):
		pass
	
	# ------------------------ Core program, This will start defragmentation ----------------------------#
	def startDefrag(self): 
		clusterNumHEX = ["",""]
		clusterContent = []
		
		print("Defragmentation is Running..")
		#root directory has 32 bytes for each entry. It contains top level directories and files and they have static positions. I cannot move them but I start my defragmentation reading starting cluster number of these files. I will not touch/move deleted files because they have not assigned space in data area and I don't care about them. I will read all the root directory and every time I find a new occurency of a file, I'll go to defrag it.
		
		for rootBytes in range (((self.startROOT +1)* 512) - 512, ((self.endROOT+1) * 512) - 512, 32): #analyze all root entries. Read important note to understand this "for".
			if self.content[rootBytes + 0] != 229 and self.HEXstringToDEC(rootBytes+31, rootBytes+27 ,-1) == 0 and self.HEXstringToDEC(rootBytes+27, rootBytes+25 ,-1) != 0: 
			#FOLDER - If file has not been deleted AND it hasn't a size AND it has first cluster number, it's a FOLDER!
				pass
				#print("cartella!")
			elif self.content[rootBytes + 0] != 229 and self.HEXstringToDEC(rootBytes+31, rootBytes+27 ,-1) != 0 and self.HEXstringToDEC(rootBytes+27, rootBytes+25 ,-1) != 0: 
			#FILE - else if file has not been deleted AND it has a size AND it has a cluster number, it's a FILE!
				
				#1. Read first cluster number in HEX and in DEC. HEX is needed in FAT table, DEC is needed in data area to find sector.
				clusterNumHEX[0] = self.cleanHEX(hex(self.content[rootBytes + 26])) #least Significant byte
				clusterNumHEX[1] = self.cleanHEX(hex(self.content[rootBytes + 27])) #most Significant byte
				clusterNumDEC = self.HEXstringToDEC(rootBytes+27, rootBytes+25 ,-1) #decimal value will be used to find sector in which I can find data file.
				
				print(clusterNumHEX[0])
				print(clusterNumHEX[1])
				
				#1.1 File size? Delete or not? Is it needed?
				#fileSizeBytes = self.HEXstringToDEC(rootBytes+31, rootBytes+27 ,-1) #this is size of the file in bytes. WIth this value I can calculate how many cluster it is using.
				#numOfClusters = fileSizeBytes //self.clusterSize #number of clusters per file.
				
				#1.5 - Try to move first cluster number if possible.
				leastUpdated, mostUpdated = self.tryMoveFirstCluster(clusterNumHEX[0], clusterNumHEX[1], clusterNumDEC) #[0] is least significant value, [1] most significant
				
				if leastUpdated != 0 or mostUpdated != 0: #overwrite first cluster position in root directory. If I have moved first cluster, try to move others.
					self.content[rootBytes + 26] = leastUpdated			#least
					self.content[rootBytes + 27] = mostUpdated			#most
					print("first cluster moved.")
					
					clusterNumHEX[0] = self.cleanHEX(hex(self.content[rootBytes + 26])) #least Significant byte
					clusterNumHEX[1] = self.cleanHEX(hex(self.content[rootBytes + 27])) #most Significant byte
					clusterNumDEC = self.HEXstringToDEC(rootBytes+27, rootBytes+25 ,-1) #decimal value will be used to find sector in which I can find data file.
					self.tryMoveOtherCluster(clusterNumHEX[0], clusterNumHEX[1], clusterNumDEC) #[0] is least significant value, [1] most significant
				else:
					print("first cluster cannot be moved. Let's search for other fragmented files.") 
					
				break
				
				
				
				
				
				
				
				#2. Read FAT table and check if file need to be defraggled.
				self.readFATtable(clusterNumHEX[0], clusterNumHEX[1]) #[0] is least significant value, [1] most significant
				
				#3. ONLY if file need to be defraggled, start reading clusters and copy that to the right position.
				 #+1 because my list starts at index 0. *512 to find all bytes and -512 because first list position is 0.
				#firstBytefirstCluster = ((((clusterNumDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
				#self.cutCluster(firstBytefirstCluster , clusterContent) #read all the first cluster. Now I am ready to move it if needed.
				
				
				
				
				
				#self.cloneFAT()
				#TODO - dopo aver finito di deframmentare devo clonare la prima FAT sulle altre FAT table.
				#aggiungere il controllo su 0x2e?
				
				
				
				
				
				
				
				
				
				
				

