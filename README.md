Tunna
=====

Tunna is a set of tools which will wrap and tunnel any TCP communication over HTTP. It can be used to bypass network restrictions in fully firewalled environments. 

v1.1	Alpha version

					  _____                        
					 |_   _|   _ _ __  _ __   __ _ 
					   | || | | | '_ \| '_ \ / _` |
					   | || |_| | | | | | | | (_| |
					   |_| \__,_|_| |_|_| |_|\__,_|	
                                                     
 
                     Tunna 0.1, for HTTP tunneling TCP connections by Nikos Vassakis
                     http://www.secforce.co.uk	/ nikos.vassakis <at> secforce.com


################################################################################################################

SUMMARY
=======

	TLDR: Tunnels TCP connections over HTTP

In a fully firewalled (inbound and outbound connections restricted - except the webserver port)

The webshell can be used to connect to any service on the remote host. 
This would be a local connection on a local port at the remote host and *should* be allowed by the firewall.

The webshell will read data from the service port wrap them over HTTP and send it as an HTTP response to the
local proxy.

The local proxy will unwrap and write the data to it's local port where the client program would be connected.

When the local proxy receives data on the local port, it will send them over to the webshell as an HTTP Post.

The webshell will read the data from the HTTP Post and put them on the service port

and repeat --^

Only the webserver port needs to be open (typically 80/443)
The whole communication (Externally) is done over the HTTP protocol


USAGE
======
  `python proxy.py -u <remoteurl> -l <localport> [options]`

Options
=======
`--help, -h`              	show this help message and exit

`--url=URL, -u URL`       	url of the remote webshell

`--lport=LOCAL_PORT, -l` 	LOCAL_PORT
                        	local listening port

`--verbose, -v`           	Verbose (outputs packet size)

`--buffer=BUFFERSIZE, -b BUFFERSIZE*`
                        	HTTP request size (some webshels have limitations on
                        	the size)

No SOCKS Options
----------------
Options are ignored if SOCKS proxy is used

`--no-socks, -n`         		Do not use Socks Proxy

`--rport=REMOTE_PORT, -r`	REMOTE_PORT
                        	remote port of service for the webshell to connect to

`--addr=REMOTE_IP, -a REMOTE_IP`
	                        address for remote webshell to connect to (default =
        	                127.0.0.1)

Upstream Proxy Options
----------------------
Tunnel connection through a local Proxy

`--up-proxy=UPPROXY, -x` 	UPPROXY
                        	Upstream proxy (http://proxyserver.com:3128)

`--auth, -A`              	Upstream proxy requires authentication

Advanced Options
----------------
`--ping-interval=PING_DELAY, -q` 	PING_DELAY
                        	webshprx pinging thread interval (default = 0.5)

`--start-ping, -s`        	Start the pinging thread first - some services send
                        	data first (eg. SSH)

`--cookie, -C`        	Request cookies

`--authentication, -t`    Basic authentication


* See limitations

example usage:
	`python proxy.py -u http://10.3.3.1/conn.aspx -l 8000 -v`

	# This will start a Local SOCKS Proxy Server at port 80000
	# This connection will be wrapped over HTTP and unwrapped at the remote server

	python proxy.py -u http://10.3.3.1/conn.aspx -l 8000 -x https://192.168.1.100:3128 -A -v

	# This will start a Local SOCKS Proxy Server at port 80000
	# It will connect through a Local Proxy (https://192.168.1.100:3128) that requires authentication
	# to the remote Tunna webshell

	python proxy.py -u http://10.3.3.1/conn.aspx -l 4444 -r 3389 -b 8192 -v --no-socks

	# This will initiate a connection between the webshell and Remote host RDP (3389) service
	# The RDP client can connect on localhost port 4444
	# This connection will be wrapped over HTTP




Prerequisites
=============

	The ability to upload a webshell on the remote server


