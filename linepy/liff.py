# -*- coding: utf-8 -*-
from akad.ttypes import (
    LiffViewRequest,
    LiffContext,
    LiffChatContext,
    LiffSquareChatContext,
    RevokeTokenRequest,
    LiffException,
)
import requests, json, time

def loggedIn(func):
    def checkLogin(*args, **kwargs):
        if args[0].isLogin:
            return func(*args, **kwargs)
        else:
            args[0].callback.default('You want to call the function, you must login to LINE')
    return checkLogin

class Liff:
    isLogin = False
    liffToken = None
    liffTokens = {}
    liffBanned = {
        'status': False,
        'time': None
    }
    wait = 0

    def __init__(self):
        self.wait = time.time()
        self.isLogin = True
        self.resend = False
        self.to = None
        self.server.setLiffHeadersWithDict({
            'Authorization': '',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; Mi A1 Build/OPM1.171019.026; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/69.0.3497.91 Mobile Safari/537.36 Line/8.1.1',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
            'X-Requested-With': 'jp.naver.line.android'
        })
        try:
            self.allowLiff()
        except Exception as error:
            self.callback.default('Failed allow liff ' + str(error))

    @loggedIn
    def allowLiff(self):
        # Copyright by https://github.com/RynKings
        data = {'on': ['P', 'CM'], 'off': []}
        headers = {
            'X-Line-Access': self.authToken,
            'X-Line-Application': self.server.APP_NAME,
            'X-Line-ChannelId': self.server.CHANNEL_ID['HELLO_WORLD'],
            'Content-Type': 'application/json'
        }
        r = self.server.postContent(self.server.LINE_PERMISSION_API, headers=headers, data=json.dumps(data))
        return r.json()

    @loggedIn
    def issueLiffView(self, to, liffId='1602289196-4xoE1JEr', revokeToken=False, isSquare=False):
        if self.liffBanned['status']:
            elapsed = time.time() - self.liffBanned['time']
            if elapsed >= 86400:
                self.liffBanned['status'] = False
            else:
                raise Exception('issueLiffView Failed (liffChannel banned please wait untill %i seconds)' % elapsed)
        if to in self.liffTokens and not self.liffToken and not revokeToken:
            self.liffToken = self.liffTokens[to]
        else:
            if self.liffToken and revokeToken:
                try:
                    self.revokeToken(self.liffToken)
                    self.liffToken = None
                except Exception:
                    pass
            if isSquare:
                context = LiffContext(squareChat=LiffSquareChatContext(to))
            else:
                context = LiffContext(chat=LiffChatContext(to))
            liffReq = LiffViewRequest(liffId=liffId, context=context)
            try:
                liffResp = self.liff.issueLiffView(liffReq)
            except LiffException as liff_error:
                if liff_error.message == 'invalid request':
                    self.liffBanned.update({
                        'status': True,
                        'time': time.time()
                    })
                raise Exception('issueLiffView Failed (%s)' % liff_error.message)
            except Exception:
                raise Exception('issueLiffView Failed (liffId is invalid or your token can\'t do this)')
            self.liffToken = liffResp.accessToken
            self.liffTokens[to] = self.liffToken
        self.to = to
        return self.liffToken

    @loggedIn
    def sendLiffMessage(self, message, data=None, liffToken=None, revokeToken=False):
        if liffToken:
            self.server.setLiffHeaders('Authorization', 'Bearer ' + liffToken)
        elif self.liffToken:
            self.server.setLiffHeaders('Authorization', 'Bearer ' + self.liffToken)
        else:
            raise Exception('sendLiffMessage Failed (you must issueLiffView before send)')
        if not data:
            data = {'messages': []}
            if isinstance(message, dict):
                data['messages'].append(message)
            else:
                data['messages'] = message
        # To avoid liff banned
        waiting = self.wait - time.time()
        if waiting > 0: time.sleep(waiting)
        r = self.server.postContent(self.server.LINE_LIFF_SEND, headers=self.server.liffHeaders, data=json.dumps(data))
        self.wait = time.time() + 1
        resp = r.json()
        if 'message' in resp and not self.resend and self.to:
            self.resend = True
            self.issueLiffView(self.to, revokeToken=True)
            return self.sendLiffMessage(None, data=data, revokeToken=revokeToken)
        if revokeToken:
            try:
                self.revokeToken(self.liffToken)
                self.liffToken = None
            except Exception:
                pass
        self.resend = False
        self.to = None
        return resp

    @loggedIn
    def sendFlexMessage(self, flexContent, altText='Hello World', liffToken=None, revokeToken=False):
        if liffToken:
            self.server.setLiffHeaders('Authorization', 'Bearer ' + liffToken)
        elif self.liffToken:
            self.server.setLiffHeaders('Authorization', 'Bearer ' + self.liffToken)
        else:
            raise Exception('sendLiffMessage Failed (you must issueLiffView before send)')
        messages = [
            {
                'type': 'flex',
                'altText': altText,
                'contents': flexContent
            }
        ]
        data = {'messages': messages}
        # To avoid liff banned
        waiting = self.wait - time.time()
        if waiting > 0: time.sleep(waiting)
        r = self.server.postContent(self.server.LINE_LIFF_SEND, headers=self.server.liffHeaders, data=json.dumps(data))
        self.wait = time.time() + 1
        resp = r.json()
        if 'message' in resp and not self.resend and self.to:
            self.resend = True
            self.issueLiffView(self.to, revokeToken=True)
            return self.sendLiffMessage(None, data=data, revokeToken=revokeToken)
        if revokeToken:
            try:
                self.revokeToken(self.liffToken)
                self.liffToken = None
            except Exception:
                pass
        self.resend = False
        self.to = None
        return resp

    @loggedIn
    def revokeToken(self, accessToken):
        self.server.setLiffHeaders('Authorization', '')
        self.liff.revokeToken(RevokeTokenRequest(accessToken))