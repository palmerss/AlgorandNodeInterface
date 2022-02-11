import time

import requests
from algosdk.future import transaction
from algosdk import mnemonic, encoding, account
from InterfaceStatLogger import InterfaceStatLogger
from multiprocessing import Process
from algosdk.v2client import algod
import json
import logging

logging.getLogger('tornado.access').disabled = True
CLIENTTOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
CLIENTADDRESS = "http://localhost:4001"
WALLETMNEMONIC = "jar over grace body leg math wait buddy slogan canyon frame moral enemy congress zebra upon high actual glory arm rifle spot rare abstract century"

def spam_txns(group_size, logger, tps_limit=None, portnumber=42069):
    group_buffer = [None] * group_size
    client = algod.AlgodClient(CLIENTTOKEN, CLIENTADDRESS)
    private_key = mnemonic.to_private_key(WALLETMNEMONIC)
    public_key = account.address_from_private_key(private_key)
    receiving_url = f"http://localhost:{portnumber}"
    interval = None

    if tps_limit:
        interval = 1 / tps_limit

    cycle_time = 0
    while True:
        try:
            if interval and cycle_time <= interval:
                    time.sleep(interval - cycle_time)

            cycle_time = time.time()
            params = client.suggested_params()
            amount = 0
            for index in range(0, group_size):
                group_buffer[index] = transaction.PaymentTxn(public_key, params, public_key, amount, note=str(cycle_time))
                amount += 1

            group_buffer = transaction.assign_group_id(group_buffer)
            for index in range(0, group_size):
                group_buffer[index] = encoding.msgpack_encode(group_buffer[index].sign(private_key))


            request_data = {
                            "requestType": "send_to_algo_node",
                            "request": {
                                        "transactions": group_buffer
                                       }
                           }

            response = requests.post(receiving_url, json.dumps(request_data))
            if response.json()['STATUS'] != 'Transaction sent':
                logger.log_info(response.json())
            logger.queue.put(group_size)
            cycle_time = time.time() - cycle_time
        except Exception as inst:
            logger.error_encountered(inst.args)

class TxnSpammer:
    def __init__(self, num_workers, group_size, tps_limit_per_worker, portNumber):
        self.worker_arr = []
        self.logger = InterfaceStatLogger('producer')
        self.num_workers = num_workers
        self.group_size = group_size
        self.tps_limit_per_worker = tps_limit_per_worker
        self.portNumber = portNumber

    def start_spam(self):
        for index in range(0, self.num_workers):
            self.worker_arr.append(Process(target=spam_txns, args=(self.group_size, self.logger, self.tps_limit_per_worker, self.portNumber)))
        for worker in self.worker_arr:
            worker.start()

    def stop_spam(self):
        for worker in self.worker_arr:
            worker.kill()
        self.worker_arr = []
