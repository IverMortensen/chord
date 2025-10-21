import json
from http.server import BaseHTTPRequestHandler
import logging as log

from chord_node import ChordNode
import chord_client


class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, node: ChordNode, *args, **kwargs):
        self.node = node
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """
        Handles get requests.
        """
        # Check the path and run the associated function
        if self.path == ("/status"):
            self.get_status()

        elif self.path == ("/predecessor"):
            self.get_predecessor()

        elif self.path.startswith("/storage/"):
            try:
                key = self.path.split("/storage/")[1]
            except (ValueError, IndexError):
                self.send_error(400, "Invalid key format")
                return
            self.get_storage(key)

        elif self.path.startswith("/value/"):
            try:
                key = self.path.split("/value/")[1]
                self.get_value(key)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid key format")

        elif self.path.startswith("/find_successor/"):
            try:
                key = self.path.split("/find_successor/")[1]
                self.get_find_successor(int(key))
            except (ValueError, IndexError):
                self.send_error(400, "Invalid key format")

        elif self.path == "/network":
            self.get_network()

        # Unknown paths receive a 404
        else:
            self.send_error(404, "Not Found")

    def do_PUT(self):
        """
        Handles put requests.
        """
        # Check the path and run the associated function
        if self.path.startswith("/value/"):
            try:
                key = self.path.split("/value/")[1]
                self.put_value(key)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid key format")

        elif self.path.startswith("/storage/"):
            try:
                key = self.path.split("/storage/")[1]
                self.put_storage(key)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid key format")

        elif self.path == "/notify":
            self.put_notify()

        elif self.path == "/fix_fingers":
            self.put_fix_fingers()

        elif self.path == "/successor":
            self.put_successor()

        # Unknown paths receive a 404
        else:
            self.send_error(404, "Not Found")

    def get_status(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def get_predecessor(self):
        predecessor = self.node.predecessor
        if predecessor is None:
            self.send_error(404, f"{self.node.id} does not have a predecessor")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(predecessor.encode("utf-8"))

    def get_value(self, key: str):
        value = self.node.get_value(key)
        if value is None:
            self.send_error(404, f"{self.node.id} is not the owner of '{key}'")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(value.encode("utf-8"))

    def get_find_successor(self, key: int):
        # Find successor
        successor = self.node.find_successor(key)
        if not successor:
            self.send_error(404, f"Couldn't find owner of key '{key}'")
            return

        # Send response containing the successor
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(successor.encode("utf-8"))

    def get_storage(self, raw_key: str):
        """
        Retrieves the value associated with the given key from the DHT.
        Response:
            200 and the value if the value is found
            404 if key can't be found
            400 if process fails
        """
        key = self.node.hash_key(raw_key)
        self.node.logger.log_client_request("get_storage", key)

        # Find responsible node
        successor = self.node.find_successor(key)
        if not successor:
            self.send_error(404, f"Couldn't find owner of key '{key}'")
            return

        # Get the value
        response = chord_client.get_value(successor, raw_key)
        if response.status_code != 200 or response.text is None:
            self.send_error(response.status_code, response.text)
            return
        value = response.text

        # Send response containing the value
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(value.encode("utf-8"))

    def get_network(self):
        """
        Retrieves all known neighbors of a node.
        Response:
            200 and a list of ip:port of each of the nodes
        """
        self.node.logger.log_client_request("get_network")

        # Get all neighbors
        neighbours = set()
        for finger in self.node.finger_table[1:]:
            if finger:
                neighbours.add(finger)

        # Send response containing the neighbors
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(list(neighbours)).encode())

    def put_notify(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            self.send_error(400, "Empty request body")
            return

        # Get the predecessor from the body
        body = self.rfile.read(content_length)
        try:
            predecessor = body.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.send_error(400, "Invalid UTF-8 encoding")
            return

        self.node.notify(predecessor)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def put_value(self, key: str):
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            self.send_error(400, "Empty request body")
            return

        # Get the value from the body
        body = self.rfile.read(content_length)
        try:
            value = body.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.send_error(400, "Invalid UTF-8 encoding")
            return

        self.node.insert_value(key, value)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def put_storage(self, raw_key: str):
        """
        Inserts a key value pair in the DHT.
        Response:
            200 on successful insertion
            400 if process fails
        """
        key = self.node.hash_key(raw_key)
        self.node.logger.log_client_request("put_storage", key=key)

        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            self.send_error(400, "Empty request body")
            return

        # Get the value from the body
        body = self.rfile.read(content_length)
        try:
            value = body.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.send_error(400, "Invalid UTF-8 encoding")
            return

        # Find responsible node
        successor = self.node.find_successor(key)
        if not successor:
            self.send_error(400, f"Couldn't find owner of key '{key}'")
            return

        # Insert value
        response = chord_client.set_value(successor, raw_key, value)
        if response.status_code != 200:
            self.send_error(response.status_code, response.text)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(value.encode("utf-8"))

    def put_successor(self):
        """
        Updates the nodes successor.
        Response:
            200 on successful update
            400 if process fails
        """
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            self.send_error(400, "Empty request body")
            return

        # Get the successor from the body
        body = self.rfile.read(content_length)
        try:
            successor_endpoint = body.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.send_error(400, "Invalid UTF-8 encoding")
            return

        # Set the nodes new successor
        self.node.successor = successor_endpoint

        successor_id = self.node.hash_key(successor_endpoint)
        log.info(f"{self.node.id} -> {successor_id}")

        self.node.logger.log_node_status()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def put_fix_fingers(self):
        """
        Tells a node to update its finger table
        Response:
            200 when node has received the request
        """
        self.node.fix_fingers()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()


def create_handler(node: ChordNode):
    def handler(*args, **kwargs):
        return HTTPHandler(node, *args, **kwargs)

    return handler
