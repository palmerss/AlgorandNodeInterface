import random
import time
import requests
import pytest
from main import *
from multiprocessing import Process
from test.TxnSpammer import TxnSpammer

@pytest.fixture(scope='session')
def port_number():
    return 42069

@pytest.fixture(scope='session')
def node_interface(port_number):
    p = Process(target=algorand_node_interface_main, args=(port_number,))
    p.start()
    yield p.pid
    p.kill()


class Test_node_throughput:
    @pytest.mark.skip()
    def test_throughput(self, node_interface, port_number):
        #spammer = TxnSpammer(8, 1, 70)
        spammer = TxnSpammer(1, 1, 10, port_number)
        spammer.start_spam()
        time.sleep(100)
        spammer.stop_spam()

    def test_txn_status(self):
        txn_id = "K23K276MKNPMDQQLWIRHIP2GMFGC3VOK5ETJCKI7UB7KZQV7KO4A"
        request = {"requestType": "get_txn_status",
                   "request": {"parameters":{"txn_id": txn_id
                                             }
                               }
                   }
        response = requests.post("http://localhost:4000", request)
        print(response)