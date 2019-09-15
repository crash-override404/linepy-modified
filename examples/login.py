# -*- coding: utf-8 -*-
from linepy import *

line = LINE('EMAIL', 'PASSWORD')
#line = LINE('AUTHTOKEN')

line.log("Auth Token : " + str(line.authToken))

# Initialize OEPoll with LINE instance
oepoll = OEPoll(line)

class Callback:
    def __init__(self, line, chatId):
        self.line = line
        self.chatId = chatId
    def callback(self, message):
        self.line.sendMessage(self.chatId, str(message))

# Receive messages from OEPoll
def RECEIVE_MESSAGE(op):
    msg = op.message

    text = msg.text
    msg_id = msg.id
    receiver = msg.to
    sender = msg._from
    
    # Check content only text message
    if msg.contentType == 0:
        # Check only group chat
        if msg.toType == 2:
            # Check if want get token
            if str(text).lower() == 'gettoken':
                callback = Callback(line, receiver)
                login = LINE(callback=callback.callback)
                line.sendMessage(login.profile.mid, "Auth Token : " + login.authToken)
            # Print log
            line.log(txt)

# Add function to OEPoll
oepoll.addOpInterruptWithDict({
    OpType.RECEIVE_MESSAGE: RECEIVE_MESSAGE
})

while True:
    oepoll.trace()
