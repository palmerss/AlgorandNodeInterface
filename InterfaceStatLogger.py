import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Queue
import numpy as np
import time

def tps_logger(queue,logger_name='default', update_frequency=1):
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    logging.basicConfig(filename='/tmp/node_stats.log', filemode='w', level=logging.INFO)
    logging_handler = RotatingFileHandler('node_stats.log', mode='a', maxBytes=5 * 1024 * 1024)
    logging_handler.setFormatter(log_formatter)
    logging_handler.setLevel(logging.INFO)

    app_log = logging.getLogger(logger_name)
    app_log.setLevel(logging.INFO)
    app_log.addHandler(logging_handler)
    app_log.info("LOGGING INITIALIZED")
    txns = 0
    time_last_sent = time.time()
    while True:
        num_txn = queue.get(block=True)
        txns += num_txn
        current_time = time.time()
        if (interval := (np.subtract(current_time, time_last_sent))) >= update_frequency:
            app_log.info(np.divide(txns, interval))
            txns = 0
            time_last_sent = current_time


class InterfaceStatLogger:
    def __init__(self, logger_name):
        self.queue = Queue()

        tps_logger_process = Process(target=tps_logger, args=(self.queue, logger_name, 1))
        tps_logger_process.start()

    def txn_sent(self, group_size):
        self.queue.put(group_size)

    def error_encountered(self, err):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        logging.basicConfig(filename='/tmp/node_stats.log', filemode='w', level=logging.ERROR)
        logging_handler = RotatingFileHandler('node_stats.log', mode='a', maxBytes=5 * 1024 * 1024)
        logging_handler.setFormatter(log_formatter)
        logging_handler.setLevel(logging.INFO)

        app_log = logging.getLogger('errors')
        app_log.setLevel(logging.INFO)
        app_log.addHandler(logging_handler)
        app_log.info(err)

    def log_info(self, info):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        logging.basicConfig(filename='/tmp/node_stats.log', filemode='w', level=logging.INFO)
        logging_handler = RotatingFileHandler('node_stats.log', mode='a', maxBytes=5 * 1024 * 1024)
        logging_handler.setFormatter(log_formatter)
        logging_handler.setLevel(logging.INFO)

        app_log = logging.getLogger('info')
        app_log.setLevel(logging.INFO)
        app_log.addHandler(logging_handler)
        app_log.info(info)
