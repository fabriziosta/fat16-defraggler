class Disk():
	def __init__(self):
		self.content = [] #This will contain all bytes of my Disk in DECIMAL.
		self.freeSpace = 0 #Total of free/empty cluster inside my image disk.
		self.SpacePercentage = 0 #Free space in percentage inside disk image.
		
		self.fileSystemSTRING = "" #This will contain file system name.
		
		self.imgDimBytes = 0 #Image size in bytes.
		self.imgDimKB = 0 #Image size in kilobytes.
		
		self.bytesPerSector = 0 #Read 0x0b and 0x0c from boot block. 0x0b is the least significant byte.
		self.totalSECTORS = 0 #Store total sectors of my disk.
		
		self.SectorPerCluster = 0 #Number of sector for each cluster.
		self.clusterSize = 0 #Size of each cluster. 
		
		self.sizeBOOT = 0 #Size of boot block. check 0x0e and 0x0f.
		self.endBOOT = 0 #Where boot block ends.
		
		self.nrFAT = 0 #Number of file allocation table. Usually they are at least 2. Check 0x10 on boot block.
		self.sizeFAT = 0 #Size of a single FAT copy.
		self.sizeFATinBYTES = 0 
		self.startFAT = 0 #Where FAT starts. Usually sector 1.
		self.endFAT = 0 #Where last FAT ends.
		
		self.totalENTRIES = 0 #Number of directory the disk can have statically inside root directory.
		self.sizeROOT = 0
		self.startROOT = 0 #Where root starts.
		self.endROOT = 0 #Where root ends.
		self.totalClusters = 0 #Total number of clusters
		
		self.sizeDATA = 0
		self.startDATA = 0 #Where area data starts.
		self.endDATA = 0 #Where area data ends.

		# ------------------- VARIABLE USED INSIDE DEFRAGGLER ---------------------- #
		#It's a constant mandatory to find in which cluster are stored file fragments. This is necessary because cluster 0 and 1 don't exist.
		self.constantValue = 0 
		#This is used to count which entry of FATtable I'm checking. Each entry in FAT table use 2bytes to store the pointer to a cluster.
		self.FATentryDEC = 0 
		#This list store index of every FAT entry. In position 0 it stores LEAST, in position 1 it will store MOST significant byte. They will be in DEC because bytearray is made up of int values.
		self.FATindex = [0,0] 
		#This list store index of next FAT entry. For next entry I mean next non-empty cluster, with value "FF FF" that I need to recognize position to move into another empty and previous cluster.
		self.nextFATindex = [0,0]
		#this list will store fragments when I need to move some clusters to sort a file.
		self.storeFile = [] 
		self.storeFileIndex = -1 #This is storeFile index, it will be increased when I find "FF FF" and I will pop a index when I finished to copy an entire file.
		#This variable is used to store array list index position for next fragment, only when file is fragmented. 
		self.nextIndexFragmentToMove = 0
		#This boolean will be used to check if a file chain is fragmented or not.
		self.fragmentedFile = False 
		#I'll use this variable to increase and update progress bar inside my main "for" loop.
		self.updateProgressBar = 0

	#Print different Output for few disk types.
	def mediaDescriptor(self, index): 
		HEXvalue = hex(self.content[index])
		print("Media Descriptor: ", HEXvalue)
		if HEXvalue == "0xfc" or HEXvalue == "0xfd" or HEXvalue == "0xfe" or HEXvalue == "0xfb" or HEXvalue == "0xf9" or HEXvalue == "0xf0":
			print('Type of media: floppy disk')
		elif HEXvalue == "0xfa":
			print('Type of media: RAMdisk')
		elif HEXvalue == "0xf8":
			print('Type of media: Hard Disk - DOS Version 2.0')

	#This useful method will be used to convert groups of hex values to an integer.
	#Convert HEX value to DEC value to find the position inside content list.
	def HEXstringToDEC(self, start, stop, step): 
		catResult = ""
		for x in range (start, stop, step):
			cleanHEX = hex(self.content[x])[2:].zfill(2) #Clean HEX from '0x' AND adding zero until I reach minimum width using .ZFILL(2)
			catResult += cleanHEX
		return int(catResult, 16) #HEX to DEC
		
	######################################################################################################
	def startDefrag(self, progressBar, step, progressText, Progress): #CORE METHOD
		# ------------------- Main Loop in which I analyze every single entry in the FAT region. --------------------------#
		for x in range((((self.startFAT+1)* 512) - 512), (self.startFAT + 1 + self.sizeFAT)* 512 - 512 ,2):
			
			#Update progressBar every "for" loop.
			self.updateProgressBar += 2
			step.set(self.updateProgressBar)
			progressBar.update()
			#Update progressText too.
			stringToPrint = "Progress: " + str(self.updateProgressBar) + " / " + str(self.sizeFATinBYTES) + " bytes" 
			Progress.set(stringToPrint)
			progressText.update()
			
			#Increase FATentry and clean clusterCOntent every "for" loop.
			self.FATentryDEC += 1
			clusterContent = []
			
			#Calculate FATindex for the actual position(each entry is made up of 2 bytes) every "for" loop.
			FATentryHEX = hex(self.FATentryDEC)[2:].zfill(4) 
			self.FATindex[0] = int(FATentryHEX[2:],16) #least in DEC
			self.FATindex[1] = int(FATentryHEX[:2],16) #most in DEC
			
			#CONDITION A) ------------------------------------------
			#F8 FF, FF FF found. Skip a loop and go to next one.
			if self.content[x] == 248 and self.content[x+1] == 255 or self.content[x] == 255 and self.content[x+1] == 255 and self.fragmentedFile == False and len(self.storeFile) == 0: 
				continue

			#CONDITION B) ------------------------------------------
			#F8 FF, FF FF found. But I have filled recently a temporary array with cluster bytes. In this case I have to move and pop cluster in this position.
			elif (self.content[x] == 248 and self.content[x+1] == 255 or self.content[x] == 255 and self.content[x+1] == 255) and self.fragmentedFile == False and len(self.storeFile) != 0:
				#0.0 Found a FF FF... so another file is starting. I'll add a new list to storeFile and increasing storeFileIndex.
				self.storeFile.append([])
				self.storeFileIndex += 1
				#1.0 Save contents of the actual fragmented cluster inside a list.
				clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
				firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
				self.moveFragment(firstClusterByte)
				#2.0 Pop contents in the remporary array in the actual position. I will do this until I have elements inside my temporary array.
				self.pasteFragment(firstClusterByte)
				continue
				#I need to store this information. It is a "FF FF" I can't store it normally as the other clusters, because I have to change root directory too.
			
			#CONDITION C) ------------------------------------------
			#00 00 found. If my temporary array is empty, find next full cluster and move it here, right now.
			elif self.content[x] == 0 and self.content[x+1] == 0 and self.fragmentedFile == False and len(self.storeFile) == 0:
				#If in this position there is a first cluster number I cannot touch it. Put "FF FF" and go ahead.
				if self.checkRoot(self.FATindex[0], self.FATindex[1]) == True:
					#print("there is a first cluster here")
					self.content[x] = 255 #FF
					self.content[x+1] = 255 #FF
					continue
					
				else: #if "00 00" it's just an unused entry. So, checkRoot() returns False and I'M GOING TO MOVE A CLUSTER TO THIS POSITION.
					#1.0 Find next non-empty cluster.
					nextLeast, nextMost, nextIndexListToMove, rootDIRfound = self.returnNextCluster(x, self.FATentryDEC) 
					
					#IMPORTANT! This if is really important because if my temporary array is full and I don't find a full cluster anymore...I have finish to defrag!
					if nextLeast == 0 and nextMost == 0 and  nextIndexListToMove == 0:
						Progress.set('Progress: Finish.')
						step.set(self.sizeFATinBYTES)
						progressBar.update()
						progressText.update()
						break #This is used to exit definitively defraggler when He isn't able to find other clusters non-empty. This means that disk has been totally checked.
						
					#1.5 #Every 2 bytes in FAT region is equal to one entry. For this reason I increase FATindex each loop and I use that to..
					#..calculate FATindex for the actual position in the loop(each entry is made up of 2 bytes)
					nextFATentryDEC = self.findFATindex(nextIndexListToMove) #DEC value for index position.
					nextFATentryHEX = hex(nextFATentryDEC)[2:].zfill(4) #convert DEC to HEX and clean it.
					self.nextFATindex[0] = nextFATentryHEX[2:] #split HEX in two values. LEAST. Need this for writing it on FAT region.
					self.nextFATindex[1] = nextFATentryHEX[:2] #split HEX in two values. MOST.
					
					#2.0 Remove cluster number from that position because i'm going to paste it in another one.
					self.content[nextIndexListToMove] = 0 
					self.content[nextIndexListToMove+1] = 0
					
					#If it is NOT a FF FF... cut-paste next filled cluster without problems.
					if nextLeast != 255 and nextMost != 255: 
						#3.0 Calculate sector in which data is stored from cluster number. Be careful with least and most significant bytes.
						clusterValueDEC = int(hex(nextMost)[2:].zfill(2) + hex(nextLeast)[2:].zfill(2), 16)
						
						#4.0 Cut all the cluster and put it in a list temporarly.
						firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) + 1) * 512) - 512 #Find first byte cluster.
						clusterContent = self.cutCluster(firstClusterByte, clusterContent) #Cut it inside this list temporarly.
						
						#5.0 Calculate first byte in which put the copied cluster.
						clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
						firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512 #Find first byte cluster.
						
						#5.5 Clean cluster that must receive bytes, from other bytes and get ready to paste.
						self.cleanCluster(firstClusterByte)
						
						#6.0 Paste the cluster inside the empty one.
						self.pasteCluster(firstClusterByte, clusterContent)
						
						#7.0 Update FAT region with new cluster number pointer
						self.content[x] = self.FATindex[0]
						self.content[x+1] = self.FATindex[1]
						
						#8.0 Update ROOT directory with new first cluster number for files/folders.
						if rootDIRfound == True:
							#Old value and new values needed to update root informations about first cluster number. 
							self.updateROOT(int(self.nextFATindex[0],16), int(self.nextFATindex[1],16), self.FATindex[0], self.FATindex[1]) 

					#ELSE, if I found an End Of File or a Folder (in HEX "FF FF"). I have to put here another cluster number of another file/folder.
					else: 
						#3.0 Calculate first byte to cut
						clusterValueDEC = int(nextFATentryHEX, 16)
						firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512 #Find first byte cluster.
						
						#4.0 Cut all the cluster and put it in a list temporarly.
						clusterContent = self.cutCluster(firstClusterByte, clusterContent) #Cut it inside this list temporarly.
						
						#5.0 Calculate first byte in which paste the cluster.
						clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
						firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
						
						#5.5 Clean cluster that must receive bytes, from other bytes and get ready to paste.
						self.cleanCluster(firstClusterByte)
						
						#6.0 Paste the cluster inside the empty one.
						self.pasteCluster(firstClusterByte, clusterContent)
						
						#7.0 Update FAT region with new cluster number pointer
						self.content[x] = 255
						self.content[x+1] = 255
						
						#8.0 Update ROOT directory with new first cluster number for files/folders.
						if rootDIRfound == True:
							#Old value and new values needed to update root informations about first cluster number. 
							self.updateROOT(int(self.nextFATindex[0],16), int(self.nextFATindex[1],16), self.FATindex[0], self.FATindex[1])

			#CONDITION D) ------------------------------------------
			#found "00 00" but my array is still full...copy here one cluster from my temporary array.
			elif self.content[x] == 0 and self.content[x+1] == 0 and self.fragmentedFile == False and len(self.storeFile) != 0:
				#If in this position there is a first cluster number I cannot touch it. Put "FF FF" and go ahead.
				if self.checkRoot(self.FATindex[0], self.FATindex[1]) == True:
					self.content[x] = 255 #FF
					self.content[x+1] = 255 #FF
					continue
				#At this moment, this "00 00" is an unused bytes. For this reason I will easily copy a cluster of my temporary array here.
				clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
				firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
				self.pasteFragment(firstClusterByte)

			#CONDITION E) ------------------------------------------
			#HEX value found. This means that HD is not fragmented OR that it is full. To understand that, check index position with his value.
			elif self.FATindex[0] == self.content[x] and self.FATindex[1] == self.content[x+1] and self.fragmentedFile == False and len(self.storeFile) == 0:
				continue

			#CONDITION F) ------------------------------------------
			#This condition is true when I finish to move a fragmented file and I have stored some clusters inside temporary array. I need to move it now in the next clusters.
			elif self.FATindex[0] == self.content[x] and self.FATindex[1] == self.content[x+1] and self.fragmentedFile == False and len(self.storeFile) != 0:
				#1.0 Save contents of the actual fragmented cluster inside a list.
				clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
				firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
				self.moveFragment(firstClusterByte)
				#2.0 Pop contents in the remporary array in the actual position. I will do this until I have elements inside my temporary array.
				self.pasteFragment(firstClusterByte)

			#CONDITION G) ------------------------------------------
			#This will executed when I found a fragmented file. Let's start populating temporary array.
			elif self.fragmentedFile == True:
				#1.0 Save contents of the actual fragmented cluster inside a list.
				clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
				firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512
				self.moveFragment(firstClusterByte)
				#2.0 Increase next fragment index to copy and move into the right cluster.
				self.nextIndexFragmentToMove += 2
				#2.5 If cluster to copy is "FF FF", fragmentedFile boolean must be set to "False" because file chain has ended.
				#Plus, if I had found "FF FF" I must set FF FF in the NEXT position now.
				if self.content[self.nextIndexFragmentToMove] == 255 and self.content[self.nextIndexFragmentToMove+1] == 255:
					#3.0 Set values to FF FF because there is an End of Cluster.
					self.content[x] = 255
					self.content[x+1] = 255
					self.fragmentedFile = False
					#4.0 Paste fragment that I have saved inside self.storeFile in the actual cluster.
					self.pasteFragment(firstClusterByte)
					continue
					
				elif self.content[self.nextIndexFragmentToMove] != 255 and self.content[self.nextIndexFragmentToMove+1] != 255:
					#3.0 Calculate sector in which data is stored from cluster number. Be careful with least and most significant bytes.
					clusterValueDEC = int(hex(self.content[self.nextIndexFragmentToMove+1])[2:].zfill(2) + hex(self.content[self.nextIndexFragmentToMove])[2:].zfill(2), 16)
					firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) + 1) * 512) - 512 #Find first byte cluster.
					#4.0 Cut all the cluster content and put it in a list temporarly.
					clusterContent = self.cutCluster(firstClusterByte, clusterContent) #Cut it inside this list temporarly.
					#5.0 Calculate first byte in which put the copied cluster.
					clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
					firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512 #Find first byte cluster.
					#6.0 Paste the cluster inside the empty one. This time I don't need to clean cluster because I cleaned it with moveFragment() method.
					self.pasteCluster(firstClusterByte, clusterContent)
					#7.0 Clean values in the next index position.
					self.content[self.nextIndexFragmentToMove] = 0
					self.content[self.nextIndexFragmentToMove+1] = 0
					continue

			#CONDITION H) ------------------------------------------
			#If FATindex and content doesn't match in the actual position we don't find the right index. This means file is fragmented.
			elif self.FATindex[0] != self.content[x] and self.FATindex[1] != self.content[x+1] and self.fragmentedFile == False:
				#1.0 Set boolean variable to "true". I have found a fragmented file.
				self.fragmentedFile = True
				#1.5 Append a new list to storeFile multidimensional list. In every list I am going to save cluster of a file.
				self.storeFile.append([])
				self.storeFileIndex += 1
				#2.0 Read cluster location from index and give it findFragment() to find where fragment is.
				self.nextIndexFragmentToMove = self.findFragment(self.content[x], self.content[x+1]) #least, most
				
				#3.0 Remove cluster number from that position because i'm going to paste it in another one.
				self.content[self.nextIndexFragmentToMove] = 0 
				self.content[self.nextIndexFragmentToMove+1] = 0
				
				#4.0 Calculate sector in which data is stored from cluster number. Be careful with least and most significant bytes.
				clusterValueDEC = int(hex(self.content[x+1])[2:].zfill(2) + hex(self.content[x])[2:].zfill(2), 16)
				
				#5.0 Cut all the cluster and put it in a list temporarly.
				firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) + 1) * 512) - 512 #Find first byte cluster.
				clusterContent = self.cutCluster(firstClusterByte, clusterContent) #Cut it inside this list temporarly.
				
				#6.0 Calculate first byte in which put the copied cluster.
				clusterValueDEC = int(hex(self.FATindex[1])[2:].zfill(2) + hex(self.FATindex[0])[2:].zfill(2), 16)
				firstClusterByte = ((((clusterValueDEC * self.SectorPerCluster) + self.constantValue) +1) * 512) - 512 #Find first byte cluster.
				
				#7.0 Clean cluster that must receive bytes, from other bytes and get ready to paste.
				self.cleanCluster(firstClusterByte)
				
				#8.0 Paste the cluster inside the empty one.
				self.pasteCluster(firstClusterByte, clusterContent)
				
				#9.0 Update FAT region with new cluster number pointer.
				self.content[x] = self.FATindex[0]
				self.content[x+1] = self.FATindex[1]

		else: #Last loop - usually, this never happens because it breaks from loop before. But if it happens, update for the last time my progress bar!
			Progress.set('Progress: Finish.')
			step.set(self.sizeFATinBYTES)
			progressBar.update()
			progressText.update()
		
		#Last but not least important operation(before exiting this method): UPDATE FAT region for each other FAT table available in the disk.
		self.cloneFAT()

	############################################# returnNextFullCluster () ####################
	def returnNextCluster(self, startFind, numberEntry):
		for x in range(startFind, (self.startFAT + 1 + self.sizeFAT)* 512 - 512 ,2):
			
			leastMostDEC = [0,0]
			indexHEX = hex(numberEntry)[2:].zfill(4) 
			leastMostDEC[0] = int(indexHEX[2:],16) #least in DEC
			leastMostDEC[1] = int(indexHEX[:2],16) #most in DEC
			resultCheckRoot = self.checkRoot(leastMostDEC[0], leastMostDEC[1]) #for every single "00 00" in FAT region check if there is a first cluster number in root directory!
			
			if resultCheckRoot == True: #the next value after "00 00"... return it.
				return self.content[x], self.content[x+1], x, True #return back "true" if it's a first cluster number
			elif self.content[x] != 0 or self.content[x+1] != 0:
				return self.content[x], self.content[x+1], x, False #return back "false" if it's not a first cluster number
				
			numberEntry += 1
		else:
			print("No more clusters non-empty to check... exiting defragmentation process...") 
			return 0, 0, 0, False #This "return" is very important because if it doesn't find me a next full cluster, program doesn't crash!

	############################################# checkRoot () ####################
	#I need this method to check if I find in the root a cluster number == to a "00 00" in the FAT region. In that case I must write "FF FF" in FAT region.
	def checkRoot(self, least, most): 
		for rootBytes in range (((self.startROOT +1)* 512) - 512, ((self.endROOT+1) * 512) - 512, 32): #analyze all root entries
			if self.content[rootBytes+26] == least and self.content[rootBytes+27] == most: #means that FAT region with "00 00" is busy with root static cluster number.
				return True
		else:
			return False

	############################################# cutCluster() and pasteCluster() and cleanCluster()####################
	#This method read hex values and copy values to a list. This will be useful when I have to move a cluster to another position.
	def cutCluster(self, firstByte, clusterContent): #cut cluster content and I'm ready to paste it in another cluster position.
		for x in range(firstByte, firstByte + (self.bytesPerSector * self.SectorPerCluster)):
				clusterContent.append(self.content[x])
				self.content[x] = 0
		return clusterContent

	def pasteCluster(self, firstByte, clusterContent): #startingByte is the first byte in which I have to copy all the cluster.
		for element in clusterContent:
			self.content[firstByte] = element
			firstByte += 1

	def cleanCluster(self, firstByte): #before starting to paste text, I need to clean every single byte of the cluster. In this way it will be ready.
		for rootBytes in range(firstByte, firstByte + (self.bytesPerSector * self.SectorPerCluster)):
			self.content[rootBytes] = 0

	############################################# findFATindex () ########################################
	#When I am moving clusters from a position to another previous position, I need to look for their value to find cluster in data area. The problem is when I find FF FF, because FF FF doesn't tell me in which area the cluster is. To solve this, I have to calculate FATindex starting from the full array of bytes and with this method find the right position.
	def findFATindex(self, index):
		nextFATentry = 0
		for entries in range((((self.startFAT+1)* 512) - 512), (self.startFAT + 1 + self.sizeFAT)* 512 - 512 ,2):
			nextFATentry += 1
			if entries == index:
				break #exit loop and stop increasing FATentry
		return nextFATentry

	############################################# updateROOT() ########################################
	#When I move a first cluster number from a position to anohter one to defrag, I need to update pointer to first cluster number that is stored inside root directory.
	def updateROOT(self, oldLeast, oldMost, newLeast, newMost):
		for rootBytes in range (((self.startROOT +1)* 512) - 512, ((self.endROOT+1) * 512) - 512, 32): #analyze all root entries
			if self.content[rootBytes+26] == oldLeast and self.content[rootBytes+27] == oldMost: 
				self.content[rootBytes+26] = newLeast
				self.content[rootBytes+27] = newMost
				return

	############################################# findFragment() ########################################
	#I use this method to find array list index to work with next fragmented cluster.
	def findFragment(self, least, most):
		#I have these values in decimal, but position inside FAT region is given in HEX. So I need to convert them in hex and THEN re-convert them in a unique DEC value.
		leastHEX = hex(least)[2:].zfill(2)
		mostHEX = hex(most)[2:].zfill(2)
		concatenate = mostHEX + leastHEX
		
		fragmentedFATentry = int (concatenate, 16)
		cont = 0
		
		for x in range((((self.startFAT+1)* 512) - 512), (self.startFAT + 1 + self.sizeFAT)* 512 - 512 ,2): #search that fragment from the starting FAT region
			cont += 1
			if cont == fragmentedFATentry:
				return x #return array index.
	
	############################################# moveFragmentAtTheEnd() ########################################
	#If there is a fragmented file, I need to move it inside a list temporarly.
	def moveFragment(self, index):
		for x in range(index, index + (self.bytesPerSector * self.SectorPerCluster)):
			self.storeFile[self.storeFileIndex].append(self.content[x])
			self.content[x] = 0
	
	############################################# pasteFragment() ########################################
	#This method is used for pasting all cluster in the position I pass as parameter to the method.
	def pasteFragment(self, firstByte):
		for x in range(0, self.clusterSize): #usually 2048 loops. Because 1 cluster is 2048 bytes in my case.
			self.content[firstByte] = self.storeFile[0].pop(0)
			firstByte += 1
		#If this list is empty now, remove it.
		if len(self.storeFile[0]) == 0:
			self.storeFile.pop(0)
			self.storeFileIndex -= 1

	############################################# cloneFAT() ########################################
	#With this method I'll clone first FAT region to the others. In this way I will have a lot of backups of my clusters in my Disk.
	def cloneFAT(self):
		for numberFAT in range(1, self.nrFAT):
			FATsizeBYTES = self.sizeFAT * 512 * numberFAT
			for x in range((((self.startFAT+1)* 512) - 512), (self.startFAT + 1 + self.sizeFAT)* 512 - 512):
				self.content[x + FATsizeBYTES] = self.content[x]
