#---------------------- Little Tutorial About Conversions by me ------------------------------#
#import binascii #to use hexlify and unhexlify

#print (binascii.hexlify(content)) #BINARY TO HEX - ALL FILE
#print(binascii.unhexlify(content)) #HEX TO BINARY - ALL FILE
#print (int("A", 16)) #HEX STRING TO DEC
#print(hex(content[0]).split('x')[1]) #DEC TO HEX STRING WITHOUT '0x'
#print(content[0]) #DECIMAL PRINT
#print(ord(a)) #print 97 - ASCII TO DEC
#print(chr(97)) #print a - DEC TO ASCII
#print(bytes(58)) #print b'/x00' - INT TO BYTES
#print(bin(10)) #print '0b1010' - INT TO BINARY
##############################################################################################

from Disk import *

myDisk = Disk()

filename = 'fat16_live_fragmented_3times_full.img'
fileToWrite = 'prova.img'

#1.0 - Open .img file and read his structure.
f = open (filename, 'rb')
allText = f.read()
f.close()

#All text will be an immutable array of bytes. To work with it I need to read/write so I need to convert it to a bytearray.
myDisk.content = bytearray(allText)

############################################# USEFUL DISK INFORMATIONS #############################################
#4.0.0 - General Informations
print("--- General Informations ---")

#4.0.1 - File name
print("File name: ", filename)

#4.0.2 File System checking
for x in range (54, 62): #I need to check 8 bytes... from 0x36 to 0x3E
	myDisk.fileSystemSTRING += chr(myDisk.content[x])
print("File System Type: ", myDisk.fileSystemSTRING)

#4.1 - Disk size in bytes/KB
myDisk.imgDimBytes = len(myDisk.content) #in bytes
myDisk.imgDimKB =  myDisk.imgDimBytes // 1024
print("File size: " , myDisk.imgDimBytes , " bytes.")
print("File size in KB: ", myDisk.imgDimKB , "KB. \n")

#4.2 - Media Descriptor
myDisk.mediaDescriptor(21) #21 is DEC of 0x15. 0x15 is a byte in the boot block that define media descriptor.

#4.3.0 - Sectors
print("\n--- Sectors Informations ---")

#4.3.1 Bytes per Sector
myDisk.bytesPerSector = myDisk.HEXstringToDEC(12,10, -1)
print("Bytes per sector: ", myDisk.bytesPerSector)

#4.3.2 Total Sectors into the disk
myDisk.totalSECTORS = myDisk.imgDimBytes // myDisk.bytesPerSector
print("Total Number of Sectors in hard disk: ", myDisk.totalSECTORS)

#4.4.0 - CLUSTERS Size or Allocation Units.
print('\n--- Clusters or Allocation Units ---') #0x0d byte in the boot block

#4.4.1 - Sectors per Cluster
myDisk.SectorPerCluster = myDisk.content[13]
print("Number of sectors per allocation unit(cluster): ", myDisk.SectorPerCluster)

#4.4.2 - Cluster size
myDisk.clusterSize = myDisk.SectorPerCluster * 512
print("Cluster Size: ", myDisk.clusterSize, " bytes")

#4.5.0 - Areas Descriptions (Size of each area of the disk)
print("\n--- Areas Descriptions ---")

#4.5.1 - BOOT BLOCK
print("(1) BOOT BLOCK")
myDisk.sizeBOOT =  myDisk.HEXstringToDEC(15,13, -1)
print("Size: ", myDisk.sizeBOOT, "sectors.")
print("Start Sector: 0")
myDisk.endBOOT = myDisk.sizeBOOT - 1 #because first sector is 0. So i.e., if we have 8 sectors for boot block it will finish at sector 7.
print("End Sector: ", myDisk.endBOOT)

#4.5.2 - FAT (FILE ALLOCATION TABLE)
print("\n(2) FAT - FILE ALLOCATION TABLE")
myDisk.nrFAT = myDisk.content[16]
print("Number of FAT:", myDisk.nrFAT)
myDisk.sizeFAT = myDisk.HEXstringToDEC(23,21, -1)
print("Size of each FAT: ", myDisk.sizeFAT, "sectors")
print("Total FATs Size: ", myDisk.sizeFAT * myDisk.nrFAT)
myDisk.startFAT = myDisk.endBOOT + 1
print("Start Sector: ", myDisk.startFAT)
myDisk.endFAT = (myDisk.sizeFAT * myDisk.nrFAT) + myDisk.startFAT #BE CAREFUL: endFAT ends at endFAT -1 because endFAT is the starting point for root directory so be careful.
print("End Sector: ", myDisk.endFAT)

