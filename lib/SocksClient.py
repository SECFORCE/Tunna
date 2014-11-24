#   _____            _         _____ _ _            _   
#  / ____|          | |       / ____| (_)          | |  
# | (___   ___   ___| | _____| |    | |_  ___ _ __ | |_ 
#  \___ \ / _ \ / __| |/ / __| |    | | |/ _ \ '_ \| __|
#  ____) | (_) | (__|   <\__ \ |____| | |  __/ | | | |_ 
# |_____/ \___/ \___|_|\_\___/\_____|_|_|\___|_| |_|\__|
#
#SocksClient v1.1a, for Proxying TCP connections by Nikos Vassakis
#http://www.secforce.com / nikos.vassakis <at> secforce.com
###############################################################

from time import time, sleep, asctime
import socket
import select 
import sys 
import time
import getopt, struct
import threading, thread

from settings import SocksServer_Defaults as Defaults

DEBUG=0

class SocksClient():	#TODO init:options
	#bufferSizeSize = size-4 - 4 bytes used for header
	def __init__(self, portnumber, hostname='', bufferSize=Defaults['buffersize'], backlog=Defaults['backlog']):
		self.bufferSize=bufferSize-4
		self.error=0
		self.backlog = backlog
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind((hostname,portnumber)) 
 		self.server.listen(self.backlog) 

		self.debug = DEBUG

		print "[S] ",asctime(), "Server Starts - %s:%s" % ((hostname if hostname!='' else 'localhost'), portnumber)	
		
		self.wrapper_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.wrapper_channel.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	def connect(self,TunnaPort, event=None):
		if event:
			event.wait()
		try:
			self.wrapper_channel.connect(('localhost', TunnaPort)) 
			success=True
		except Exception, e:
			print 'something\'s wrong Exception type is %s' % `e`
			sys.exit()

		self.iserver(self.server, self.wrapper_channel)
		
		self.server.close()
		self.wrapper_channel.close()
	
	def sockReceive(self,s,size):
		try:
			data = s.recv(size)
			while len(data) < size and data:
				if self.debug >1: print len(data) , size
				data += s.recv((size-len(data)))
			return data
		except socket.error as e:	#Socket error
			self.error=self.error+1
			self.printError(e)
			if self.error > 20 : sys.exit()
			pass

	def printError(self,e):
		print '\033[91m',e,'\033[0m'

	def srcPort(self,s):
		return s.getpeername()[1]

	def iserver(self,local_proxy_server,wrapper_channel):	#add blocking to wrapper_channel
		debug = DEBUG
		sockets = [local_proxy_server,wrapper_channel] 
		running = 1 
		SocketDict = {}

		#Multiple input -> will get sent over http 1st byte of packet will be socket identifier
		while running: 
			inputready,outputready,exceptready = select.select(sockets,[],[]) 

			for s in inputready: 
				try:
					if debug > 1: print "[+] Open Sockets: ",len(sockets)-1
					if s == local_proxy_server: # Accept client connections
						# handle the server socket 
						client, address = self.server.accept() 
						SocketDict[self.srcPort(client)]=client
						sockets.append(client)
						if debug > 1: print "Accepted Client lSrc: "+str(self.srcPort(client))

					elif s == wrapper_channel:	# Receive response 
						head = self.sockReceive(s,4)
						try:
							(lSrc,size) = struct.unpack('!HH',head)
						except struct.error as e:
							pass						
						
						if debug > 2: print "< R received ", "lSrc: ", lSrc, "size: ", size

						if size > 0:
							data = self.sockReceive(s,size)
								
							if lSrc in SocketDict:
								if debug > 2: print "\t relaying to lSrc: ", lSrc, 'len', len(data)
								SocketDict[lSrc].send(data)
							else:
								if debug > 2: print "\t Received response for unknown port " , str(lSrc) , len(data)
						else:
								if debug > 2: print "\t Closing Socket: ", lSrc
								SocketDict[lSrc].close()
								sockets.remove(SocketDict[lSrc])
								del SocketDict[lSrc]

					else: 	# handle all other sockets - lSrc
						lSrc=self.srcPort(s)
						data = s.recv(self.bufferSize)
							
						if debug > 2: print "> L Received Data (client -",lSrc,") :" , len(data)
						if len(data)>0 and data: 
							data = struct.pack('!HH', self.srcPort(s),len(data)) + data
							if debug > 2: print  "\t sending: ",len(data),"\tstruct:", struct.pack('!HH', self.srcPort(s),len(data))
							wrapper_channel.send(data) 
						if len(data)==0: 
							if debug > 2: print "\t No data: Closing Socket: ", self.srcPort(s)
							data = struct.pack('!HH', self.srcPort(s),len(data))
							if debug > 2: print  "\t sending: ",len(data),"\tstruct:", struct.pack('!HH', self.srcPort(s),len(data))
							wrapper_channel.send(data) 
							if s in sockets: 
								del SocketDict[self.srcPort(s)]
								sockets.remove(s)
								s.close()	
				except socket.error, (errno, e):# socket.error, KeyError:
					if errno != 107:
						self.printError(e)
					if errno == 107:
						pass
					try:
						del SocketDict[self.srcPort(s)]
						sockets.remove(s)
						s.close()
					except:
						pass
					pass
				except (KeyError, struct.error) as e:
					self.printError(e)
					pass
		server.close()
