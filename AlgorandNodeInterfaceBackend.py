from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk import encoding, account, mnemonic
from joblib import load
import json

#TODO we need akita_inu_asa_utils to be a submodule of both contracts repo and this repo
from akita_inu_asa_utils import wait_for_txn_confirmation, get_asset_balance, get_algo_balance, read_global_state, read_local_state
from InterfaceStatLogger import InterfaceStatLogger
import base64

class AlgorandNodeInterfaceBackend:
    def __init__(self):
        self.logger = InterfaceStatLogger("Algorand_Node_Interface")
        self.algod = self.get_client()


        self.transaction_handler_mapping ={
               
                }

        self.testing_handler_mapping = {
            "generate_test_wallet": self.generate_test_wallet
        }
    
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

    def handle_get_state(self, request):
        try:
            creator_key = request["creatorPublicKey"]
            user_key = request["userPublicKey"]
            pool_id = request["parameters"]["pool_id"]
            global_state = read_global_state(self.algod, creator_key, pool_id)
            local_state = read_local_state(self.algod, user_key, pool_id)
            response = {
                        "local_state": local_state,
                        "global_state": global_state
                    }
        except Exception as inst:
            return {"Error": f"Error getting asset balance: {inst.args}"}
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

    def handle_testing_request(self, request):
        if request["testType"] in self.testing_handler_mapping.keys():
            return self.testing_handler_mapping[request["testType"]](request)

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

    def get_token_address(self, token_file='/shared_volume/algod.token'):
        fp = open(token_file)
        token = fp.readline()
        return token, "http://node_interface_network:8080"

    def get_client(self):
        token, address = self.get_token_address()
        client = algod.AlgodClient(token, address)
        self.logger.log_info(client.status())
        return client

    def load_schema(self, file_path):
        f = open(file_path, 'r')
        stateJSON = json.load(f)
        return transaction.StateSchema(stateJSON['num_ints'], stateJSON['num_bytes'])

    def generate_test_wallet(self, request):
        private_key, address = account.generate_account()
        response = {
                    "mnemonic": mnemonic.from_private_key(private_key),
                    "private_key": private_key,
                    "public_key": address
                }
        return response

