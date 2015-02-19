#!/usr/bin/python
#   _____            _         _____                          
#  / ____|          | |       / ____|                         
# | (___   ___   ___| | _____| (___   ___ _ ____   _____ _ __ 
#  \___ \ / _ \ / __| |/ / __|\___ \ / _ \ '__\ \ / / _ \ '__|
#  ____) | (_) | (__|   <\__ \____) |  __/ |   \ V /  __/ |   
# |_____/ \___/ \___|_|\_\___/_____/ \___|_|    \_/ \___|_|  
#
#SocksServer v1.1a, for Proxying TCP connections by Nikos Vassakis
#http://www.secforce.com / nikos.vassakis <at> secforce.com
########################################################################
#Tested with Python 2.6.5

import getopt, sys
import socket
import select 
import sys 
import time
import struct
import threading, thread

DEBUG=1 #Change to 0 for no output

Defaults={
	'hostname':'localhost',
	'webServerPort':0,
	'timeout':0.5,	#TODO: Not implemented
	'bufferSize':1024*8
}

class SocksServer():
	#bufferSizeSize = 1024-4

	def __init__(self, socket, event=threading.Event(), bufferSize=Defaults['bufferSize']):
		self.debug=DEBUG
		self.bufferSize=bufferSize-4
		self.timeout=1	#XXX:For Speed - requests are threaded now but no real gain
		
		self.lock = threading.Lock()
		self.server=socket
		self.event=event 
	
		if self.debug > 0: print "[S]",time.asctime(), "Server Starts - %s:%s" % (self.server.getsockname()[0], self.server.getsockname()[1])
	
	def run(self):
		self.event.set() #all done
		self.server.listen(50)
		self.server.setblocking(True)
		wrapper_channel, address = self.server.accept()
		self.iserver(wrapper_channel)
		wrapper_channel.close()

	def sockReceive(self,s,size):	#Receive until we have the whole packet
		try:
			data = s.recv(size)
			while len(data) < size and data:
				if self.debug > 2: print len(data) , size
				data += s.recv((size-len(data)))
			return data
		except socket.error as e: #Socket error
				self.printError(e)
				pass

	def printError(self,e):		#Red Print
		print '\033[91m',e,sys.exc_info()[0],'\033[0m'

	def parse_socks(self,data):	#Parses the Socks4a Headder
		#Based on Socks4a RFC
		
		user_idx = data[8:].find('\x00')
		fmt = '!BBH4s%ss' % (user_idx)
		#print " Data: \\x" + ('\\x'.join(x.encode('hex') for x in data)),"fmt",fmt
		try:
			(version,command,port,ip,user) = struct.unpack(fmt,data[:8+user_idx])
		except struct.error as e:
			self.printError(e)
			if self.debug >2: print data
			if self.debug >2: print " Data: \\x" + ('\\x'.join(x.encode('hex') for x in data))
			return None
		
		if version != 4:
			print "[-] Unsupported version: " + str(version)
			return None
		
		if command != 1:
			print "[-] Unsupported command: " + str(command)
			return None
		#Get IP
		if ip[:3] == '\x00\x00\x00' and ip[3:] != '\x00':	#SOCKS4a
			#print data[8+1+user_idx:].find('\x00')
			host = data[8+user_idx+1:8+user_idx+1+data[8+user_idx+1:].find('\x00')]	
		else:
			host = socket.inet_ntoa(ip)
		
		return (version,command,port,user,host)

	def establishConnection(self,s,data,sockets,SocketDict,inSrcPort):
		granted = '\x00\x5a\x00\x00\x00\x00\x00\x00' 	#Socks request granted response
		rejected = '\x00\x5b\x00\x00\x00\x00\x00\x00'	#Socks request rejected response
		
		try:
			#Parse data
			(version,command,port,user,host) = self.parse_socks(data)

			if self.debug > 2: print (version,command,port,user,host)
			
			#Connect to socket
			outSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			outSock.settimeout(self.timeout)
			outSock.connect((host, port))
			
			if self.debug >4: print "[T] Establish connection locking 1"
			
			self.lock.acquire()
			try:			
				sockets.append(outSock)
				SocketDict[self.srcPort(outSock)] = inSrcPort,outSock		#Link incoming port to created socket
				s.send(struct.pack('!HH',inSrcPort,len(granted))+granted)	#Send connection established responce
			finally:
				if self.debug >4: print "[T] Establish connection releasing 1"
				self.lock.release()
			
			if self.debug > 0: print "[S] Connection to "+host+" Established"
		except (TypeError,socket.error, KeyError) as e :
			print "[-] Socks: Rejected", e
			
			if self.debug >4: print "[T] Establish connection locking 2"
			self.lock.acquire()
			try:
				s.send(struct.pack('!HH',inSrcPort,len(rejected))+rejected)	#Send connection rejected responce (port closed)
			finally:
				if self.debug >4: print "[T] Establish connection releasing 2"
				self.lock.release()
			pass

	def srcPort(self,s):
		return s.getsockname()[1]

	def findISocket(self, port, dictionary):
		for (p, sock) in dictionary.itervalues():
			if p == port:								#If inSrcPort number in list redirect to socket
				if self.debug > 3: print "\t (Found -",self.srcPort(sock),") -Redirecting-"
				return sock
		else:
			return False
	
	def deleteISocket(self, socket,dictionary,sockets):
		del dictionary[self.srcPort(socket)]
		sockets.remove(socket)
	
	def iserver(self, wrapper_channel):
		sockets = [wrapper_channel] 
		self.sockets=sockets
		running = 1 
		SocketDict = {}
		debug=DEBUG

		while running: 
			inputready,outputready,exceptready = select.select(sockets,[],[]) 
			for s in inputready:
				try:
					if debug > 2: print "[+] Open Sockets: ",len(sockets)
					if s == wrapper_channel: # handle the input - main - socket 
					
						head = self.sockReceive(s,4) #Tunna Head: First 4 bytes=incoming port and size of packet 
						(inSrcPort,size) = struct.unpack('!HH',head)
						if debug > 3: print "< L Received: ", "inSrcPort: ", inSrcPort, "size: ", size,"\n\t", struct.unpack('!HH',head)

						if size > 0:
							data = self.sockReceive(s,size)
							outSock=self.findISocket(inSrcPort,SocketDict)
							if outSock:
								outSock.send(data)
							else: # In socket not in list - Try Socks
								if debug > 4: print "[D] Starting Connection Thread"
								Thread = threading.Thread(
									target=self.establishConnection, args=(s,data,sockets,SocketDict,inSrcPort)
									).start()
								#self.establishConnection(s,data,sockets,SocketDict,inSrcPort)
						else: #inSrcPort send no data - Port Closed 
							if debug > 3: print "\t Close Socket: ", inSrcPort
							
							outSock=self.findISocket(inSrcPort,SocketDict)
							if outSock:
								self.lock.acquire()
								try:
									self.deleteISocket(outSock,SocketDict,sockets)
								finally:
									self.lock.release()
								outSock.close()
								break
							else: # Input socket not in list ?
								if debug > 3: print "[E] Received empty & socket not in list: ", inSrcPort
					else: # Other sockets (outSockets)
						data = s.recv(self.bufferSize) 
						if debug > 3: print "> R Received: Data (client -",self.srcPort(s),") :" , len(data) 
						
						if data: 
							
							if debug > 3: print "\t sending to:", SocketDict[self.srcPort(s)][0],"len", len(data)
							if debug >4: print "[T] Write to channel locking 1"
							
							self.lock.acquire()
							try:
								wrapper_channel.send((struct.pack('!HH',SocketDict[self.srcPort(s)][0],len(data))+data))
							except (TypeError,socket.error, KeyError) as e:
								print "[-] Send Failed:", e
								pass
							finally:
								if debug >4: print "[T] Write to channel releasing 1"
								self.lock.release()
						
						if len(data)==0:
							if debug > 3: print "\tClosing port: ", SocketDict[self.srcPort(s)][0],'len:', len(data),"Local Port:", self.srcPort(s)
							
							if debug >4: print "[T] Write to channel locking 2"
							self.lock.acquire()
							try:
								wrapper_channel.send((struct.pack('!HH',SocketDict[self.srcPort(s)][0],len(data)))) 	#send empty to lSrc will close the socket on the other end
							except (TypeError,socket.error, KeyError) as e :
								self.printError(e)
								pass
							finally:
								if debug >4: print "[T] Write to channel releasing 2"
								self.lock.release()
							
							self.lock.acquire()
							try:
								self.deleteISocket(s,SocketDict,sockets)
							finally:
								self.lock.release()

							s.close()
				except struct.error as e:
					print "[-] Received malformed packet: Closing Socks Proxy"
					sys.exit()
				except socket.error as e:	#Kill misbehaving socket
					self.printError(e)
					try:
						self.lock.acquire()
						try:
							self.deleteISocket(s,SocketDict,sockets)
						finally:
							self.lock.release()
						s.close()
					except:
						pass		
					pass	
		wrapper_channel.close()

	def __del__(self):
		if hasattr(self,"sockets"):
			for s in self.sockets:
				s.close()
				
