#Tested with Python 2.6.5
import SocketServer
import urllib2
import cookielib
import gzip, zlib, StringIO
from time import time, sleep
import threading, thread
import asyncore
import socket
import getopt, sys

class MainServerSocket(asyncore.dispatcher):	#Initialise socket thread
	def __init__(self, localport):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.bind(('',localport))
		self.listen(5)
	def handle_accept(self):	
		newSocket, address = self.accept( ) #Accept connection
		print "[+] Connected from", address
		S=SecondaryServerSocket(newSocket)	#Socket handling thread
		S.init_ping_thread(start_p_thread)
		
class SecondaryServerSocket(asyncore.dispatcher_with_send):
	global url
	#Mux: To ensure that only one HTTP request is made at a time
	mutex_http_req = threading.Lock()
	pings=0	
	start_p_thread = False

	def init_ping_thread(self,start=False):	#Initialise thread
		self.pt = threading.Thread(name='ping', target=self.Pinging_Thread, args=())
		self.pt.setDaemon(1)				#will exit if main exits
		if start:
			self.start_p_thread = True
			self.pt.start()

	def Pinging_Thread(self):
		print "[+] Starting Ping thread"
		wait = True
		while 1:							#loop forever
			if wait: sleep(ping_delay)		#send ping to server interval
			self.mutex_http_req.acquire()	#Ensure that the other thread is not making a request at this time
			try:
				resp_data=HTTPreq(url,"")	#Read response
				if verbose: v_print(pings_n=1)
				if resp_data:					#If response had data write them to socket
					if verbose: v_print(received_d_pt=len(resp_data))
					self.send(resp_data)		#write to socket
					resp_data=""				#clear data
					#not clearing flag in case more data avail.
					wait = False				#Dont wait: if there was data probably there are more
				else:
					wait = True
			finally:
				self.mutex_http_req.release()	
		print "[-] Pinging Thread Exited"
		thread.interrupt_main()		#Signal main thread -> exits

	def handle_read(self):
		self.data = self.recv(bufferSize)	#Read socket
		if self.data:						#If data send them over HTTP (post)
			self.mutex_http_req.acquire()	#Ensure that the other thread is not making a request at this time
			
			if self.start_p_thread == False:	#Starts pinging thread (Will only run after first data is read from socket)
				self.start_p_thread = True
				self.pt.start()
				
			try:
				if verbose: v_print(sent_d=len(self.data))
				resp_data=HTTPreq(url,self.data)		#send data with a HTTP post
				if resp_data:							#If data is received back write them to socket
					if verbose: v_print(received_d=len(resp_data))
					self.send(resp_data)				#Write data to socket
					resp_data=""						#clear data
			finally:
				self.mutex_http_req.release()
				
	def handle_close(self):			#Client disconnected
		self.pt._Thread__stop()		#Stop socket thread and exit
		print "[-] Disconnected"
		exit()
		

def Threaded_request(url,cj):
	#Sends connection options to the webshell
	#In php this thread will stall to keep the connection alive (will not receive response)
	#In other langs [OK] is received
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	global remote_ip

	print '[+] Spawning keep-alive thread'	
	if remote_ip:
		resp = HTTPreq(url+"&port="+str(remote_port)+"&ip="+str(remote_ip))
	else:
		resp = HTTPreq(url+"&port="+str(remote_port))
	if(resp != '[OK]'):				#if ok is not received something went wrong (if nothing is received: it's a PHP webshell)
		print resp
		print '[-] Keep-alive thread exited'
		thread.interrupt_main()
	else:							#If ok is received (non-php webshell): Thread not needed
		print '[-] Keep-alive thread not required'

def HTTPreq(url,data=""):
	if data:	#If there is data do a HTTP Post and send the data
		f=opener.open(urllib2.Request(url,data,headers={'Content-Type': 'application/octet-stream'}))
	else:		#If there is no data do a HTTP Get
		f=opener.open(url)
	#If response is gzip encoded
	if ('Content-Encoding' in f.info().keys() and f.info()['Content-Encoding']=='gzip') or \
		('content-encoding' in f.info().keys() and f.info()['content-encoding']=='gzip'):
		url_f = StringIO.StringIO(f.read())	
		data = gzip.GzipFile(fileobj=url_f).read()
	else:	#response not encoded
		data = f.read()
	return  data	#Return response

