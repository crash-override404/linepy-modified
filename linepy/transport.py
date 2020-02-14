# -*- coding: utf-8 -*-
from io import BytesIO
from six.moves import urllib, http_client
import os, socket, sys, warnings, base64, time, json, asyncio, six
import hyper, httpx, httplib2

from thrift.transport.TTransport import TTransportBase
try:
    from thrift.protocol import fastbinary
except ImportError:
    fastbinary = None

class THttpClient(TTransportBase):
    '''Http implementation of TTransport base.'''

    def __init__(self, uri_or_host, port=None, path=None, customThrift=False, request='httplib', http2=False, proxy_host=None, proxy_port=None, proxy_auth=None):
        '''THttpClient supports two different types constructor parameters.

        THttpClient(host, port, path) - deprecated
        THttpClient(uri)

        Only the second supports https.
        '''
        if port is not None:
            warnings.warn(
                'Please use the THttpClient("http://host:port/path") syntax',
                DeprecationWarning,
                stacklevel=2
            )
            self.host = uri_or_host
            self.port = port
            assert path
            self.path = path
            self.scheme = 'http'
        else:
            parsed = urllib.parse.urlparse(uri_or_host)
            self.scheme = parsed.scheme
            assert self.scheme in ('http', 'https')
            if self.scheme == 'http':
                self.port = parsed.port or http_client.HTTP_PORT
            elif self.scheme == 'https':
                self.port = parsed.port or http_client.HTTPS_PORT
            self.host = parsed.hostname
            self.path = parsed.path
            if parsed.query:
                self.path += '?%s' % parsed.query
        proxy = None
        self.request = request
        self.http2 = http2
        self.realhost = proxy_host
        self.realport = proxy_port
        self.proxy_auth = proxy_auth
        self.__wbuf = BytesIO()
        if self.scheme == 'https' and self.using_proxy() and self.proxy_auth:
            self.proxy_headers = {'Proxy-Authorization': self.proxy_auth}
        else:
            self.proxy_headers = None
        self.url = '%s://%s:%s%s' % (self.scheme, self.host, self.port, self.path)
        if customThrift:
            if self.request == 'hyper':
                if self.http2:
                    self.__http = hyper.HTTP20Connection(self.host, self.port, proxy_host=self.realhost, proxy_port=self.realport, proxy_headers=self.proxy_headers)
                else:
                    self.__http = hyper.HTTPConnection(self.host, self.port, proxy_host=self.realhost, proxy_port=self.realport, proxy_headers=self.proxy_headers)
            elif self.request == 'httpx':
                self.__http = httpx.AsyncClient(base_url='%s://%s' % (self.scheme, self.host), http2=self.http2)
            else:
                if self.http2:
                    self.__http = httplib2.Http()
                elif self.scheme == 'http':
                    self.__http = http_client.HTTPConnection(self.host, self.port)
                elif self.scheme == 'https':
                    self.__http = http_client.HTTPSConnection(self.host, self.port)
                    if self.using_proxy():
                        self.__http.set_tunnel(self.realhost, self.realport, self.proxy_headers)
        else:
             self.__http = None
        self.__async_loop = asyncio.get_event_loop() if self.request == 'httpx' else None
        self.__http_response = None
        self.__response_data = None
        self.__last_read = 0
        self.__timeout = None
        self.__custom_headers = None
        self.__time = time.time()
        self.__custom_thrift = customThrift
        self.__loop = 0

    @staticmethod
    def basic_proxy_auth_header(proxy):
        if proxy is None or not proxy.username:
            return None
        ap = '%s:%s' % (urllib.parse.unquote(proxy.username),
                        urllib.parse.unquote(proxy.password))
        cr = base64.b64encode(ap).strip()
        return 'Basic ' + cr

    def using_proxy(self):
        return self.realhost is not None

    def open(self):
        if self.request == 'hyper':
            if self.http2:
                self.__http = hyper.HTTP20Connection(self.host, self.port, proxy_host=self.realhost, proxy_port=self.realport, proxy_headers=self.proxy_headers)
            else:
                self.__http = hyper.HTTPConnection(self.host, self.port, proxy_host=self.realhost, proxy_port=self.realport, proxy_headers=self.proxy_headers)
        elif self.request == 'httpx':
            self.__http = httpx.AsyncClient(base_url='%s://%s' % (self.scheme, self.host), http2=self.http2)
        else:
            if self.http2:
                self.__http = httplib2.Http()
            elif self.scheme == 'http':
                self.__http = http_client.HTTPConnection(self.host, self.port)
            elif self.scheme == 'https':
                self.__http = http_client.HTTPSConnection(self.host, self.port)
                if self.using_proxy():
                    self.__http.set_tunnel(self.realhost, self.realport, self.proxy_headers)

    def close(self):
        if self.request != 'httpx':
            self.__http.close()
        self.__http = None
        self.__http_response = None
        self.__response_data = None
        self.__last_read = 0

    def getHeaders(self):
        return self.headers

    def isOpen(self):
        return self.__http is not None

    def setTimeout(self, ms):
        if not hasattr(socket, 'getdefaulttimeout'):
            raise NotImplementedError

        if ms is None:
            self.__timeout = None
        else:
            self.__timeout = ms / 1000.0

    def setCustomHeaders(self, headers):
        self.__custom_headers = headers

    def read(self, sz):
        if self.request == 'httpx' or (self.request == 'httplib' and self.http2):
            max_sz = self.__last_read + sz
            min_sz = self.__last_read
            self.__last_read = max_sz
            content = self.__response_data[min_sz:max_sz]
        else:
            content = self.__http_response.read(sz)
        return content

    def write(self, buf):
        self.__wbuf.write(buf)

    def __withTimeout(f):
        def _f(*args, **kwargs):
            orig_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(args[0].__timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                socket.setdefaulttimeout(orig_timeout)
            return result
        return _f

    async def httpx_flush(self, data, headers):
        # Building httpx request
        request = self.__http.build_request('POST', self.path, data=data, headers=headers)

        # Sending httpx request
        self.__http_response = await self.__http.send(request)
        self.code = self.__http_response.status_code
        self.message = self.__http_response.reason_phrase
        self.headers = self.__http_response.headers
        self.__response_data = self.__http_response.read()
        self.__last_read = 0

    def flush(self):
        if self.__custom_thrift:
            if self.__loop <= 2:
                if self.isOpen(): self.close()
                self.open(); self.__loop += 1
            elif time.time() - self.__time > 90:
                self.close(); self.open(); self.__time = time.time()
        else:
            if self.isOpen():
                self.close()
            self.open()

        # Pull data out of buffer
        data = self.__wbuf.getvalue()
        self.__wbuf = BytesIO()

        if not self.__custom_headers or 'User-Agent' not in self.__custom_headers:
            user_agent = 'Python/THttpClient'
            script = os.path.basename(sys.argv[0])
            if script:
                user_agent = '%s (%s)' % (user_agent, urllib.parse.quote(script))
        else:
            user_agent = None
        if self.request == 'hyper':
            headers = {'Content-Type': 'application/x-thrift', 'Content-Length': str(len(data)), 'User-Agent': user_agent}
            if self.__custom_headers:
                headers.update(self.__custom_headers)

            # Sending request with payload
            request = self.__http.request('POST', self.path, data, headers)

            # Get reply to flush the request
            self.__http_response = self.__http.get_response(request)
            self.code = self.__http_response.status
            self.message = self.__http_response.reason
            self.headers = self.__http_response.headers
        elif self.request == 'httpx':
            headers = {'Content-Type': 'application/x-thrift', 'Content-Length': str(len(data)), 'User-Agent': user_agent}
            if self.__custom_headers:
                headers.update(self.__custom_headers)
            self.__async_loop.run_until_complete(self.httpx_flush(data, headers))
        elif self.request == 'httplib' and self.http2:
            headers = {'Content-Type': 'application/x-thrift', 'Content-Length': str(len(data)), 'User-Agent': user_agent}
            if self.__custom_headers:
                headers.update(self.__custom_headers)

            # Sending and get reply to request
            self.__http_response, self.__response_data = self.__http.request(self.url, 'POST', headers=headers, body=data)
            self.__last_read = 0
            self.code = self.__http_response.status
            self.message = self.__http_response.reason
            self.headers = self.__http_response
        else:
            # HTTP request
            if self.using_proxy() and self.scheme == 'http':
                # need full URL of real host for HTTP proxy here (HTTPS uses CONNECT tunnel)
                self.__http.putrequest('POST', 'http://%s:%s%s' %
                                    (self.realhost, self.realport, self.path))
            else:
                self.__http.putrequest('POST', self.path)

            # Write headers
            self.__http.putheader('Content-Type', 'application/x-thrift')
            self.__http.putheader('Content-Length', str(len(data)))
            if not self.__custom_headers or 'User-Agent' not in self.__custom_headers:
                self.__http.putheader('User-Agent', user_agent)

            if self.__custom_headers:
                for key, val in six.iteritems(self.__custom_headers):
                    self.__http.putheader(key, val)

            self.__http.endheaders()

            # Write payload
            self.__http.send(data)

            # Get reply to flush the request
            self.__http_response = self.__http.getresponse()
            self.code = self.__http_response.status
            self.message = self.__http_response.reason
            self.headers = self.__http_response.msg

    # Decorate if we know how to timeout
    if hasattr(socket, 'getdefaulttimeout'):
        flush = __withTimeout(flush)