LIMITATIONS / KNOWN BUGS / HACKS
================================
	
	This is a POC code and might cause DoS of the server.
		All efforts to clean up after execution or on error have been made (no promises)

	Based on local tests: 		
		* JSP buffer needs to be limited (buffer option):
				4096 worked in Linux Apache Tomcat
				1024 worked in XAMPP Apache Tomcat (slow)
				* More than that created problems with bytes missing at the remote socket
				eg: ruby proxy.rb -u http://10.3.3.1/conn.jsp -l 4444 -r 3389 -b 1024 -v

		* Sockets not enabled by default php windows (IIS + PHP)
		
		* Return cariages on webshells (outside the code): 
			get sent on responses / get written on local socket --> corrupt the packets

		* PHP webshell for windows: the loop function DoS'es the remote socket: 
			sleep function added -> works but a bit slow 
		* PHP webshell needs new line characters removed at the end of the file (after "?>")
			as these will get send in every response and confuse Tunna 
		
	
FILES
=====

	Webshells:
		conn.jsp	Tested on Apache Tomcat (windows + linux)
		conn.aspx	Tested on IIS 6+8 (windows server 2003/2012) 
		conn.php	Tested on LAMP + XAMPP + IIS (windows + linux)

	WebServer:
		webserver.py	Tested with Python 2.6.5

	Proxies:
		proxy.py	Tested with Python 2.6.5
	

Technical Details
=================

 Architecture descisions
 -----------------------
	Data is sent raw in the HTTP Post Body (no post variable)

	Instructions / configuration is sent to the webshell as URL parameters (HTTP Get)
	Data is sent in the HTTP body (HTTP Post)

	Websockets not used: Not supported by default by most of webservers
	Asyncronous HTTP responses not really possible
		Proxy queries the server constantly (default 0.5 seconds)


 INITIATION PHASE
 ----------------
	
1st packet initiates a session with the webshell - gets a cookie back
	eg: http://webserver/conn.ext?proxy 	

2nd packet sends connection configuration options to the webshell
	eg: http://webserver/conn.ext?proxy&port=4444&ip=127.0.0.1
	
	IP and port for the webshell to connect to
	This is a threaded request:
		In php this request will go into an infinate loop 
		to keep the webshell socket connection alive
		In other webshells [OK] is received back

 TUNNA CLIENT
 ------------
A local socket is going to get created where the client program is going to connect to
Once the client is connected the pinging thread is initiated and execution starts.
Any data on the socket (from the client) get read and get sent as a HTTP Post request
Any data on the webshell socket get sent as a response to the POST request

 PINGING THREAD
 --------------
Because HTTP responses cannot be asyncronous. 
This thread will do HTTP Get requests on the webshell based on an interval (default 0.5 sec)
If the webshell has data to send, it will (also) send it as a reply to this request
Otherwise it sends an empty response

In general:
	Data from the local proxy get send with HTTP Post
	There are Get requests every 0.5 sec to query the webshell for data
	If there is data on the webshell side get send over as a response to one of these requests	

 WEBSHELL
 --------
The webshell connects to a socket on the local or a remote host. 
Any data written on the socket get sent back to the proxy as a reply to a request (POST/GET)
Any data received with a post get written to the socket.

 NOTES
 -----
All requests need to have the URL parameter "proxy" set to be handled by the webshell
	(http://webserver/conn.ext?proxy)
 
 AT EXIT / AT ERROR
 ------------------
Kills all threads and closes local socket
Sends proxy&close to webshell:
	Kills remote threads and closes socket	

 SOCKS
 -----
The SOCKS support is an addon module for Tunna. Locally is a seperate thread that handles the connection 
requests and traffic adds a header that specifies the port and the size of the packet and forwards it to 
Tunna. Tunna sends it over to the remote webserver, removes the HTTP headers and forwards the packet to
the remote SOCKS proxy. The remote SOCKS proxy initiates the connection and mapps the received port to
the local port. If the remote SOCKS proxy receives data from the service, it looks at the mapping table
and finds the port it needs to respond to, adds the port as a header so the local SOCKS proxy will know where
to forward the data. Any traffic from the received port will be forwarded to the local port and vice versa.
 

COPYRIGHT & DISCLAIMER
======================

Tunna, TCP Tunneling Over HTTP
Nikos Vassakis
Copyright (C) 2014 SECFORCE.

This tool is for legal purposes only.

This program is free software: you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the 
Free Software Foundation, either version 3 of the License, or (at your 
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General 
Public License for more details.

You should have received a copy of the GNU General Public License along 
with this program. If not, see <http://www.gnu.org/licenses/>.
