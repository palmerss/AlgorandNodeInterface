from algosdk.v2client import algod, indexer
from algosdk.future import transaction
from algosdk import encoding, account, mnemonic

import json
import os
import base64

BALANCE_PER_ASSET = 100000


def get_application_address(app_id):
    return encoding.encode_address(encoding.checksum(b'appID' + app_id.to_bytes(8, 'big')))


def check_build_dir():
    if not os.path.exists('build'):
        os.mkdir('build')


def get_asset_balance(client, public_key, asset_id):
    for asset in client.account_info(public_key)['assets']:
        if asset['asset-id'] == asset_id:
            return asset['amount']
    return 0


def is_opted_into_asset(client, public_key, asset_id):
    for asset in client.account_info(public_key)['assets']:
        print(asset['asset-id'])
        if asset['asset-id'] == asset_id:
            return True
    return False


def get_algo_balance(client, public_key):
    return client.account_info(public_key)['amount']

def get_min_algo_balance(number_assets):
    return BALANCE_PER_ASSET + (BALANCE_PER_ASSET * number_assets)

def generate_new_account():
    private_key, address = account.generate_account()
    return mnemonic.from_private_key(private_key), private_key, address


def compile_program(client, source_code, file_path=None):
    compile_response = client.compile(source_code)
    if file_path == None:
        return base64.b64decode(compile_response['result'])
    else:
        check_build_dir()
        fp = open('build/' + file_path, "wb")
        fp.write(base64.b64decode(compile_response['result']))
        fp.close()


# read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)
    output = {}
    for app in results['apps-local-state']:
        if app['id'] == app_id:
            for key_value in app['key-value']:
                if key_value['value']['type'] == 1:
                    value = key_value['value']['bytes']
                else:
                    value = key_value['value']['uint']
                output[base64.b64decode(key_value['key']).decode()] = value
            return output

def get_translated_local_state(client, app_id, public_key):
    local_state = read_local_state(client, public_key, app_id)
    for key in local_state.keys():
        if type(local_state[key]) != int:
            local_state[key] = int.from_bytes(base64.b64decode(local_state[key]), "big")
    return local_state


# read app global state
def read_global_state(client, app_id):
    output = {}
    for key_value in client.application_info(app_id)['params']['global-state']:
        if key_value['value']['type'] == 1:
            value = base64.b64decode(key_value['value']['bytes'])
        else:
            value = key_value['value']['uint']
        output[base64.b64decode(key_value['key']).decode()] = value
    return output

def get_translated_global_state(client, app_id):
    global_state = read_global_state(client, app_id)
    for key in global_state.keys():
        if type(global_state[key]) != int:
            global_state[key] = int.from_bytes(global_state[key], "big")
    return global_state

def pretty_print_state(state):
    for keyvalue in state:
        print(base64.b64decode(keyvalue['key']))
        print(keyvalue['value'])
    print("\n\n\n")


def get_key_from_state(state, key):
    for i in range(0, len(state)):
        found_key = base64.b64decode(state[i]['key'])
        if found_key == key:
            if state[i]['value']['type'] == 1:
                return base64.b64decode(state[i]['value']['bytes'])
            elif state[i]['value']['type'] == 2:
                return state[i]['value']['uint']


def dump_teal_assembly(file_path, program_fn_pointer, args=None):
    check_build_dir()
    with open('build/' + file_path, 'w') as f:
        if args != None:
            compiled = program_fn_pointer(*args)
        else:
            compiled = program_fn_pointer()
        f.write(compiled)


def load_compiled(file_path):
    try:
        fp = open('build/' + file_path, "rb")
        compiled = fp.read()
        fp.close()
    except:
        print("Error reading source file...exiting")
        exit(-1)
    return compiled


def asset_id_from_create_txn(client, txn_id):
    ptx = client.pending_transaction_info(txn_id)
    asset_id = ptx["asset-index"]
    return asset_id


def load_developer_config(file_path='DeveloperConfig.json'):
    fp = open(file_path)
    return json.load(fp)


def get_algod_client(token, address):
    return algod.AlgodClient(token, address)


def write_schema(file_path, num_ints, num_bytes):
    f = open('build/' + file_path, "w")
    json.dump({"num_ints": num_ints,
               "num_bytes": num_bytes}, f)
    f.close()


def load_schema(file_path):
    f = open('build/' + file_path, 'r')
    stateJSON = json.load(f)
    return transaction.StateSchema(stateJSON['num_ints'], stateJSON['num_bytes'])


def wait_for_txn_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception(
                'pool error: {}'.format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        'pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))


def send_transactions(client, transactions):
    transaction_id = client.send_transactions(transactions)
    wait_for_txn_confirmation(client, transaction_id, 5)
    return transaction_id

def get_remote_indexer(token="", address="https://algoindexer.algoexplorerapi.io/", headers={'User-Agent':'Random'}):
    return indexer.IndexerClient(token, address, headers)
