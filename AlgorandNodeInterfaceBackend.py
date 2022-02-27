import time

from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk import encoding, account, mnemonic
from joblib import load
import json
import os

#TODO we need akita_inu_asa_utils to be a submodule of both contracts repo and this repo
from akita_inu_asa_utils import wait_for_txn_confirmation, get_asset_balance, get_algo_balance, get_translated_local_state, get_translated_global_state
from InterfaceStatLogger import InterfaceStatLogger
import base64

TEST_TOKENS_DRIP_RATE = 5000000
class AlgorandNodeInterfaceBackend:
    def __init__(self):
        self.logger = InterfaceStatLogger("Algorand_Node_Interface")
        self.algod = self.get_client()
        self.test_wallet = self.load_test_wallet()

        self.transaction_handler_mapping ={
               
                }

        self.testing_handler_mapping = {

        }
    
    def load_test_wallet(self):
        fp = open("./testWallet")
        test_mnemonic = fp.readline()
        pk = mnemonic.to_private_key(test_mnemonic)
        sk = mnemonic.to_public_key(test_mnemonic)
        return {"mnemonic": test_mnemonic,
                "public_key": pk,
                "private_key": sk}

    
    def load_json(self, file_path):
        fp = open(file_path)
        json_file = json.load(fp)
        fp.close()
        return json_file

    def send_raw_transactions(self, txns, **kwargs):
        serialized = []
        for txn in txns:
            serialized.append(base64.b64decode(txn))

        return self.algod.send_raw_transaction(
            base64.b64encode(b"".join(serialized)), **kwargs
        )

    def handle_get_test_token(self, request):
        try:
            token_to_request = request["parameters"]["token_id"]
            user_to_receive = request["userPublicKey"]
            txn = transaction.AssetTransferTxn(self.test_wallet['public_key'], 
                                                self.algod.suggested_params(),
                                                user_to_receive,
                                                TEST_TOKENS_DRIP_RATE,
                                                token_to_request)
            txn = txn.sign(self.test_wallet['private_key'])
            self.algod.send_transactions([txn])
            return {"STATUS": "Test tokens dispensed"}
        except Exception as inst:
            return {"ERROR": f"Error dispensing test tokens: {inst.args}"}

    def handle_get_state(self, request):
        try:
            local_state = None
            pool_id = request["parameters"]["pool_id"]

            global_state = get_translated_global_state(self.algod, pool_id)
            if 'userPublicKey' in request.keys():
                local_state = get_translated_local_state(self.algod, pool_id, request["userPublicKey"])

            response = {
                        "local_state": local_state,
                        "global_state": global_state
                    }
        except Exception as inst:
            return {"Error": f"Error getting state: {inst.args}"}
        return response

    def handle_get_txn_status(self, request):
        try:
            response = {}
            txn_id = request['parameters']['txn_id']
            pending_txn = self.algod.pending_transaction_info(txn_id)
            if pending_txn.get("confirmed-round", 0) > 0:
                response['txn_status'] = pending_txn
            elif pending_txn["pool-error"]:
                response = {"Error": "Error getting txn status due to algorand node pool error"}
        except Exception as inst:
                response =  {"Error": f"Error getting txn status: {inst.args}"}
        return response
    
    def handle_get_user_asa_balance(self, request):
        try:
            asset_id = request["asset_id"]
            public_key = request["user_public_key"]
            response = {
                        "asset_id": asset_id,
                        "asset_balance": get_asset_balance(self.algod, public_key, asset_id)
                    }
        except Exception as inst:
            return {"Error": f"Error getting asset balance: {inst.args}"}
        return response

    def handle_get_user_algo_balance(self, request):
        try:
            public_key = request["user_public_key"]
            response = {
                        "algo_balance": get_algo_balance(self.algod, public_key)
                    }
        except Exception as inst:
            return {"Error": f"Error getting algo balance: {inst.args}"}
        return response
    
    def handle_get_user_asa_algo_balance(self, request):
        try:
            public_key = request["user_public_key"]
            asset_id = request["asset_id"]
            response = {
                        "algo_balance": get_algo_balance(self.algod, public_key), 
                        "asset_id": asset_id,
                        "asset_balance": get_asset_balance(self.algod, public_key, asset_id)
                    }
        except Exception as inst:
            return {"Error": f"Error getting algo asset balance: {inst.args}"}
        return response

    def handle_transaction_request(self, request):
        if request["transactionType"] in self.transaction_handler_mapping.keys():
            return self.transaction_handler_mapping[request["transactionType"]](request)

    def ping(self, request):
        return {"STATUS": "PONG"}

    def handle_send_to_algo_node_request(self, request):
        try:
            txn_id = self.send_raw_transactions(request['transactions'])
            self.logger.txn_sent(len(request['transactions']))
            transaction_response = self.algod.pending_transaction_info(txn_id)
            app_id = ""
            if "application-index" in transaction_response.keys():
                app_id = transaction_response['application-index']
            response = {
                        "STATUS": "Transaction sent",
                        "txn_id": txn_id,
                        "app_id": app_id,
                        "transaction_response":transaction_response
                       }

        except Exception as inst:
            errormsg = {"Error": f"Error sending transaction: {inst.args}"}
            self.logger.error_encountered(errormsg)
            return errormsg
        return response

    def get_token(self, token_file='/shared_volume/algod.token'):
        time.sleep(10) #hacky work around for slow machines...
        while True:
            if os.path.exists(token_file):
                fp = open(token_file)
                token = fp.readline()
                self.logger.log_info(f"Algorand Node Token: {token}")
                return token
            else:
                time.sleep(1)
                self.logger.log_info("Algorand Client Token not found... retrying")

    def wait_for_client_to_idle(self, client):
        while client.status()['catchpoint'] != '':
            time.sleep(1)

    def establishClient(self, address):
        token = self.get_token()
        client = algod.AlgodClient(token, address)
        self.wait_for_client_to_idle(client)
        return client

    #try testnet first and then main net #TODO I need to handle address the same way as token to clean this up
    def get_client(self):
        address = "http://algo_node_testnet:8080"
        try:
            client = self.establishClient(address)
        except:
            try:
                address = "http://algo_node_mainnet:8080"
                client = self.establishClient(address)
            except:
                print("Connection to Algorand Client could not be established")
                exit()

        self.logger.log_info("Algorand Client Has Started and is caught up")
        return client

    def load_schema(self, file_path):
        f = open(file_path, 'r')
        stateJSON = json.load(f)
        return transaction.StateSchema(stateJSON['num_ints'], stateJSON['num_bytes'])