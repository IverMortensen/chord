import hashlib
import logging as log
import sys
import random
from http.server import ThreadingHTTPServer
from time import sleep
from threading import Thread

from chord_node import ChordNode
from log import init_logger
from http_handler import create_handler


def run_periodic_function(func, min_delay=5, max_delay=10):
    """Run a function periodically with random delays"""
    while True:
        delay = random.uniform(min_delay, max_delay)
        sleep(delay)
        func()


def main():
    init_logger()
    log.info("Python script started.")
    endpoint = sys.argv[1]
    m = int(sys.argv[2])
    ip, port = endpoint.split(":")
    port = int(port)

    # Hash ip and port to avoid collisions if the same node is used twice
    hash = hashlib.sha1(endpoint.encode()).hexdigest()
    id = int(hash, 16) % (2**m)

    # Setup chord node
    node = ChordNode(ip=ip, port=port, id=id, m=m)
    log.info(f"Node initialized: \n\tID: {id} \n\tm: {m}")

    # Schedule periodic functions
    stabilize = Thread(
        target=run_periodic_function, args=(node.stabilize,), daemon=True
    )
    # fix_fingers = Thread(
    #     target=run_periodic_function, args=(node.fix_fingers,), daemon=True
    # )
    check_predecessor = Thread(
        target=run_periodic_function, args=(node.check_predecessor,), daemon=True
    )

    stabilize.start()
    # fix_fingers.start()
    check_predecessor.start()

    # Start HTTP server
    handler = create_handler(node)
    http_server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    log.info(f"HTTP server started: {ip}:{port}")

    http_server.serve_forever()


if __name__ == "__main__":
    main()
