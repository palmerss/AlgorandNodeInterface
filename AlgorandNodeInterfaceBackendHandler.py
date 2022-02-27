import tornado.ioloop
import tornado.web
import json

class AlgorandNodeInterfaceBackendHandler(tornado.web.RequestHandler):
    
    def initialize(self, backend):
        self.backend = backend

        self.handlerMapping ={ 
                "transaction" : backend.handle_transaction_request,
                "get_txn_status": backend.handle_get_txn_status,
                "send_to_algo_node": backend.handle_send_to_algo_node_request,
                "get_user_asa_balance": backend.handle_get_user_asa_balance,
                "get_user_algo_balance": backend.handle_get_user_algo_balance,
                "get_user_asa_algo_balance": backend.handle_get_user_asa_algo_balance,
                "get_test_token": backend.handle_get_test_token,
                "get_state": backend.handle_get_state,
                "testing": backend.handle_testing_request,
                "ping": backend.ping,
        }

    def get(self):
        self.write("You're not supposed to be here")

    def post(self):
        msg = json.loads(self.request.body)
        if msg["requestType"] in self.handlerMapping.keys():
            response = self.handlerMapping[msg["requestType"]](msg["request"])
            self.write(response)
        else:
            print("Invalid Message Received")
        
    
