Tunna_Defaults ={
	#Default Tunna Settings
	'bufferSize':1024*8,	# Size of Socket Buffer
	'verbose':False,	# Verbose Print
	'ping_delay':0.5,	# Delay between requests
	'interval':0.2,
	'bind':'0.0.0.0', 	# Change to localhost for binding Tunna to localport	
	'useSocks':True,	# Will use Socks Proxy if available
	'ignoreServerCert':True,
	
	# Default Remote Settings
	'local_port':0,
	'remote_port':0,
	'remote_ip':"127.0.0.1",
	'start_p_thread':False,	# Start quering the socket first (eg. for SSH)

	#Set Up a Local Proxy
	'upProxy':None,	#autodetect
	'upProxyAuth':None,

	#! Not to be changed
	'ProxyFileWin':'lib/socks4aServer.exe',
	'ProxyFilePy':'lib/socks4aServer.py',

	#! HTTP headers
	'Cookie':'',
}

Webserver_Defaults ={
	#Default WebServer Settings
	'hostname':"0.0.0.0",	#Change to localhost for local connection
	'webServerPort':8000,
	'ssl':False,

	# For Debug purposes
	'WDEBUG':2,
	'USEFILE':False,
	
	#SSL Certificate
	'certificate':'''
-----BEGIN PRIVATE KEY-----
MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBAOKdz+7Zm+Fjq6qw
4rwDvRl7XLwR2CNclfXlH3Ff8eLEZDpiEqJs47zKHAYBF5aEevIRGYMqbsErUYCC
Gu504KxZOgGoGmd8r3oDbqJp0pPovMbVPZOV0Ms+Q1fAHHfBN5+lLm3eovhVQ54G
4ADHjU2P8BJ21VEkwBf5y35vNAkLAgMBAAECgYEAq9O1AgoF49RLKdWNVboP++5J
1mBBXi6plhTwzmpNYgA/bvVF49pko5UrwnG5jOtOvZSxn37hE57g4WvFN+FvKFF2
PFO3X4Shg4Rn84ZejoOhGs2KeGodZ/UbeU1qKm6N4kvLUPLFyyCnT875MbfXUozh
Py+iaRzntvfBrSokyiECQQD+7EUcpeecMfIrRXVJxpak0HbscxvwfWAcKkt3a500
Q7w8jkWeLyrb2jmoTVnsp89kzR2CyZkuUOWQHrpSmR4FAkEA45Ls5jBgfhY/doHe
b5l41XjMN6WnPqxeMx9CRQFDRXcw/DRGrW2m5/SRptYS+W46aW6v39J3+0sYHv3z
4SonzwJAR8IackYBPGaS1LtomKveG+bSkxyT8M5aD5OYSrVwOxYWFrW1wyFj3x8+
u7GKbqOOLcHPXNGC3RbIiBkeOcIAQQJACzETk3J3nFvNvS8/2C8tARqSuH3eDrf9
XfhAkxIv07+72ftcKnVFCw09CH5oqnmgR8UYwyIfom0b/5IvpzgigwJBAJSiZXBJ
LsaVAOBetNmymX/EMoQEqNZCqi2ajVMwQEkXEnAOIz7sj1GGBdm4UMy+dCy4hR/V
EY6wtgLRqgpaUN0=
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIICMjCCAZugAwIBAgIJAKKavRy2ij+ZMA0GCSqGSIb3DQEBBQUAMDIxCzAJBgNV
BAYTAkdCMRMwEQYDVQQIDApTb21lLVN0YXRlMQ4wDAYDVQQKDAVUdW5uYTAeFw0x
NDA3MDMxMzQ2MzNaFw0xNTA3MDMxMzQ2MzNaMDIxCzAJBgNVBAYTAkdCMRMwEQYD
VQQIDApTb21lLVN0YXRlMQ4wDAYDVQQKDAVUdW5uYTCBnzANBgkqhkiG9w0BAQEF
AAOBjQAwgYkCgYEA4p3P7tmb4WOrqrDivAO9GXtcvBHYI1yV9eUfcV/x4sRkOmIS
omzjvMocBgEXloR68hEZgypuwStRgIIa7nTgrFk6AagaZ3yvegNuomnSk+i8xtU9
k5XQyz5DV8Acd8E3n6Uubd6i+FVDngbgAMeNTY/wEnbVUSTAF/nLfm80CQsCAwEA
AaNQME4wHQYDVR0OBBYEFNlKP/pXnWoVqmxDwmSFSjTBbDnFMB8GA1UdIwQYMBaA
FNlKP/pXnWoVqmxDwmSFSjTBbDnFMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEF
BQADgYEAM4CnP9QXKHljQ/gCble052+LfSwPWryRjwxTy3qlEpmSKb4UT6GlqABV
Cm2clM978TeCgsvOqsYya5iza/Gp8miKCmQ6WWxxiSm/J7QVHcaWIK9hqoPC6AXa
I9iUqOJ9Esv2NuHYxG4XWtYfyttktIJcuAhQ/3IfZZJ9SKZTIPs=
-----END CERTIFICATE-----
	'''
}

SocksServer_Defaults={
	'buffersize':1024*8,
	'backlog':10
}

