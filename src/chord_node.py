import json
import random
from typing import List
from threading import Event, Thread

import logging as log
import hashlib
import chord_client
from chord_logger import ChordLogger


def run_periodic_function(func, stop_event, min_delay=10, max_delay=15):
    """Run a function periodically with random delays"""
    while not stop_event.is_set():
        delay = random.uniform(min_delay, max_delay)
        if stop_event.wait(delay):
            break
        func()


class ChordNode:
    def __init__(self, ip: str, port: int, id: int, m: int):
        self.ip: str = ip
        self.port: int = port
        self.address = f"{ip}:{port}"
        self.m: int = m
        self.r: int = 4

        self.id: int = id
        self.successor: str = self.address
        self.successor_list: List[str] = []
        self.predecessor: str | None = None
        self.finger_table: List[str | None] = [None] * (self.m + 1)
        self.next = m
        self.storage = {}
        self.sim_crash = False

        self.logger = ChordLogger(
            self, f"/mnt/users/imo059/chord_logs/chord_log-{self.id}.log"
        )
        self.start_periodic_functions()

    def start_periodic_functions(self):
        # Create stop event
        self.stop_event = Event()

        # Create threads for periodic functions
        self.stabilize_thread = Thread(
            target=run_periodic_function,
            args=(self.stabilize, self.stop_event, 1, 2),
            daemon=True,
        )
        self.fix_fingers_thread = Thread(
            target=run_periodic_function,
            args=(self.fix_fingers, self.stop_event, 3, 5),
            daemon=True,
        )
        self.check_predecessor_thread = Thread(
            target=run_periodic_function,
            args=(self.check_predecessor, self.stop_event, 1, 2),
            daemon=True,
        )

        # Start periodic functions threads
        self.stabilize_thread.start()
        self.fix_fingers_thread.start()
        self.check_predecessor_thread.start()

    def stop_periodic_functions(self):
        # Stop periodic functions threads
        self.stop_event.set()

        # Join the threads
        self.stabilize_thread.join()
        self.fix_fingers_thread.join()
        self.check_predecessor_thread.join()

    def create(self):
        self.predecessor = None
        self.successor = self.address
        self.successor_list = [self.address]
        self.logger.updated_successor(self.id)
        self.logger.updated_predecessor(-1)

    def join(self, other: str):
        self.predecessor = None
        self.logger.updated_predecessor(-1)

        # Find a successor within new network
        response = chord_client.find_successor(other, self.id)
        if response and response.status_code == 200:
            successor = response.text
        else:
            # If no successor is found, fallback by setting node joined as successor
            successor = other

        self.successor = successor
        successor_id = self.hash_key(successor)
        self.logger.updated_successor(successor_id)

    def update_successor_list(self):
        # Get the successor list of the successor
        response = chord_client.get_successor_list(self.successor)
        if response is None or response.status_code != 200:
            log.warning("Failed to get successor's successor list")
            return
        successor_list = list(json.loads(response.text))

        # Add successor to beginning of list
        successor_list.insert(0, self.successor)

        # Limit the size of the successor list
        self.successor_list = successor_list[0 : self.r]

        self.logger.updated_successor_list(self.successor_list)

    def stabilize(self):
        # If successor has failed, remove it from the successor list
        # and update our successor
        response = chord_client.get_status(self.successor)
        if response is None or response.status_code != 200:
            log.info(f"Successor {self.hash_key(self.successor)} has failed.")
            self.successor_list = self.successor_list[1:]

            # Check if successor list is empty
            if not self.successor_list:
                log.error(
                    "No more successors in successor list. Setting self to successor"
                )
                self.successor = self.address
                self.successor_list.append(self.address)
                return

            else:
                self.successor = self.successor_list[0]

        # Get our successor's predecessor
        response = chord_client.get_predecessor(self.successor)
        if response is None or response.status_code not in [200, 404]:
            log.error(
                f"Stabilize failed. Could not find predecessor of {self.successor}"
            )
            return

        # If successor has a predecessor...
        elif response.status_code == 200:
            predecessor = response.text
            successor_id = self.hash_key(self.successor)
            predecessor_id = self.hash_key(predecessor)

            if predecessor != self.address:
                # Check if the predecessor is within us and our successor
                within = False
                if self.id < successor_id:
                    within = predecessor_id > self.id and predecessor_id < successor_id
                else:
                    within = predecessor_id > self.id or predecessor_id < successor_id

                # If this is the case update our successor
                if within:
                    self.successor = predecessor
                    self.logger.updated_successor(predecessor_id)

        # Update successor list
        self.update_successor_list()

        # Notify successor that we might be its predecessor
        chord_client.notify(self.successor, self.address)

    def notify(self, new_predecessor: str):
        within = False
        new_predecessor_id = self.hash_key(new_predecessor)

        if self.predecessor:
            predecessor_id = self.hash_key(self.predecessor)

            # Check if the new predecessor is within current predecessor and us
            if predecessor_id < self.id:
                within = (
                    new_predecessor_id > predecessor_id and new_predecessor_id < self.id
                )
            else:
                within = (
                    new_predecessor_id > predecessor_id or new_predecessor_id < self.id
                )

        # If predecessor isn't set or new predecessor is within, update predecessor
        if self.predecessor is None or within:
            self.predecessor = new_predecessor
            self.logger.updated_predecessor(new_predecessor_id)

    def fix_fingers(self):
        self.next = self.next + 1

        if self.next > self.m:
            self.next = 1

        id = (self.id + 2 ** (self.next - 1)) % (2**self.m)
        finger = self.find_successor(id)
        if finger:
            self.finger_table[self.next] = finger

        self.logger.fix_fingers()

    def check_predecessor(self):
        if self.predecessor is None:
            return

        response = chord_client.get_status(self.predecessor)
        if response is None or response.status_code != 200:
            log.info(f"Predecessor {self.predecessor} has failed.")
            self.predecessor = None
            self.logger.updated_predecessor(-1)

    def insert_value(self, key: str, value: str):
        self.logger.insert_value(key, value)
        self.storage[key] = value

    def get_value(self, key: str) -> str | None:
        value = self.storage.get(key, None)
        self.logger.get_value(key, value)
        return value

    def hash_key(self, key: str) -> int:
        hash = hashlib.sha1(key.encode()).hexdigest()
        return int(hash, 16) % (2**self.m)

    def closest_preceding_node(self, id: int) -> str | None:
        # Loop through finger table from last to first
        for i in range(self.m, 0, -1):
            finger = self.finger_table[i]
            if not finger:
                continue

            # Check that the id is within finger node
            within = False
            successor_id = self.hash_key(finger)
            if self.id < id:
                within = successor_id > self.id and successor_id < id
            else:
                within = successor_id > self.id or successor_id < id
            if not within:
                continue

            # Check that node is available
            response = chord_client.get_status(finger)
            if response is None or response.status_code != 200:
                self.finger_table[i] = None
                log.warning(f"Can't get a response from {successor_id}.")
                continue

            # Return the first available node
            return finger

        log.warning(f"Can't find the closest node to {id}.")
        return None

    def find_successor(self, id: int) -> str | None:
        # Check if the id is within the node's successor
        # If so, and its available, return the successor
        within = False
        successor_id = self.hash_key(self.successor)
        if self.id < successor_id:
            within = id > self.id and id <= successor_id
        else:
            within = id > self.id or id <= successor_id

        if within:
            # Check that successor is available
            response = chord_client.get_status(self.successor)
            if response and response.status_code == 200:
                # Return the successor
                self.logger.found_successor(id, successor_id)
                return self.successor

        # If not within successor or successor isn't available
        # Find and return the closest known node
        closest_node = self.closest_preceding_node(id)
        if closest_node:
            closest_node_id = self.hash_key(closest_node)

            # Pass the find successor check to the closest node and return its result
            self.logger.passing_successor_check(id, closest_node_id)
            response = chord_client.find_successor(closest_node, id)
            if response is None or response.status_code != 200:
                log.warning(
                    f"Failed to pass successor check to closest node {closest_node_id}."
                )
                return None
            return response.text

        # No successor found
        # Pass the successor check to the successor and return its result
        self.logger.passing_successor_check(id, successor_id)
        response = chord_client.find_successor(self.successor, id)
        if response is None or response.status_code != 200:
            log.warning(f"Failed to pass successor check to successor {successor_id}.")
            return None
        successor = response.text
        return successor
