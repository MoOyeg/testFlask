# Source: https://lightrun.com/how-to-perform-python-remote-debugging/

import multiprocessing
import os

def initialize_debugger(debug_port=None,debug_host=None,debug_wait=True):
    """Debugger Method"""
    debug_port = 5679 if debug_port is None else debug_port
    debug_host = "0.0.0.0" if debug_host is None else debug_host
    
    if multiprocessing.current_process().pid > 1:
        import debugpy
        debugpy.listen((debug_host, debug_port))
        if debug_wait:
            print("Debugger is ready to be attached, press F5", flush=True)
            debugpy.wait_for_client()
            print("Visual Studio Code debugger is now attached", flush=True)