def banner():
	print "   _____            _         _____                          "
	print "  / ____|          | |       / ____|                         "
	print " | (___   ___   ___| | _____| (___   ___ _ ____   _____ _ __ "
	print "  \\___ \\ / _ \\ / __| |/ / __|\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|"
	print "  ____) | (_) | (__|   <\\__ \\____) |  __/ |   \\ V /  __/ |   "
	print " |_____/ \\___/ \\___|_|\\_\\___/_____/ \\___|_|    \\_/ \\___|_|  "
	print ""

	print  "SocksServer v1.1a, for Proxying TCP connections by Nikos Vassakis"
	print  "http://www.secforce.com / nikos.vassakis <at> secforce.com"
	print "###############################################################"
	print ""	
	
if __name__ == '__main__':
	if DEBUG > 2: banner()
	options={}
	
	if sys.argv < 1:
		usage()
		sys.exit(2)
	else:
		options['webServerPort']=int(sys.argv[1])
		#TODO: Parse Arguments
		options=dict(Defaults.items() + options.items()) if options else Defaults

		SocksServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		SocksServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		SocksServerSocket.bind((options['hostname'],options['webServerPort'])) 

		S=SocksServer(SocksServerSocket)
		
		try:
			S.run()	
		except KeyboardInterrupt:
			if DEBUG > 0: print "[S] Shutting Down SocksServer" 
			sys.exit(9)
