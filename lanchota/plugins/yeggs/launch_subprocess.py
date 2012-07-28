#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import signal
import sys
import thread
import zmq

from multiprocessing import Process, Queue

from utils import Request, Response, KEYWORD_VALUE

# Better than os.getcwd() with symlinks
CURRENT_DIR = os.path.abspath(__file__.partition('launch_subprocess.py')[:-1][0])

if sys.platform == 'linux2':
    # FIXME: just for testing purposes 
    sublib_dir = 'lin32'
else:
    sublib_dir = 'win32'

LIBS_DIR = os.path.join(CURRENT_DIR, "lib", sublib_dir)
sys.path.insert(1, LIBS_DIR)
FLAG_OK = "O"
FLAG_ERR = "E"
FLAG_PORT = "P"
FLAG_STOP = "S"
INIT_MESSAGE = "OK"
DEFAULT_INSTANCE_NAME = "default"
ZMQ_PORT_NUMBER = 5555

WORKER_PROCESSES = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def callback(*args):
    if len(args) == 3:
        flag = args[1]
        response = args[2]
    else:
        flag = args[0]
        response = args[1]

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:"+str(ZMQ_PORT_NUMBER))

    if flag == FLAG_OK:
        data = response.render()
        json_data = json.dumps(data)
    elif flag == FLAG_ERR:
        if isinstance(response, Response):
            data = response.render()
        else:
            try:
                data = str(e)
            except:
                data = "General error"
        json_data = json.dumps(data)
    elif flag == FLAG_PORT:
        json_data = json.dumps(response.value)
    elif flag == FLAG_STOP:
        pid = os.getpid()
        json_data = '['+str(pid)+']'

    logger.info("sending %s %s" % (flag, json_data))
    socket.send_unicode(flag + json_data + "\0")
    if flag!=FLAG_STOP:
        msg_in = socket.recv()

def run_method(*args):
    request = args[0]
    method = args[1]

    if len(args)>2:
        params = args[2:]
    else:
        params = []

    response = Response()
    response.instance_name = request.instance_name

    try:
        data = method(*params)
    except Exception, e:
        # TODO: Error should be json data
        logging.error(e)
        response.value = str(e)
        callback(FLAG_ERR, response)
    else:
        if data is not None:
            response.value = data
            callback(FLAG_OK, response)

def get_available_connection(startin_port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    char_conn_string = "tcp://127.0.0.1:" + str(startin_port)

    try:
        socket.bind(char_conn_string);
    except Exception, e:
        startin_port +=1;
        return get_available_connection(startin_port);

    return socket, startin_port;


if __name__ == "__main__":
    arguments = sys.argv
    ZMQ_PORT_NUMBER = arguments[1]
    socket, startin_port = get_available_connection(6666)

    logging.info("Now using startin_port:%s" % startin_port)
    callback(FLAG_PORT, Response('port', startin_port))

    while True:
        msg = socket.recv_json()
        flag_async = msg[0]
        yegg_name = msg[1]

        if flag_async != 9:
            instance_name, method_name = msg[2].split("=")
        else:
            instance_name = DEFAULT_INSTANCE_NAME
            method_name = msg[2]

        params = msg[3]

        if flag_async == 9:
            for process in WORKER_PROCESSES.itervalues():
                process.terminate()
            callback(FLAG_STOP, None)

        elif flag_async == 1: # Launch asynchronous process
            try:
                socket.send(INIT_MESSAGE)
                class_name, method_name = method_name.split(".")
                worker_name = ".".join((instance_name,yegg_name,class_name))
                worker_process = WORKER_PROCESSES.get(worker_name, None)

                if worker_process is None:
                    yegg = __import__(yegg_name, globals(), locals(), [], -1)
                    worker_class = getattr(yegg, class_name)
                    request = Request(instance_name=instance_name,
                                      callback=callback)
                    WORKER_PROCESSES[worker_name] = worker_class(request,
                                                                 *params)
                    WORKER_PROCESSES[worker_name].start()
                else:
                    # Run the method as a thread to avoid blocking issue
                    request = Request(instance_name=instance_name,
                                      callback=callback)
                    func = getattr(worker_process, method_name)
                    parameters = [request, func] + params
                    thread.start_new_thread(run_method, tuple(parameters))
            except Exception, e:
                callback(FLAG_ERR, e)
        else:
            try:
                socket.send(INIT_MESSAGE)
                yegg = __import__(yegg_name, globals(), locals(), [], -1)
                method = getattr(yegg, method_name)
                request = Request(instance_name=instance_name,
                                  callback=callback)
                parameters = [request, method] + params
                thread.start_new_thread(run_method, tuple(parameters))
            except Exception, e:
                callback(FLAG_ERR, e)

    sys.exit(0)
