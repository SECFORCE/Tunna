 #Tested with ruby 1.9.2 
require "socket"
require "net/http"
require "net/https"
require 'thread'
require "uri"
require "zlib"
require 'optparse'

Thread.abort_on_exception = true

class HTTPwrapper
	def initialize( url , remote_ip=nil , remote_port=0, verbose=0 )
		@uri = URI(url)
		@url=@uri.path+"?proxy"
		#init v_print variables
		if verbose then
			@send=0
			@received=0
			@received_pt=0
			@pings=0
		end
		#Add http headers for cookie and encoding
		@headers = {
			'Accept-encoding' => 'gzip',
			'Content-Type' => 'application/octet-stream'
		}
		#1st request: get cookie
		data = HTTPreq(@url)
		puts data	#print response
		#2nd request: send connection config - this thread stalls in PHP
		@t = Thread.new { Threaded_request(remote_port,remote_ip)}
		sleep(2)
	end
	
	def HTTPreq(url, data="",timeout=300)			#HTTP wrapper
		http = Net::HTTP.new(@uri.host,@uri.port)	
		http.open_timeout = timeout					#Set ruby response timeout
		http.read_timeout = timeout

		if data then	#If data make a HTTP Post request
			resp, data = http.post(url, data, @headers)	
		else  			#If no data make a HTTP Get request
			resp, data = http.get(url, @headers)
		end
		
		#If cookie was not set: set it now
		@headers['Cookie'] = resp.response['set-cookie'] if !@headers.has_key?('Cookie')	

		#If response is gzip encoded: decode it
		if resp.header[ 'Content-Encoding' ].eql?( 'gzip' ) then	
			f = StringIO.new( resp.body )
			url_f = Zlib::GzipReader.new( f )
			data = url_f.read()	
		else 						#Response is not encoded
			data = resp.body
		end	
		
		if resp.code == '200' then
			return data				#return response
		else 						#Something went wrong: print response and exit
			puts "[-] Received status code " + resp.code
			puts resp.body
			exit
		end
	end
	
	def Threaded_request(remote_port, remote_ip=nil)
		#Sends connection options to the webshell
		#In php this thread will stall to keep the connection alive (will not receive response)
		#In other langs [OK] is received
		puts '[+] Spawning keep-alive thread'
		if remote_ip then							#sends webshell config [port and ip to connect to]
			resp = HTTPreq(@url+"&port="+remote_port.to_s()+"&ip="+remote_ip.to_s(),nil,36000)	#set timeout of request 
		else 										#Else use webshell defaults
			resp = HTTPreq(@url+"&port="+remote_port.to_s(),nil,36000)
		end
		if(resp.strip != '[OK]') then 				#if ok is not received something went wrong (if nothing is received: it's a PHP webshell)
			puts resp
			Thread.main.raise "[-] Keep-alive thread exited"
		else 										#If ok is received (non-php webshell): Thread not needed
			puts '[-] Keep-alive thread not required'
		end
	end
	
	def v_print(options={})	#Verbose output for Debugging
		options = {:sent_d => 0, :received_d => 0, :received_d_pt => 0, :pings_n => 0}.merge(options)
		@send+=options[:sent_d]
		@received+=options[:received_d]
		@received_pt+=options[:received_d_pt]
		@pings+=options[:pings_n]
		
		$stdout.sync = true
		$stdout.write("\x1b[2J\x1b[H")	#Unix only
		
		print "Received Data: %d (%d)\nReceived Data From Ping Thread: %d (%d) \nSent data: %d (%d) \nPings sent: %d\r\n" % [@received, options[:received_d], @received_pt,options[:received_d_pt], @send, options[:sent_d], @pings]
		$stdout.flush()
	end
	
	def clean_up			#On exit 
		Thread.kill(@t)		#Kill thread_request thread
	end
end	#wrapper

