import hashlib
import logging as log
import sys
from http.server import ThreadingHTTPServer
from time import sleep
from threading import Thread

from chord_node import ChordNode
from log import init_logger
from http_handler import create_handler


def start_http(port: int, node: ChordNode):
    handler = create_handler(node)
    http_server = ThreadingHTTPServer(("0.0.0.0", port), handler)

    server_thread = Thread(target=http_server.serve_forever)
    server_thread.daemon = True
    server_thread.start()


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
    log.info(f"Node initialized: id:{id}, m:{m}")

    # Start HTTP server
    try:
        start_http(port, node)
        log.info(f"HTTP server started: {ip}:{port}")
    except Exception as e:
        log.error(f"Failed to start HTTP server for {endpoint}: {e}")

    while True:
        sleep(1)


if __name__ == "__main__":
    main()
