# -*- coding: utf-8 -*-
from akad.ttypes import Message
from .auth import Auth
from .models import Models
from .talk import Talk
from .square import Square
from .call import Call
from .timeline import Timeline
from .server import Server
from .shop import Shop

class LINE(Auth, Models, Talk, Square, Call, Timeline, Shop):

    def __init__(self, idOrAuthToken=None, passwd=None, **kwargs):
        """
        :param idOrAuthToken: Login email, token. Default: None
        :param passwd: Login password. Default: None
        :param kwargs: See below
        :Keyword Arguments:
            - **certificate**: Line certificate after email login. Default: None
            - **systemName**: System name when first login. Default: None
            - **appType**: Application type to login. Default: None
            - **appName**: Application name to login. Default: None
            - **showQr**: Print out qr code. Default: False
            - **channelId**: Channel ID to login Timeline. Default: None
            - **keepLoggedIn**: Keep logged in if succesfull login. Default: True
            - **customThrift**: Increase speed thrift with custom thrift. Default: False
        :return:
        """
        self.certificate = kwargs.pop('certificate', None)
        self.systemName = kwargs.pop('systemName', None)
        self.appType = kwargs.pop('appType', None)
        self.appName = kwargs.pop('appName', None)
        self.showQr = kwargs.pop('showQr', False)
        self.channelId = kwargs.pop('channelId', None)
        self.keepLoggedIn = kwargs.pop('keepLoggedIn', True)
        self.customThrift = kwargs.pop('customThrift', False)
        Auth.__init__(self)
        if not (idOrAuthToken or idOrAuthToken and passwd):
            self.loginWithQrCode()
        if idOrAuthToken and passwd:
            self.loginWithCredential(idOrAuthToken, passwd)
        elif idOrAuthToken and not passwd:
            self.loginWithAuthToken(idOrAuthToken)
        self.__initAll()

    def __initAll(self):

        self.profile    = self.talk.getProfile()
        self.userTicket = self.generateUserTicket()
        self.groups     = self.talk.getGroupIdsJoined()

        Models.__init__(self)
        Talk.__init__(self)
        Square.__init__(self)
        Call.__init__(self)
        Timeline.__init__(self)
        Shop.__init__(self)
