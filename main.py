import tornado.ioloop
import tornado.web
from AlgorandNodeInterfaceBackend import AlgorandNodeInterfaceBackend
from AlgorandNodeInterfaceBackendHandler import AlgorandNodeInterfaceBackendHandler
from tornado.httpserver import HTTPServer

def make_app(backend):
    return tornado.web.Application([(r"/", AlgorandNodeInterfaceBackendHandler, {"backend" : backend}), ])

def algorand_node_interface_main(portnumber=42069):
    backend = AlgorandNodeInterfaceBackend()
    http_server = tornado.httpserver.HTTPServer(make_app(backend))
    http_server.bind(portnumber)
    http_server.start()
    print("listening")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    algorand_node_interface_main()