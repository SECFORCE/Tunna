#!/usr/bin/python
# _______                   __          __  _     _____                          
#|__   __|                  \ \        / / | |   / ____|                         
#   | |_   _ _ __  _ __   __ \ \  /\  / /__| |__| (___   ___ _ ____   _____ _ __ 
#   | | | | | '_ \| '_ \ / _` \ \/  \/ / _ \ '_ \\___ \ / _ \ '__\ \ / / _ \ '__|
#   | | |_| | | | | | | | (_| |\  /\  /  __/ |_) |___) |  __/ |   \ V /  __/ |   
#   |_|\__,_|_| |_|_| |_|\__,_| \/  \/ \___|_.__/_____/ \___|_|    \_/ \___|_|   
#
#TunnaWebServer v1.1a, for HTTP tunneling TCP connections by Nikos Vassakis
#http://www.secforce.com / nikos.vassakis <at> secforce.com
#################################################################################
#Tested with Python 2.6.5

import time
import BaseHTTPServer
from urlparse import urlparse, parse_qs, parse_qsl
import random
import Cookie
import socket
import select 
import sys,os
import time
import getopt, struct
import threading, thread
import ssl
import tempfile
import SocketServer

from lib.SocksServer import SocksServer

from settings import Webserver_Defaults as Defaults

class MultiThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class WebServer():
	def __init__(self, options):
		self.options=options
		hostname=options['hostname']
		portNumber=options['webServerPort']
		
		server_class = MultiThreadedHTTPServer		#Multithreaded webserver
		#server_class = BaseHTTPServer.HTTPServer 	#For non-threaded webserver
		wHandler = self.WebHandler
		httpd = server_class((hostname, portNumber), wHandler)
		self.hostname = hostname
		
		sessions={}
		wHandler.sessions=sessions
		wHandler.debug=options['WDEBUG']
		wHandler.usefile=options['USEFILE']

		#wHandler.auth
		try:
			if options['ssl']:	#SSL server
				self.certFile = tempfile.NamedTemporaryFile(suffix=".pem")
				self.certFile.write(options['certificate'])
				self.certFile.flush()
				httpd.socket = ssl.wrap_socket (httpd.socket, certfile=self.certFile.name, server_side=True,ssl_version=ssl.PROTOCOL_TLSv1)

			print "[W]",time.asctime(), "Web Server Starts - %s:%s" % (hostname, portNumber), "(SSL Server)" if options['ssl'] else ''

			httpd.serve_forever()
				
		except KeyboardInterrupt:
			pass
		
		self.cleanup(sessions)
		if hasattr(self,'sslFile'):
			self.sslFile.close()
		httpd.server_close()
		
		print "[W] ",time.asctime(), "Web Server Stops - %s:%s" % (hostname, portNumber)
	
	def cleanup(self,sessions):
		print "[-] Cleaning up"
		for sessionId in sessions:
			session=sessions[sessionId]
			if 'SocksProcess' in session:
				print "[-] Killing process", session['SocksProcess'].pid
				session['SocksProcess'].kill()
				time.sleep(1)
			if 'file' in session:
				print "[-] Removing File", session['file'].name
				os.remove(session['file'].name)
			if 'SocksThread' in session:
				print "[-] Killing Socks Thread"
				t=session['SocksThread']
				t._Thread__stop()
				t.join()
	
	class WebHandler(BaseHTTPServer.BaseHTTPRequestHandler):
		debug=0
		bufferSize = 8192
		sessions=None
		
		def do_GET(self):
			self.handle_request()
			
		def do_POST(self):
			self.handle_request()

		def send(self,data="", responseCode=200):
			self.send_response(responseCode)
			
			for morsel in self.cookie.values():	#Add cookie
				self.send_header('Set-Cookie', morsel.output(header='').lstrip())
			for (k,v) in self.resp_headers.items():
				self.send_header(k,v)
			self.end_headers()
			
			self.wfile.write(data)

		def readFile(self):
			import cgi
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			
			if ctype == 'multipart/form-data':
				
				fs = cgi.FieldStorage( fp = self.rfile, 
					headers = self.headers, 
					environ={ 'REQUEST_METHOD':'POST' }  
				  )
				
			if 'meterpreter' in fs:
				return fs['meterpreter'].file.read()
			elif 'proxy' in fs:
				return fs['proxy'].file.read()
			else:
				return None

		def fileUpload(self):
			f=self.readFile()
			
			self.tmpFile = tempfile.NamedTemporaryFile(suffix=".exe",delete=False)
			self.tmpFile.write(f)
			self.tmpFile.close()
			if self.debug >1: print "[W] File uploaded to:",self.tmpFile.name
			return self.tmpFile
	
		def fileRun(self,session,port):
			f=session['file']
			if 'linux' in sys.platform:
				os.system(('chmod +x %s' % f.name))
			import subprocess
			session['SocksProcess']=subprocess.Popen([f.name,str(port)])
			if self.debug >1: print "[W] Executing file",f.name

		def handle_request(self):
			bufferSize=self.bufferSize
			self.resp_headers = {"Content-type":'application/oclet-stream'}
			
			#Get cookie parameters
			self.cookie=Cookie.SimpleCookie()
			
			if self.headers.has_key('cookie'):
				self.cookie=Cookie.SimpleCookie(self.headers.getheader("cookie"))
			#Get URL parameters
			url_param = dict(parse_qsl(urlparse(self.path).query,keep_blank_values=True))
			
			if self.debug > 2: print "[+] url parameters:",url_param
			#Handle requests
			if url_param.get('proxy') == '':
				session=self.Session()
				#if self.options['authorization'] and session['Authorized'] == None:
				#"Authorization Required"
				
				if url_param.get('file') == '':
					if url_param.get('upload') == '':
						session['file']=self.fileUpload()
					else:
						print "[-] Wrong Parameters (?)\n\t", url_param
					self.send()
					return
				
				if url_param.get('close') == '':
					self.close(session)
					return
				
				if url_param.get('port'):	#if port is specified connects to that port
					session['port'] = url_param.get('port', None)

				if url_param.get('ip'):		#if ip is specified connects to that ip
					session["ip"] = url_param.get('ip', None)
		
				if url_param.get('socks') == '':
					session["socks"]=True
		
				if self.debug > 2: print "[+] url parameters:",url_param
				
				if session.get("running") == None:	#new session
					session["running"]=0
					
					response="[Server] All good to go, ensure the listener is working ;-)\n"
					if not self.usefile:	#Used For Testing
						response+="[PROXY]\n"
					elif self.usefile:
						response+="[FILE]:"
						if os.name == 'posix':
							response+="[LINUX]\n"
						elif os.name == 'nt':
							response+="[WIN]\n"
						else:
							response+="[UNKNOWN]\n"
					self.send(response)
				else:
					if session.get("running") == 0:	
						sock = socket.socket()
						try:
							#TODO: if file does not exist use legacy tunna to connect to proxy
							if 'socks' in session:	#Start Socks Proxy
								self.startSocks(session)
								sock=session["socket"]
								session["running"]=1
								self.send("[OK] Proxy") #will proxy
								print "[+] Socket Connected To SocksProxy", sock.getpeername()
							else:					#Legacy connection
								if url_param.get('ip') and url_param.get('port'):
									sock.connect((url_param.get('ip'), int(url_param.get('port')))) 
									sock.setblocking(0)
									session["socket"]=sock
									session["running"]=1
									self.send("[OK]")	
									print "[+] Socket Connected", sock.getpeername(), sock
								else:
									print "[-] Missing Parameters to connect:", url_param
									self.send(("[-] Missing Parameters to connect: %s" % url_param),500)
						except Exception, e:
							self.send('[-] something\'s wrong with %s.\n\t Exception type is: %s' % (url_param, `e`))
							print "Exception:",session,e
					else:	#running	
						sock = socket.socket()
						sock = session.get("socket")
						#Read data from request and write to socket
						try:
							if 'Content-Length' in self.headers:	#Else is a get request
								postdata = self.rfile.read(int(self.headers['Content-Length']))
								sock.send(postdata)
							#Read Data from socket and write to response
							data=sock.recv(bufferSize)
							if data == "":
								self.send("[-] Socket Disconnected",500)
							else:
								self.send(data)
						except socket.error:
							self.send()
							
				if self.debug > 3: print "[debug] Session:", session
			else:
				self.send("Tunna v1.1a") #Version 1.1a

		def log_message(self, format, *args):
			if self.debug > 2: print ("[W] %s - - [%s] %s" % (self.address_string(),self.log_date_time_string(),format%args))

		def startSocks(self,session):
			#Create a Random port	
			SocksServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
			SocksServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			SocksServerSocket.setblocking(0) #DEL
			SocksServerSocket.bind(('localhost',0)) 
			
			if 'file' in session: #if file exists run file (used mainly for testing)
				f=session['file']
				if self.debug > 3: print "[Debug] starting socks executable"
				#./Uploaded Executable random_port
				self.fileRun(session,SocksServerSocket.getsockname()[1])
			else:	#else start proxy in thread
				if self.debug > 3: print "[Debug] starting internal socks"
				event = threading.Event()
				event.clear()	
				
				self.socksServer=SocksServer(SocksServerSocket,event)
				
				SocksThread = threading.Thread(name='SocketServer', target=	self.socksServer.run, args=())
				SocksThread.setDaemon(1)				#will exit if main exits
				SocksThread.start()
				
				if self.debug > 3: print "[Debug] waiting for event"
				event.wait() 
				
				session['SocksThread'] = SocksThread
			time.sleep(1)
			sock = socket.socket()
			sock.connect(('localhost',SocksServerSocket.getsockname()[1]))
			sock.setblocking(0)	
			session["socket"]=sock
			SocksServerSocket.close()
			
		def Session(self):
			sessions=self.sessions
			if self.cookie.has_key("sessionId"):
				sessionId=self.cookie["sessionId"].value

				if sessions.get(sessionId): return sessions.get(sessionId)
			else:	#Because life's too short
				sessionId=''.join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for i in range(32)])
				self.cookie["sessionId"]=sessionId
			try:
				sessions[sessionId]=dict()
			except KeyError:
				pass
			return sessions[sessionId]
		
		def invalidateSession(self):
			sessions=self.sessions
			if self.cookie.has_key("sessionId"):
				sessionId=self.cookie["sessionId"].value
				del sessions[sessionId]
		
		def close(self,session):
			#Clean up everything in session
			session["running"]=-1
			try:
				if 'SocksProcess' in session:
					if self.debug > 1: print "[-] Killing process", session['SocksProcess'].pid
					session['SocksProcess'].kill()
				if 'file' in session:
					if self.debug > 1: print "[-] Removing File", session['file'].name
					os.remove(session['file'].name)
				if 'SocksThread' in session:
					if self.debug > 1: print "[-] Killing Socks Thread"
					if hasattr(self,'socksServer'):	del self.socksServer
					t=session['SocksThread']
					t._Thread__stop()
					t.join()
			except Exception, e:
				print "[-]", e
			channel = socket.socket()
			channel = session.get("socket")
			if channel: 
				channel.close()
				self.send("[Server] Closing the connection")
			else:
				self.send("[Server] No open socket")
			self.invalidateSession()
			return
					
