#!/usr/bin/python
#  _____
# |_   _|   _ _ __  _ __   __ _
#   | || | | | '_ \| '_ \ / _` |
#   | || |_| | | | | | | | (_| |
#   |_| \__,_|_| |_|_| |_|\__,_|
#
#Tunna v1.1a, for HTTP tunneling TCP connections by Nikos Vassakis
#http://www.secforce.com / nikos.vassakis <at> secforce.com
########################################################################
#Tested with Python 2.6.5

from time import time, sleep, asctime
import threading, thread
import optparse
import sys
import urllib2
from base64 import b64encode
from lib.TunnaClient import TunnaClient

from settings import Tunna_Defaults as Defaults

DEBUG=0

def banner():
	print "  _____                        "
	print " |_   _|   _ _ __  _ __   __ _ "
	print "   | || | | | '_ \\| '_ \\ / _` |"
	print "   | || |_| | | | | | | | (_| |"
	print "   |_| \\__,_|_| |_|_| |_|\\__,_|"
	print ""

	print  "Tunna v1.1a, for HTTP tunneling TCP connections by Nikos Vassakis"
	print  "http://www.secforce.com / nikos.vassakis <at> secforce.com"
	print "###############################################################"
	print ""

def main():
	banner()
	parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter())

	parser.set_usage("python proxy.py -u <remoteurl> -l <localport> [options]")

	parser.add_option('-u','--url', help='url of the remote webshell', dest='url', action='store')
	parser.add_option('-l','--lport', help='local listening port', dest='local_port', action='store', type='int')
	#Verbosity
	parser.add_option('-v','--verbose', help='Verbose (outputs packet size)', dest='verbose', action='store_true',default=Defaults['verbose'])
	#Legacy options
	legacyGroup = optparse.OptionGroup(parser, "No SOCKS Options","Options are ignored if SOCKS proxy is used")
	legacyGroup.add_option('-n','--no-socks', help='Do not use Socks Proxy', dest='useSocks', action='store_false',default=Defaults['useSocks'])
	legacyGroup.add_option('-r','--rport', help='remote port of service for the webshell to connect to', dest='remote_port', action='store', type='int',default=Defaults['remote_port'])
	legacyGroup.add_option('-a','--addr', help='address for remote webshell to connect to (default = 127.0.0.1)', dest='remote_ip', action='store',default=Defaults['remote_ip'])
	parser.add_option_group(legacyGroup)
	#Proxy options
	proxyGroup = optparse.OptionGroup(parser, "Upstream Proxy Options", "Tunnel connection through a local Proxy")
	proxyGroup.add_option('-x','--up-proxy', help='Upstream proxy (http://proxyserver.com:3128)', dest='upProxy', action='store', default=Defaults['upProxy'])
	proxyGroup.add_option('-A','--auth', help='Upstream proxy requires authentication', dest='upProxyAuth', action='store_true', default=Defaults['upProxyAuth'])
	parser.add_option_group(proxyGroup)
	#Advanced options
	advancedGroup = optparse.OptionGroup(parser, "Advanced Options")
	parser.add_option('-b','--buffer', help='HTTP request size (some webshels have limitations on the size)', dest='bufferSize', action='store', type='int', default=Defaults['bufferSize'])
	advancedGroup.add_option('-q','--ping-interval', help='webshprx pinging thread interval (default = 0.5)', dest='ping_delay', action='store', type='float', default=Defaults['ping_delay'])
	advancedGroup.add_option('-s','--start-ping', help='Start the pinging thread first - some services send data first (eg. SSH)', dest='start_p_thread', action='store_true', default=Defaults['start_p_thread'])
	advancedGroup.add_option('-c','--verify-server-cert', help='Verify Server Certificate', dest='start_p_thread', action='store_false', default=Defaults['ignoreServerCert'])
	advancedGroup.add_option('-C','--cookie', help='Request cookies', dest='cookie', action='store')
        advancedGroup.add_option('-t','--authentication', help='Basic authentication (username:password or \'-\' for stdin input', dest='bauth', action='store', default='no')

	parser.add_option_group(advancedGroup)

	(args, opts) = parser.parse_args()

	options=dict(Defaults.items() + vars(args).items()) if args else Defaults	#If missing options use Default

	if options['remote_port']:
		options['useSocks']=False

	if not options['local_port']:
		parser.print_help()
		parser.error("Missing local port")
	if not options['url']:
		parser.print_help()
		parser.error("Missing URL")
	if options['upProxyAuth']:	#Upstream Proxy requires authentication
		username=raw_input("Proxy Authentication\nUsername:")
		from getpass import getpass
		passwd=getpass("Password:")

		if not options['upProxy']:
			parser.error("Missing Proxy URL")
		else:
			from urlparse import urlparse
			u=urlparse(options['upProxy'])
			prx="%s://%s:%s@%s" % (u.scheme,username,passwd,u.netloc)

			password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
			password_mgr.add_password(None,prx,username,passwd)

			proxy_handler = urllib2.ProxyHandler({u.scheme:prx})
			proxy_basic_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
			proxy_digest_handler = urllib2.ProxyDigestAuthHandler(password_mgr)

			options['upProxyAuth']=[proxy_handler,proxy_basic_handler,proxy_digest_handler]
        if not options['bauth'] == 'no':            # Basic authentication
            if options['bauth'] == '-':
                username=raw_input("Basic Authentication\nUsername:")
                from getpass import getpass
                passwd=getpass("Password:")
            else:
                username, passwd = options['bauth'].split(':')

            options['bauth'] = b64encode('%s:%s' % (username, passwd))

	try:
		T=TunnaClient(options)
		TunnaThread = threading.Thread(name='TunnaThread', target=T.run(), args=(options,))
		TunnaThread.start()

		while True:
			sleep(10)

	except (KeyboardInterrupt, SystemExit) as e:
		print '[!] Received Interrupt or Something Went Wrong'
		if DEBUG > 0:
			import traceback
			print traceback.format_exc()

		if 'T' in locals():
			T.__del__()
		if 'TunnaThread' in locals() and TunnaThread.isAlive(): TunnaThread._Thread__stop()
		sys.exit()
	except Exception as e:
		if DEBUG > 0:
			import traceback
			print traceback.format_exc()
		print "General Exception:",e

def startTunna(options):
	T=TunnaClient(options)
	T.run()

if __name__ == "__main__":
	main()