#4.5.3 - Disk Root Directory
print("\n(3) DISK ROOT DIRECTORY")
print("Size of each Entry: 32 bytes per directory/entry")
myDisk.totalENTRIES = myDisk.HEXstringToDEC(18,16, -1)
print("Number of root directory entries: ", myDisk.totalENTRIES) #0x11 - 0x12 bytes of boot block.
print("Total entries dimensions ( 32 x", myDisk.totalENTRIES ,"): ", myDisk.totalENTRIES * 32, " bytes.")
myDisk.sizeROOT = (myDisk.totalENTRIES * 32) // myDisk.bytesPerSector
print("Size of root directory (",myDisk.totalENTRIES * 32, "/", myDisk.bytesPerSector , "): ", myDisk.sizeROOT ,"sectors.")
myDisk.startROOT = myDisk.endFAT
print("Start Sector: ", myDisk.startROOT) #where FAT ends, ROOT starts!
myDisk.endROOT = myDisk.startROOT + myDisk.sizeROOT
print("End Sector: ", myDisk.endROOT) 

#4.5.4 - Data Area Management and Clusters
print("\n(4) FILE DATA AREA")
myDisk.sizeDATA = myDisk.totalSECTORS - myDisk.endROOT
print("Data area size: ", myDisk.sizeDATA , " sectors.")
myDisk.totalClusters = myDisk.sizeDATA // myDisk.SectorPerCluster
print("Total Cluster number (DataAreaSize/SectorsPerCluster): ", myDisk.totalClusters, " clusters")
myDisk.startDATA = myDisk.endROOT
print("Start Sector: ", myDisk.startDATA) #where ROOT ends, file data area starts!
myDisk.endDATA = myDisk.totalSECTORS
print("End Sector: ", myDisk.endDATA)

#4.8 - CONSTANT VALUE TO SUBSTRACT to find first cluster, that start from 2. (because first 2 entries of root directory are reserved and cluster 0 and 1 don't exist.)
print("\n(5) UTILITIES")
myDisk.constantValue = myDisk.endROOT - (myDisk.SectorPerCluster * 2)
print("Constant Value: ", myDisk.constantValue)
print("(Formula to find first cluster number in Data Area: (DecimalFirstClusterNumber * SectorPerCluster) + Constant Value)")

############################################# DEFRAGMENTATION PROCESS ####################
#VERY IMPORTANT NOTE: IF I HAVE TO CHECK FOR I.E. SECTOR 9, IT IS EQUAL TO 10, BECAUSE SECTORS STARTS AT 0. AND IF I HAVE TO CHECK LAST ELEMENT OF SECTOR 0, IT IS 511 BECAUSE
#THE "content" array that contains all my bytes starts at position 0!! BE CAREFUL.
##########################################################################################
#5.0 Check free space 
print("\n--- Checking Free Space ---")
print("Loading...")

#for y in range(myDisk.startDATA, myDisk.endDATA - 4, myDisk.SectorPerCluster): #step 4 if 1 cluster = 4 sectors.
	#isEmpty = True #I'll use this variable to check if a cluster is empty or not.
	#firstByte = (((y+1)*512) - 1) - 511 		#First byte to analyze for every cluster. Read important note to understand this substractions.
	#for x in range (firstByte, firstByte + (myDisk.SectorPerCluster * 512)): #checking one per one bytes of a cluster.
		#if myDisk.content[x] != 0:
			#isEmpty = False
			#break #With this "break" I save a lot of resources because I don't need to check all the bytes if I find just one bytes != 0.
	#if isEmpty == True:
		#myDisk.freeSpace += 1

#print("...finished!")

#print("Cluster free in Data Area: ", myDisk.freeSpace)
#print("Free sectors in the disk: (", myDisk.freeSpace, "x", myDisk.SectorPerCluster, "): " , myDisk.freeSpace * myDisk.SectorPerCluster, " sectors." )
#Percentage15 = myDisk.totalSECTORS * 15 // 100 #disk must have 15% free space to be defragmented. Let's calculate it.
#SpacePercentage = ((myDisk.freeSpace * myDisk.SectorPerCluster) * 100) // myDisk.totalSECTORS
#print("Free Space in percentage: ", SpacePercentage ,"%")
#if SpacePercentage > 15:
	#print("You can start defragmentation! You have enough free space.")
#else:
	#print("You cannot defrag this disk! You have not enough free space.")
	#quit()


##5.5 DEFRAGGLER 
#defragmentation = int(input("Vuoi deframmentare?"))
#if defragmentation == 1:
myDisk.startDefrag()

#When defrag is ended, write all contents in another new .img file. In this way I don't broke my .img fragmented image.
f2 = open(fileToWrite, 'wb')
f2.write(myDisk.content)
f2.close()