class SocketServer
	def initialize( options={})
		#init required variables		
		@url = options[:url]+"?proxy"
		local_port = options[:local_port]
		remote_port = options[:remote_port]
		@bufferSize = options[:bufferSize]
		#init local socket
		@descriptors = Array::new
		@serverSocket = TCPServer.new( "", local_port )
		@serverSocket.setsockopt(Socket::SOL_SOCKET,Socket::SO_REUSEADDR, true )
		#init options
		remote_ip = options[:remote_ip] 
		@ping_delay = options[:ping_delay]
		@start_p_thread = options[:start_p_thread] 
		@verbose = options[:verbose]
		#init_tunnel
		@http=HTTPwrapper.new(@url,remote_ip,remote_port, @verbose)
		#Mux: To ensure that only one HTTP request is made at a time
		@mutex = Mutex.new
		@mutex_http_req = Mutex.new
	end # initialize

	def init_ping_thread(start=0)
		@pt = Thread.new { Pinging_Thread(@ping_delay); }
		if start then
			@pt.run
		end
	end
	
	def Pinging_Thread(interval)
		sleep
		puts "[+] Starting Ping thread"
		wait=true
		while 1											#loop forever
			sleep(interval) if wait	== true				#send ping to server interval
			@mutex_http_req.synchronize do 				#Ensure that the other thread is not making a request at this time
				resp_data=@http.HTTPreq(@url,nil)		#Read response
					@http.v_print({:pings_n => 1}) if @verbose
				if resp_data != "" then					#If response had data write them to socket
					@http.v_print({:received_d_pt => resp_data.length}) if @verbose
					@sock.write(resp_data)				#write to socket
					resp_data=""						#clear data
					#not clearing flag in case more data avail.
					wait=false							#Dont wait: if there was data probably there are more
				else
					wait=true
				end
			end
		end	
		Thread.main.raise "[-] Pinging Thread Exited"	
	end #pinging thread
	
	def run
		data=nil
		while 1
			if (@sock = @serverSocket.accept) then
				accept_new_connection							# Will block until: receives a connect to the server (listening) socket
				while 1		
					if @sock.eof? or @sock.closed? then			# If client disconnects: raise exception -> will exit 
						Thread.main.raise("[-] Client disconnected %s:%s\n" % [@sock.peeraddr[2], @sock.peeraddr[1]])
					else
						data = @sock.read_nonblock(@bufferSize)	#Read Data from socket
						if data != "" then						#If there was data send them over HTTP (post)
							@mutex_http_req.synchronize do 		#Ensure that the other thread is not making a request at this time
														
								if @start_p_thread == false		#Starts pinging thread (Will only run after first data is read from socket)
									@pt.run
									@start_p_thread = true
								end
								
								@http.v_print({:sent_d => data.length}) if @verbose
								resp_data=@http.HTTPreq(@url,data)		#send data with a HTTP post
								if resp_data != "" then					#If data is received back write them to socket
									@http.v_print({:received_d => resp_data.length}) if @verbose
									@sock.write(resp_data)				#Write data to socket
									resp_data=""						#clear data			
								end		
							end
						end
					end
				end
			end
		end
	end #run
	
	def clean_up
		#Kills threads & send close command to remote server
		@sock.close if defined?(@sock)				#close socket
		Thread.kill(@pt) if defined?(@pt)			#Kill pinging thread
		puts @http.HTTPreq(@url+"&close").strip()	#Send close command to webshell
		@http.clean_up								#Call class clean_up
	end

	private

	def accept_new_connection	#Client connected to socket
		printf("[+] Connected from %s:%s\n", @sock.peeraddr[2], @sock.peeraddr[1])
		init_ping_thread(@start_p_thread)	#Spawn pinging thread - will sleep/start execution depending on bool var start_p_thread
	end # accept_new_connection
end #server


def usage
	puts "  _____                        "
	puts " |_   _|   _ _ __  _ __   __ _ "
	puts "   | || | | | '_ \\| '_ \\ / _` |"
	puts "   | || |_| | | | | | | | (_| |"
	puts "   |_| \\__,_|_| |_|_| |_|\\__,_|"
	puts ""

	puts  "Tunna v0.1, for HTTP tunneling TCP connections by Nikos Vassakis"
	puts  "http://www.secforce.com / nikos.vassakis <at> secforce.com"
	puts "###############################################################"
	puts ""
end

def get_arguments
	#props: http://stackoverflow.com/questions/1541294/how-do-you-specify-a-required-switch-not-argument-with-ruby-optionparser
	usage
	options = {}
	optparse = OptionParser.new do |opts|
	opts.banner = "Usage: ruby proxy.rb -u <remoteurl> -l <localport> -r <remote_service_port> [options]"
	
	opts.on('-u', '--url URL', 'url of the remote webshell') do |url|
		options[:url] = url
	end

	opts.on('-l', '--lport PORT', Integer, 'local port of webshprx') do |lport|
		options[:local_port] = lport
	end

	opts.on('-r', '--rport PORT', Integer, 'remote port of service for the webshell to connect to') do |rport|
		options[:remote_port] = rport
	end

	opts.on('-q', '--ping-interval NUM', Float, 'webshprx pinging thread interval (default = 0.5)') do |interval|
		options[:ping_delay] = interval
	end

	opts.on('-a', '--addr IP', 'address for remote webshell to connect to (default = 127.0.0.1)') do |addr|
		options[:remote_ip] = addr
	end
	
	opts.on('-b', '--buffer BUFF', Integer, 'HTTP request size (some webshels have limitations on the size)') do |bufferSize|
		options[:bufferSize] = bufferSize
	end
	
	opts.on('-s', '--start-ping', 'start the pinging thread first - some services send data first (SSH)') do 
		options[:start_p_thread] = true
	end
	  
	opts.on('-v', '--verbose', 'verbose output') do 
		options[:verbose] = true
	end

	opts.on('-h', '--help', 'Display this screen') do
		usage
		puts opts
		exit
	end
	end

	begin
		optparse.parse!
		mandatory = [:url, :local_port, :remote_port]	#required switches
		missing = mandatory.select{ |param| options[param].nil? }
		if not missing.empty?
			puts "Missing options: #{missing.join(', ')}"
			puts optparse
			exit
		end
		return options
	rescue OptionParser::InvalidOption, OptionParser::MissingArgument
		puts $!.to_s	# Friendly output when parsing fails
		puts optparse
		exit
	end    
end

begin

defaults={
	:remote_ip => "127.0.0.1", 
	:ping_delay => 0.5, 
	:start_p_thread => false, 
	:verbose => false,
	:bufferSize => 8192
}
options = defaults.merge(get_arguments())

puts "[+] Local Proxy listening at localhost:%d\n\t Remote service to connect to %s -> %s:%d" % [options[:local_port],options[:url],options[:remote_ip],options[:remote_port]]

Server = SocketServer.new( options )
Server.run()

rescue Exception => e
    puts "#{e.message}"
    if defined?(Server) then
		Server.clean_up
	end
end
