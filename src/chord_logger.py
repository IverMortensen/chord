from __future__ import annotations
import json
import time
import os
import logging as log
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from chord_node import ChordNode


class ChordLogger:
    def __init__(self, node: ChordNode, log_file: str):
        self.node = node
        self.log_file = log_file

    def log_event(self, event_type, **kwargs):
        event = {
            "timestamp": time.time(),
            "node_id": self.node.id,
            "event": event_type,
            **kwargs,
        }
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)

        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def log_node_status(self):
        if not self.node.successor:
            self.log_event(
                "status",
                successor="None",
                num_keys=len(self.node.storage),
                storage=self.node.storage,
            )
            return

        self.log_event(
            "status",
            successor=self.node.hash_key(self.node.successor),
            num_keys=len(self.node.storage),
            storage=self.node.storage,
            m=self.node.m,
        )

    def log_client_request(self, request, key=None):
        if key:
            self.log_event("client_request", request=request, key=key)
        else:
            self.log_event("client_request", request=request)

    def join(self, node: int):
        log.info(f"Joined network of {node}")
        self.log_event("join_network", node=node)

    def leave(self):
        self.log_event("leave_network")

    def check_key(self, key):
        self.log_event("check_key", key=key)

    def found_successor(self, key, successor_id):
        self.log_event("found_successor", key=key, successor_id=successor_id)

    def updated_successor(self, successor_id):
        log.info(f"Updating successor: {self.node.id} -> {successor_id}")
        self.log_event("updated_successor", successor_id=successor_id)

    def updated_predecessor(self, predecessor_id):
        log.info(f"Updating predecessor: {predecessor_id} <- {self.node.id}")
        if predecessor_id == -1:
            self.log_event("updated_successor", predecessor_id="None")
        else:
            self.log_event("updated_successor", predecessor_id=predecessor_id)

    def updated_successor_list(self, successor_list: list):
        log.info(f"Updated successor list: {successor_list}")
        self.log_event("updated_successor_list", successor_list=successor_list)

    def passing_successor_check(self, key, successor_id):
        log.info(
            f"{successor_id} is the closest node to {key}."
            + f"Passing search to {successor_id}"
        )
        self.log_event("passing_successor_check", key=key, successor_id=successor_id)

    def insert_value(self, key, value):
        self.log_event("insert_key", key=key, value=value)

    def get_value(self, key, value):
        self.log_event("get_key", key=key, value=value)

    def fix_fingers(self):
        log.info("Fixing fingers")
        finger_table: List[str] = []
        for finger in self.node.finger_table[1:]:
            if not finger:
                finger_table.append("None")
                continue
            finger_id = self.node.hash_key(finger)
            finger_table.append(str(finger_id))

        self.log_event("fix_fingers", finger_table=finger_table)
