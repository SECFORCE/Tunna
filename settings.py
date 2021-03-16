Tunna_Defaults = {
    # Default Tunna Settings
    'bufferSize': 1024*8,  # Size of Socket Buffer
    'verbose': False,  # Verbose Print
    'ping_delay': 0.5,  # Delay between requests
    'interval': 0.2,
    'bind': '0.0.0.0', 	# Change to localhost for binding Tunna to localport
    'useSocks': True,  # Will use Socks Proxy if available
    'ignoreServerCert': True,

    # Default Remote Settings
    'local_port': 0,
    'remote_port': 0,
    'remote_ip': "127.0.0.1",
    # Start quering the socket first (eg. for SSH)
    'start_p_thread': False,

    # Set Up a Local Proxy
    'upProxy': None,  # autodetect
    'upProxyAuth': None,

    #! Not to be changed
    'ProxyFileWin': 'lib/socks4aServer.exe',
    'ProxyFilePy': 'lib/socks4aServer.py',

    #! HTTP headers
    'Cookie': '',
}

Webserver_Defaults = {
        # Default WebServer Settings
        'hostname': "0.0.0.0",  # Change to localhost for local connection
        'webServerPort': 8000,
        'ssl': False,

        # For Debug purposes
        'WDEBUG': 2,
        'USEFILE': False,

        # SSL Certificate
        'certificate': b'''
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDTZfKj8Ipq+POr
yQxS8ybw9KCpowCOTdmMq6mXrA35Q8BCZ6xsRImMGWIJ5OTUCw6ynOJxDo9+6XvX
YVrqJoPy/452n2NLX0Yq2RhHSD3RKwi/KjVKLIjvplHPxwYI/gotLMbzvRPd1Y/3
rDJXlxIeU+lFo7K1kXwz4G3u0AivIMR7izsMyvDfSXW4G98/ESogfM4a9LtgnMHL
Dj1iB1ruUMbPzYAmJ4j6Tq8dGUZ2T1QSFS4RA9Nb3as3TVrRDIZWhUL/A9uCIeQn
hp7JQJKQuIslKOAxdWtenBn3qzOm/5/Sk2RpSdHpsnUWxUQB4Mxr7gkNb5p+XwnE
Toti/0tvAgMBAAECggEAeSRO68uIRszrNmI8Abz9b89/0jZqtyG9rXMh+JzMVS+S
GXu3v0N3XyWcnPbievDrN0fYK9mgOaYrJb3Qj6YKr1HrneawzByI5T0LQK4RXrA+
ju3tI9hpkIvLDjqLJtQNmN20FTEhFVqw6clv/+m+pEqJvzKT0qDQgBn4ZYYps9EU
poYx2xxA9nqIzFUoWfYhqBsHHERQktMrq4KHxqSq/uMvA45kKv2VkpJwUDEL3mHt
njO+F5isEKLJ5LE6dPXTfZVGRfMHYCulDuSNka/qTEkUf1D2tK200dp5+BFondXC
B48v0sojCqL+6+GBk/XNrkcEuIBUFfpO5uhjtf+bwQKBgQDp+iVgc2nuKFouj24p
CnSZiR9yTgL7yb0tqNUXfwXimZeeMels1oTGt9hVI4vv6HnM6NVcrV2VVWAdQzS8
AxZOZzCHc67yyhyP4ZakeIRlIo/GUT8xJe2P3hA4yCqncQ0AhktKdvtac0i20OP2
uMwCCMx50ZEVD5vBeFfIrHtuiQKBgQDnS78QxIbM+2ck3bYM6tAgmEKByW5SH1dX
SPr8iybeJSEcWw1wlBawlxiCeV2YUsqDNOjrWdeRlimc2CCWeTegXhR+uB7p15n5
isXgQti5mmqHbBL6V6eHvn/bR1001Bnw0G5xBT40IzzvRwyzCDFFteffIFnJXRr9
sFWuyuMsNwKBgQClDT/GnUPxq+eKBsYID4cXM+LKCHwUUEiyZ/ICRCnLotuQzdbD
X0SExfXGgW/ayhz5zpmMagOlL3fAzMLriiX3ItXaB2I3hRnG6bURyq5ihZH0rSWt
rvq5TUYWOCXWvmoUn6eHHQ3MzZxS0mKtjcjj+n77xDjbKYqPXSxXtEzSOQKBgQCO
mVeZ6eBF/nVv+DUmL5rTjavrQpn+jY4WpUsAanYzHWcViVl24AZBJ1aYEmVO5TQv
wm4bs89A1fif12v3+ZH/ECHIopGEkEVA4XrvsabWf0pQZaQpreL+wMcpFQ105ZN8
sbR1f8sC7/rAduhwdIuUM/tZyCMzD3D1mUKqOjHm7wKBgC0t0xSvAKI4yPHZHg1p
rLtBR1y7io2IR0QqMtjw444C0GjfZrnTX2VIQjjlwbglAzpfeoKal1KxHvZaKPyW
FlTlja84ysjyAr9a3e/Ij/u+86U9QdP/yfZG8JfPD+6Lwr5FOJX2OkR99KiJwFSH
ek4j89uU4CS0WIsWsOLFjxhq
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIDazCCAlOgAwIBAgIUZm3Ruz3V0LraJVRzkfNMBG5WIqowDQYJKoZIhvcNAQEL
BQAwRTELMAkGA1UEBhMCR0IxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoM
GEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDAeFw0yMTAzMTYxMTU4NTVaFw0yMjAz
MTYxMTU4NTVaMEUxCzAJBgNVBAYTAkdCMRMwEQYDVQQIDApTb21lLVN0YXRlMSEw
HwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEB
AQUAA4IBDwAwggEKAoIBAQDTZfKj8Ipq+POryQxS8ybw9KCpowCOTdmMq6mXrA35
Q8BCZ6xsRImMGWIJ5OTUCw6ynOJxDo9+6XvXYVrqJoPy/452n2NLX0Yq2RhHSD3R
Kwi/KjVKLIjvplHPxwYI/gotLMbzvRPd1Y/3rDJXlxIeU+lFo7K1kXwz4G3u0Aiv
IMR7izsMyvDfSXW4G98/ESogfM4a9LtgnMHLDj1iB1ruUMbPzYAmJ4j6Tq8dGUZ2
T1QSFS4RA9Nb3as3TVrRDIZWhUL/A9uCIeQnhp7JQJKQuIslKOAxdWtenBn3qzOm
/5/Sk2RpSdHpsnUWxUQB4Mxr7gkNb5p+XwnEToti/0tvAgMBAAGjUzBRMB0GA1Ud
DgQWBBRNDdbFxPW7pNZIAsWw5vRVsjlvKTAfBgNVHSMEGDAWgBRNDdbFxPW7pNZI
AsWw5vRVsjlvKTAPBgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQCt
WezSK3/a2zIIC7JgG+TRK80X19FluUX8NQo/MQzzlFjTdXYOieWpK6yXlOFkhZes
CW/uh+UG9fPwOnyF0pPUvmZdvEcUKX7KVqhN3PKQws90pb/Ed8BfNk6b8iOlyEfF
4vL6wzVd+p2rJSme4MLH7JkYNxJK19fWo5hRKH2YDV26pKI8IP95NAVltHEV59pt
4pVoaAq2MwYijh8/Fda3qYKak9nSaZRb2Q5aQWO79EJd8sUYgPnsFnTGgzi1W4p1
0/ztt0BWnr+MMSypXZOg6FeUW0M31CWvuDRY7ZuWIUZYXoYMIzGeCKII/jfCNkZv
yDGDvevWlR9pWp2iyf0t
-----END CERTIFICATE-----
	'''
}

SocksServer_Defaults = {
    'buffersize': 1024*8,
    'backlog': 10
}
