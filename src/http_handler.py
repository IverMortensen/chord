import json
from http.server import BaseHTTPRequestHandler

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
        if self.node.sim_crash:
            return

        # Check the path and run the associated function
        if self.path == ("/status"):
            self.get_status()

        elif self.path == ("/node-info"):
            self.get_node_info()

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

        elif self.path == "/successor_list":
            self.get_successor_list()

        # Unknown paths receive a 404
        else:
            self.send_error(404, "Not Found")

    def do_PUT(self):
        """
        Handles put requests.
        """
        if self.node.sim_crash:
            return

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

        elif self.path == "/predecessor":
            self.put_predecessor()

        # Unknown paths receive a 404
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """
        Handles post requests.
        """
        # Only sim-recover should be available when simulating a crash
        if self.node.sim_crash:
            if self.path == "/sim-recover":
                self.post_sim_recover()
            return

        if self.path.startswith("/join"):
            try:
                address = self.path.split("?nprime=")[1]
                self.post_join(address)
            except (ValueError, IndexError):
                self.send_error(400, "Invalid key format")

        elif self.path == "/leave":
            self.post_leave()

        elif self.path == "/sim-crash":
            self.post_sim_crash()

        elif self.path == "/sim-recover":
            self.post_sim_recover()

        # Unknown paths receive a 404
        else:
            self.send_error(404, "Not Found")

    def get_status(self):
        """
        Check if a node is reachable.
        Response:
            200 When request has been received
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def get_node_info(self):
        """
        Get info about the node.
        Response:
            200 Successful and the info in the body.
        """
        # Get all neighbors
        neighbours = set()
        for finger in self.node.finger_table[1:]:
            if finger:
                neighbours.add(finger)

        # Construct the info message
        info = {
            "node_hash": self.node.id,
            "successor": self.node.successor,
            "others": list(neighbours),
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(info).encode())

    def get_predecessor(self):
        """
        Get the predecessor the node.
        Response:
            200 Successful and the predecessor in the body
            404 If the nodes does not have a predecessor
        """
        predecessor = self.node.predecessor
        if predecessor is None:
            self.send_error(404, f"{self.node.id} does not have a predecessor")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(predecessor.encode("utf-8"))

    def get_value(self, key: str):
        """
        Get a value from the nodes key value store.
        Response:
            200 Successful and the value in the body
            404 If the nodes doesn't have the value
        """
        value = self.node.get_value(key)
        if value is None:
            self.send_error(404, f"{self.node.id} is not the owner of '{key}'")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(value.encode("utf-8"))

    def get_find_successor(self, key: int):
        """
        Finds the node with the given key.
        Response:
            200 Successful and the node with the key in the body
            404 Couldn't find the owner of the key
        """
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
            500 Issue with connecting to the owner of the key
        """
        key = self.node.hash_key(raw_key)
        self.node.logger.log_client_request("get_storage", key)

        # Find responsible node
        successor = self.node.find_successor(key)
        if not successor:
            self.send_error(404, f"Couldn't find the owner of key '{key}'")
            return

        # Get the value
        response = chord_client.get_value(successor, raw_key)
        if response is None:
            self.send_error(500, f"Couldn't connect to owner of key '{key}'")
            return
        if response.status_code != 200:
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
            200 Successful and a list of ip:port of each of the nodes
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

    def get_successor_list(self):
        """
        Retrieves the successor list of the node.
        Response:
            200 Successful and the successor list
        """
        # Send response containing the neighbors
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(self.node.successor_list).encode())

    def put_notify(self):
        """
        Notifies a node that the given node in the body might be its predecessor.
        Response:
            200 on successful delivery
            400 Empty body or invalid encoding
        """
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
        """
        Inserts a value into the nodes key value store.
        Response:
            200 On successful insertion
            400 Empty body or invalid encoding
        """
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
            200 On successful insertion
            400 Empty body or invalid encoding
            500 Internal error
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
        if response is None:
            self.send_error(500, "Error occured while setting value")
            return
        if response.status_code != 200:
            self.send_error(response.status_code, response.text)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(value.encode("utf-8"))

    def put_fix_fingers(self):
        """
        Tells the node to update its finger table
        Response:
            200 when request has been received
        """
        self.node.fix_fingers()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def put_successor(self):
        """
        Tells a node to update its successor.
        Response:
            200 When request has been received
            400 Empty body or invalid encoding
        """
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            self.send_error(400, "Empty request body")
            return

        # Get the value from the body
        body = self.rfile.read(content_length)
        try:
            successor = body.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.send_error(400, "Invalid UTF-8 encoding")
            return

        # Update successor
        self.node.successor = successor

        successor_id = self.node.hash_key(successor)
        self.node.logger.updated_successor(successor_id)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def put_predecessor(self):
        """
        Tells a node to update its predecessor.
        Response:
            200 When request has been received
            400 Empty body or invalid encoding
        """
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            self.send_error(400, "Empty request body")
            return

        # Get the value from the body
        body = self.rfile.read(content_length)
        try:
            predecessor = body.decode("utf-8").strip()
        except UnicodeDecodeError:
            self.send_error(400, "Invalid UTF-8 encoding")
            return

        # Update predecessor
        self.node.predecessor = predecessor

        predecessor_id = self.node.hash_key(predecessor)
        self.node.logger.updated_predecessor(predecessor_id)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def post_join(self, node: str):
        """
        Tells the node to join the chord network of the given node
        Response:
            200 when request has been received
        """
        # Join the other nodes network
        self.node.join(node)

        node_id = self.node.hash_key(node)
        successor_id = self.node.hash_key(self.node.successor)
        self.node.logger.join(node_id)
        self.node.logger.updated_successor(successor_id)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def post_leave(self):
        """
        Tells a node to leave the network and be in its own network.
        Response:
            200 When request has been received
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        self.node.logger.leave()

        # Make successor node and predecessor node point to each other
        if self.node.predecessor and self.node.successor:
            chord_client.set_successor(self.node.predecessor, self.node.successor)
            chord_client.set_predecessor(self.node.successor, self.node.predecessor)

        # Send keys to successor
        for key, value in self.node.storage.items():
            chord_client.set_value(self.node.successor, key, value)

        # Leave the network by creating a new network
        self.node.create()

    def post_sim_crash(self):
        """
        Tells a node to simulate that it has crashed.
        Response:
            200 When request has been received
        """
        self.node.logger.log_client_request("sim-crash")
        self.node.stop_periodic_functions()
        self.node.sim_crash = True

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def post_sim_recover(self):
        """
        Tells a node to end simulated crash.
        Response:
            200 When request has been received
        """
        self.node.logger.log_client_request("sim_recover")
        self.node.start_periodic_functions()
        self.node.sim_crash = False

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()


def create_handler(node: ChordNode):
    def handler(*args, **kwargs):
        return HTTPHandler(node, *args, **kwargs)

    return handler