def banner():
	print " _______                   __          __  _     _____                          "
	print "|__   __|                  \\ \\        / / | |   / ____|                         "
	print "   | |_   _ _ __  _ __   __ \\ \\  /\\  / /__| |__| (___   ___ _ ____   _____ _ __ "
	print "   | | | | | '_ \\| '_ \\ / _` \\ \\/  \\/ / _ \\ '_ \\\\___ \\ / _ \\ '__\\ \\ / / _ \\ '__|"
	print "   | | |_| | | | | | | | (_| |\\  /\\  /  __/ |_) |___) |  __/ |   \\ V /  __/ |   "
	print "   |_|\\__,_|_| |_|_| |_|\\__,_| \\/  \\/ \\___|_.__/_____/ \\___|_|    \\_/ \\___|_|   "
	print ""

	print  "TunnaWebServer v1.1a, for HTTP tunneling TCP connections by Nikos Vassakis"
	print  "http://www.secforce.com / nikos.vassakis <at> secforce.com"
	print "###############################################################"
	print ""

def usage():
	#TODO: argparse
	print "Usage:"
	print "\t webserver.py -r <hostname:Port>"
	print "    --ssl:		for SSL server"

if __name__ == '__main__':
	banner()
	options={}
	try:
		opts, args = getopt.getopt(sys.argv[1:], "r:h", ["help","ssl"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	try:	
		for o, a in opts:
			if o in ("-h", "--help"):
				usage()
				sys.exit()
			elif o == "-r":
				try:
					options['hostname'], webServerPort= a.split(":")
					options['webServerPort']=int(webServerPort)
				except ValueError:
					options['webServerPort']=int(a)
			elif o == "--ssl":
				options['ssl']=True
			else:
				usage()
				sys.exit(2)
	except:
		usage()
		sys.exit(2)
	else:
		options=dict(Defaults.items() + options.items()) if options else Defaults
		try:
			WebServer(options)
		except KeyboardInterrupt:
				sys.exit()
