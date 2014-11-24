Tunna
=====

Tunna is a set of tools which will wrap and tunnel any TCP communication over HTTP. It can be used to bypass network restrictions in fully firewalled environments. 

v0.1	Alpha version

					  _____                        
					 |_   _|   _ _ __  _ __   __ _ 
					   | || | | | '_ \| '_ \ / _` |
					   | || |_| | | | | | | | (_| |
					   |_| \__,_|_| |_|_| |_|\__,_|	
                                                     
 
                     Tunna 0.1, for HTTP tunneling TCP connections by Nikos Vassakis
                     http://www.secforce.co.uk	/ nikos.vassakis <at> secforce.com


################################################################################################################

High level Diagram:

 +-------------------------------------------+                     +-------------------------------------------+
 | Local Host                                |                     | Remote Host                               |
 |-------------------------------------------|                     |-------------------------------------------|
 |   +----------+       +------------+       |   +-------------+   |   +------------+        +----------+      |
 |   |Client App|+----->|Local Proxy |<==========|  Firewall   |======>|  Webshell  |+------>|Server App|      |
 |   +----------+       +------------+       |   +-------------+   |   +------------+        +----------+      |
 +-------------------------------------------+                     +------------------------------------------ +


Technical Diagram:

 +-------------------------------------------+                     +-------------------------------------------+
 | Local Host                                |                     | Remote Host                               |
 |-------------------------------------------|                     |-------------------------------------------|
 |                                           |                     |                                           |
 |                   +-----------------+     |                     |     +-----------------+                   |
 |                   |   Local Proxy   |     |                     |     | Web Shell (URL) |                   |
 |                   |-----------------|     |                     |     |-----------------|                   |
 |                   | +-------------+ |     |                     |     |                 |                   |
 |                   | |HTTP encap.  | |     |   HTTP Traffic      |     |  +-----------+  |                   |
 |                   | +------^------+ <=================================>  |HTTP-->Sock|  |                   |
 |                   |        |        |     |                     |     |  +-----+-----+  |                   |
 |                   | +------+------+ |     |                     |     |        |        |                   |
 |                   +-|  Local Port |-+     |                     |     +--------v--------+                   |
 |                     +------^------+       |                     |              |                            |
 |                            |              |                     |              |                            |
 |  +----------------+        |              |                     |              |        +----------------+  |
 |  |Local Client    |        |              |                     |              +--------> Remote Service |  |
 |  |----------------|        |              |                     |                       |----------------|  |
 |  |Connect to local|        |              |                     |                       |Connection      |  |
 |  |Socket          |        |              |                     |                       |received from   |  |
 |  |                +--------+              |                     |                       |localhost       |  |
 |  |                |                       |                     |                       |                |  |
 |  |                |                       |                     |                       |                |  |
 |  +----------------+                       |                     |                       +----------------+  |
 +-------------------------------------------+                     +-------------------------------------------+


SUMMARY
=======

	TLDR: Tunnels TCP connections over HTTP

In a fully firewalled (inbound and outbound connections restricted - except the webserver port)

The webshell can be used to connect to any service on the remote host. 
This would be a local connection on a local port at the remote host and *should* be allowed by the firewall.

The webshell will read data from the service port wrap them over HTTP and send it as an HTTP response to the
local proxy.

The local proxy will unwrap and write the data to its local port where the client program would be connected.

When the local proxy receives data on the local port, it will send them over to the webshell as an HTTP Post.

The webshell will read the data from the HTTP Post and put them on the service port

and repeat --^

Only the webserver port needs to be open (typically 80 - *not really tested over 443 SSL)
The whole communication (Externally) is done over the HTTP protocol
Theoretically (UNTESTED) the webshell can connect to any other remote host / remote service:
	* There are some webserver limitations - not allowing external socket connections etc.


USAGE
======

	ruby proxy.rb -u <remoteurl> -p <localport> -r <remote_service_port> [options]
or
	python proxy.py -u <remoteurl> -p <localport> -r <remote_service_port> [options]

    -u, --url URL                    url of the remote webshell
    -l, --lport PORT                 local port of proxy
    -r, --rport PORT                 remote port of service for the webshell to connect to
    -q, --ping-interval NUM          webshprx pinging thread interval (default = 0.5)
    -a, --addr IP                    address for remote webshell to connect to (default = 127.0.0.1)
*   -b, --buffer BUFF                HTTP request size (some webshels have limitations on the size)
    -s, --start-ping                 start the pinging thread first - some services send data first (SSH)
    -v, --verbose                    verbose output - for debugging purposes
    -h, --help                       Display this screen

* See limitations

example usage:
	ruby proxy.rb -u http://10.3.3.1/conn.aspx -l 4444 -r 3389 -b 8192 -v

	# This will initiate a connection between the webshell and Remote host RDP (3389) service
	# The RDP client can connect on localhost port 4444
	# This connection will be wrapped over HTTP


Prerequisites
=============

	The ability to upload a webshell on the remote server


LIMITATIONS / KNOWN BUGS / HACKS
================================
	
	This is a POC code and might cause DoS of the server.
		All efforts to clean up after execution or on error have been made ... but no promises

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
		
	
FILES
=====

	Webshells:
		conn.jsp	Tested on Apache Tomcat (windows + linux)
		conn.aspx	Tested on IIS 6+8 (windows server 2003/2012) 
		conn.php	Tested on LAMP + XAMPP + IIS (windows + linux)

	Proxies:
		proxy.rb	Tested with ruby 1.9.2 	
		proxy.py	Tested with Python 2.6.5


Technical Details
=================

 Architecture descisions
 -----------------------
	Data is sent raw in the HTTP Post Body (no post variable)
		To save a couple of bytes

	Instructions / configuration is sent to the webshell as URL parameters (HTTP Get)
	Data is sent in the HTTP body (HTTP Post)

	Websockets not used: Not supported by default by most of webservers (Maybe futrure dev)
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

 PROXY
 -----
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


COPYRIGHT & DISCLAIMER
======================

Tunna, TCP Tunneling Over HTTP
Nikos Vassakis
Copyright (C) 2013 SECFORCE.

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
