from typing import List

import logging as log
import hashlib
import chord_client
from chord_logger import ChordLogger


class ChordNode:
    def __init__(self, ip: str, port: int, id: int, m: int):
        self.ip: str = ip
        self.port: int = port
        self.address = f"{ip}:{port}"
        self.m: int = m

        self.id: int = id
        self.successor: str = self.address
        self.predecessor: str | None = None
        self.finger_table: List[str | None] = [None] * (self.m + 1)
        self.storage = {}

        self.logger = ChordLogger(
            self, f"/mnt/users/imo059/chord_logs/chord_log-{self.id}.log"
        )

    def create(self):
        self.predecessor = None
        self.successor = self.address
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

    def stabilize(self):
        # Get our successor's predecessor
        response = chord_client.get_predecessor(self.successor)
        if not response or response.status_code == 404:
            log.info("Successor doesn't have a predecessor.")
        elif response.status_code != 200:
            log.error(
                "Stabilize failed. " +
                f"Could not find predecessor of {self.successor}: {response.text}"
            )

        # If successor has a predecessor...
        if response and response.status_code == 200:
            successor_id = self.hash_key(self.successor)
            predecessor = response.text

            # If our successor's predecessor is us everything is fine
            if predecessor == self.address:
                return

            predecessor_id = self.hash_key(predecessor)

            # Check if the predecessor is within us and our successor
            within = False
            if self.id < successor_id:
                within = predecessor_id > self.id and predecessor_id <= successor_id
            else:
                within = predecessor_id > self.id or predecessor_id <= successor_id

            # If this is the case update our successor
            if within:
                self.successor = predecessor
                self.logger.updated_successor(predecessor_id)

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
                    new_predecessor_id > predecessor_id
                    and new_predecessor_id <= self.id
                )
            else:
                within = (
                    new_predecessor_id > predecessor_id or new_predecessor_id <= self.id
                )

        # If predecessor isn't set or new predecessor is within, update predecessor
        if self.predecessor is None or within:
            self.predecessor = new_predecessor
            self.logger.updated_predecessor(new_predecessor_id)

    def fix_fingers(self):
        old_table = self.finger_table.copy()
        for i in range(1, self.m + 1):
            id = (self.id + 2 ** (i - 1)) % (2**self.m)
            self.finger_table[i] = self.find_successor(id)

        # Only log on change
        if old_table != self.finger_table:
            self.logger.fix_fingers()

    def check_predecessor(self):
        if self.predecessor is None:
            return

        response = chord_client.get_status(self.predecessor)
        if not response or response.status_code != 200:
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
            successor_id = self.hash_key(finger)

            # Check if id is within finger node
            within = False
            if self.id < id:
                within = successor_id > self.id and successor_id < id
            else:
                within = successor_id > self.id or successor_id < id

            # If within return the finger node
            if within:
                return finger

        return None

    def find_successor(self, id: int) -> str | None:
        if not self.successor:
            log.error(f"Node {self.id} does not have a successor")
            return None

        successor_id = self.hash_key(self.successor)

        # Check if the id is within the first successor
        within = False
        if self.id < successor_id:
            within = id > self.id and id <= successor_id
        else:
            within = id > self.id or id <= successor_id

        # If within first successor, return first successor
        if within:
            self.logger.found_successor(id, successor_id)
            return self.successor

        # If not within successor, find and return the closest known node
        closest_node = self.closest_preceding_node(id)
        if closest_node:
            closest_node_id = self.hash_key(closest_node)
            self.logger.passing_successor_check(id, closest_node_id)
            log.info(
                f"{closest_node_id} is the closest node to {id}. Passing search to {closest_node_id}"
            )

            # Pass the find successor check to the closest node and return its result
            response = chord_client.find_successor(closest_node, id)
            if response.status_code != 200:
                return None
            successor = response.text
            return successor

        # No successor found
        self.logger.passing_successor_check(id, successor_id)
        log.info(
            f"Can't find the owner of {id}. Passing search to successor {successor_id}"
        )

        # Pass the find successor check to the successor node and return its result
        response = chord_client.find_successor(self.successor, id)
        if response.status_code != 200:
            return None
        successor = response.text
        return successor
