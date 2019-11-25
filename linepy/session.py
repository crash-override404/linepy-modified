# -*- coding: utf-8 -*-
from .transport import THttpClient
from thrift.protocol import TCompactProtocol
from akad import AuthService, TalkService, ChannelService, CallService, SquareService, LiffService, ShopService

class Session:

    def __init__(self, url, headers, path='', customThrift=False):
        self.host = url + path
        self.headers = headers
        self.customThrift = customThrift

    def Auth(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._auth  = AuthService.Client(self.protocol)

        if isopen:
            self.transport.open()

        return self._auth

    def Talk(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._talk  = TalkService.Client(self.protocol)
        if isopen:
            self.transport.open()

        return self._talk

    def Channel(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._channel  = ChannelService.Client(self.protocol)

        if isopen:
            self.transport.open()

        return self._channel

    def Call(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._call  = CallService.Client(self.protocol)

        if isopen:
            self.transport.open()

        return self._call

    def Square(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._square  = SquareService.Client(self.protocol)

        if isopen:
            self.transport.open()

        return self._square

    def Shop(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._shop  = ShopService.Client(self.protocol)

        if isopen:
            self.transport.open()

        return self._shop

    def Liff(self, isopen=True):
        self.transport = THttpClient(self.host, customThrift=self.customThrift)
        self.transport.setCustomHeaders(self.headers)

        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)
        self._liff  = LiffService.Client(self.protocol)

        if isopen:
            self.transport.open()

        return self._liff
