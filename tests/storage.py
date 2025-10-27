import sys
import random

from utils import store_value, get_value


def test_store_value(nodes: list):
    num_values = len(nodes) // 2
    num_nodes = len(nodes)

    print(f"Storing {num_values} values...")
    for i in range(0, num_values):
        key_value = str(i)
        node_idx = i
        node = nodes[node_idx % num_nodes]

        store_value(node, key_value, key_value)
    print("Done.")


def test_get_value(nodes: list):
    num_values = len(nodes) // 2
    num_nodes = len(nodes)

    print("Retrieving from same nodes...")
    for i in range(0, num_values):
        key_value = str(i)
        node_idx = i
        node = nodes[node_idx % num_nodes]

        value = get_value(node, key_value)
        if value is None:
            print("    ERROR: Got no value.")
        elif value != key_value:
            print("    ERROR: Got wrong value.")
    print("Done.")

    print("Retrieving different nodes...")
    for i in range(0, num_values):
        key_value = str(i)
        node_idx = random.randint(0, num_nodes - 1)
        node = nodes[node_idx % num_nodes]

        value = get_value(node, key_value)
        if value is None:
            print("    ERROR: Got no value.")
        elif value != key_value:
            print("    ERROR: Got wrong value.")
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 1:
        sys.exit(1)
    host_ports = sys.argv[1:]

    test_store_value(host_ports)
    test_get_value(host_ports)
