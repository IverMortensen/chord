from __future__ import annotations
from typing import List
import requests

import logging as log
import hashlib
from chord_logger import ChordLogger


class ChordNode:
    def __init__(self, ip: str, port: int, id: int, m: int):
        self.ip: str = ip
        self.port: int = port
        self.address = f"{ip}:{port}"
        self.m: int = m

        self.id: int = id
        self.successor: str | None = None
        self.finger_table: List[str | None] = [None] * (self.m + 1)
        self.storage = {}

        self.logger = ChordLogger(
            self, f"/mnt/users/imo059/chord_logs/chord_log-{self.id}.log"
        )

    def get_id(self) -> int:
        return self.id

    def get_successor(self) -> str | None:
        return self.successor

    def get_endpoint(self) -> str:
        return f"{self.ip}:{self.port}"

    def get_ip(self) -> str:
        return self.ip

    def get_port(self) -> int:
        return self.port

    def fix_fingers(self):
        for i in range(1, self.m + 1):
            id = (self.id + 2 ** (i - 1)) % (2**self.m)
            self.finger_table[i] = self.find_successor(id)
        self.logger.fix_fingers()

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
        self.logger.check_key(id)
        log.info(f"{self.id} checking {id}...")
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
            log.info(f"{successor_id} is the onwner of {id}")
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
            response = requests.get(f"http://{closest_node}/successor/{id}")
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
        response = requests.get(f"http://{self.successor}/successor/{id}")
        if response.status_code != 200:
            return None
        successor = response.text
        return successor
