import tornado.ioloop
import tornado.web
from tornado import httpclient
import os
import subprocess
import handlers
import re

# py file name to port number
proxymap = {}

port = 8505

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(os.getcwd())
        for f in os.scandir('./examples'):
            self.write("File: {}".format(f.name))

class DefaultProxyHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("INIT PROXYHANDLER ***")

    async def get(self):
        match = re.search(r"^/(.+\.py)/(.*)$", self.request.path)
        appname, path = None, None
        if match:
            appname, path = match[1], match[2]
            print(match)

        else:
            print("NO MATCH: "+self.request.path)
            self.set_status(404)
            self.finish()
            return

        print("appname {}, path {}".format(appname, path))

        global proxymap
        my_port = 0
        if not appname in proxymap:

            global port

            proc = subprocess.Popen(['streamlit', 'run', os.path.join('./examples', appname),
                                     '--server.port', str(port),
                                     '--server.headless', 'True'])

            proxymap[appname] = {'proc': proc, 'port': port}

            url = 'http://localhost:{}/'.format(port)

            self.application.add_handlers(
                r".*",
                [
                    (rf"^/{appname}/stream(.*)", handlers.ProxyWSHandler, {'proxy_url': url+'stream'}),
                    (rf"^/{appname}/(.*)", handlers.ProxyHandler, {'proxy_url': url})
                ])


            print("Started {}: {}".format(appname, port))

            my_port = port

            port += 1
        else:
            my_port = proxymap[appname]['port']
            print("Already running {}: {}".format(appname, my_port))

        self.write("{} is running on port {}. Refresh shortly.".format(appname, my_port))

        self.finish()


def make_app():
    return tornado.web.Application([
        (r"^/$", MainHandler),
    ],
    debug=True,
    default_handler_class=DefaultProxyHandler)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
