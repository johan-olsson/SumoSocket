from tornado import websocket, web, ioloop, httpserver
import json, re

subscriptions = {}
sessions = {}
app = web.Application()

class SubscribeHandler(websocket.WebSocketHandler):

    def open(self, *params):
        print('Client connected')

        global subscriptions
        global sessions
        self.subscriptions = subscriptions
        self.sessions = sessions

        self.params = params

        if not self.request.uri in self.sessions:
            self.sessions[self.request.uri] = []

        if self not in self.sessions[self.request.uri]:
            self.sessions[self.request.uri].append(self)
            
    def on_message(self, message):
        for key, subscriptionList in subscriptions.items():
            if re.match(key, self.request.uri):
                for subscription in subscriptionList:
                    subscription(message)
                
    def on_close(self):
        if self in self.sessions[self.request.uri]:
            self.sessions[self.request.uri].remove(self)



class Endpoint():
    def __init__(self, path):
        global app
        global subscriptions
        
        if path[-1] != '$':
            path = '{}$'.format(path)

        self.subscriptions = subscriptions
        self.path = path

        if not self.path in subscriptions:
            subscriptions[self.path] = []
            app.add_handlers(
                '127.0.0.1', [
                    (self.path, SubscribeHandler)
            ])
        
    def subscribe(self, subscription):
        self.subscriptions[self.path].append(subscription)
        def unSubscribe():
            self.subscriptions[self.path].remove(subscription)
        subscription.unSubscribe = unSubscribe
        return subscription

    def broadcast(self, message):
        print('Broadcasting')

        for key, sessionList in sessions.items():
            if re.match(self.path, key):
                for session in sessionList:
                    session.write_message(message)



def start():
    server = httpserver.HTTPServer(app)
    server.listen(9000)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    start()



