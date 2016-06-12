#!/usr/bin/env python

import websocket
import time
import json
import max7219.led as led
from max7219.font import proportional, SINCLAIR_FONT, TINY_FONT, CP437_FONT
import Queue
from threading import Thread

SERVER_URL = 'wss://localhost:5443'
ACCESS_TOKEN = 'eyJhbGciOiJIUzI1...'
SUBSCRIBE_TOPIC = 'cloud_matrix'
GROUP_ID = 'cloud_matrix_client_0'

queue = Queue.Queue()
device = led.matrix(cascaded=4, vertical=True)

def poll():
    item = 'NO DATA'

    while True:
        try:
            item = queue.get(False)
            device.show_message(item, font=proportional(CP437_FONT))
            queue.task_done()
        except Queue.Empty:
            device.show_message(item, font=proportional(CP437_FONT))

def authenticate(ws):
    data = {}
    data['event'] = 'auth'
    data['token'] = ACCESS_TOKEN
    payload = json.dumps(data)
    ws.send(payload)

def subscribe(ws):
    data = {}
    data['event'] = 'subscribe'
    data['topics'] = [SUBSCRIBE_TOPIC]
    data['groupId'] = GROUP_ID
    payload = json.dumps(data)
    ws.send(payload)

def process_auth(ws, payload):
    if (payload['success']):
        print 'Authenticated'
        subscribe(ws)
    else:
        print 'Authentication failed: ' + payload['message']

def process_message(ws, payload):
    message = payload['value']
    print 'Got message: ' + message
    queue.put(message)

def process_revoke(ws, payload):
    print 'Partition revoked'

def process_assign(ws, payload):
    print 'Partition assigned'

def on_message(ws, message):
    payload = json.loads(message)
    event = payload['event']

    if event == 'auth':
        process_auth(ws, payload)
    elif event == 'message':
        process_message(ws, payload)
    elif event == 'revoke':
        process_revoke(ws, payload)
    elif event == 'assign':
        process_assign(ws, payload)

def on_error(ws, error):
    print error

def on_close(ws):
    print 'Connection closed'

def on_open(ws):
    print 'Connection open'
    authenticate(ws)

if __name__ == '__main__':
    pollThread = Thread(target = poll)
    pollThread.daemon = True
    pollThread.start()

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(SERVER_URL,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