def setup_tunnel():
	#Initial Request to get the cookie
	print opener.open(url).read()
	sleep(1)
	
	#2nd request: send connection options to webshell - In php this thread will stall
	t = threading.Thread(target=Threaded_request, args=(url,cj))
	t.setDaemon(1)	#Daemonize the thread
	t.start()		#start the thread
	#Add support for gzip
	opener.addheaders = [('Accept-encoding', 'gzip')]
	
def v_print(sent_d=0, received_d=0, received_d_pt=0,pings_n=0):	#Verbose output for Debugging
	global send
	global received
	global received_pt
	global pings
	
	send+=sent_d
	received+=received_d
	received_pt+=received_d_pt
	pings+=pings_n

	sys.stdout.write("\x1b[2J\x1b[H")	#Unix only

	sys.stdout.write(
		"Received Data: %d (%d)\nReceived Data From Ping Thread: %d (%d) \nSent data: %d (%d) \nPings sent: %d\r\n" 
		% (received,received_d, received_pt,received_d_pt, send, sent_d, pings) )
	sys.stdout.flush()

def banner():
	print "  _____                        "
	print " |_   _|   _ _ __  _ __   __ _ "
	print "   | || | | | '_ \\| '_ \\ / _` |"
	print "   | || |_| | | | | | | | (_| |"
	print "   |_| \\__,_|_| |_|_| |_|\\__,_|"
	print ""

	print  "Tunna v0.1, for HTTP tunneling TCP connections by Nikos Vassakis"
	print  "http://www.secforce.com / nikos.vassakis <at> secforce.com"
	print "###############################################################"
	print ""

def usage():
	banner()
	print "Usage: python proxy.py -u <remoteurl> -l <localport> -r <remote_service_port> [options]"
	print "    -u:		url of the remote webshell"
	print "    -l:		local port of webshprx"
	print "    -r:		remote port of service for the webshell to connect to"
	print "    -q:		webshprx pinging thread interval (default = 0.5)"
	print "    -a:		address for remote webshell to connect to (default = 127.0.0.1)"
	print "    -b:		HTTP request size (some webshels have limitations on the size)"	
	print "    -s:		start the pinging thread first - some services send data first (SSH)"	
	print "    -v:		Verbose (outputs packet size)"
	print "    -h:		Help page"
	print
	

#Defaults
interval = 0.2
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
verbose=False
ping_delay = 0.5
send=0
received=0
received_pt=0
pings=0
localport=0
remote_port=0
remote_ip="127.0.0.1"
start_p_thread=False
bufferSize=8192

def main():
	#Life's too short globals
	global url
	global localport
	global remote_port
	global verbose
	global ping_delay
	global interval
	global remote_ip	
	global start_p_thread
	global bufferSize

	try:
		opts, args = getopt.getopt(sys.argv[1:], "vhsd:a:u:l:r:q:b:", ["help"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	try:
		for o, a in opts:
			if o in ("-h", "--help"):
				usage()
				sys.exit()
			if o == "-u":
				url=a
				url+="?proxy"
			if o == "-l":
				localport=int(a)
			if o == "-r":
				remote_port=int(a)
			if o == "-v":
				verbose = True
			if o == "-d":
				interval=int(a)
			if o == "-q":
				ping_delay=int(a)
			if o == "-a":
				remote_ip=a
			if o == "-b":
				bufferSize=int(a)
			if o == "-s":
				start_p_thread=True
				
	except:
		usage()
		sys.exit(2)
	if localport==0 or url=="" or remote_port==0:
		usage()
		sys.exit(2)
	else:
		try:	
			print "[+] Local Proxy listening at localhost:%d\n\t Remote service to connect to at remotehost:%d" % (localport,remote_port)
			setup_tunnel()
			# Activate the server; this will keep running until you
			# interrupt the program with Ctrl-C
			MainServerSocket(localport)
			asyncore.loop(interval)
		except (KeyboardInterrupt, SystemExit):
			print HTTPreq(url+"&close")	#Close handler thread on remote server

if __name__ == "__main__":
	main()

