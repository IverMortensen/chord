import sys

from utils import stabilize, join_ring


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    num_nodes = int(sys.argv[1])
    host_ports = sys.argv[2:]

    if num_nodes != len(host_ports):
        print(f"    Expected {num_nodes} nodes, got {len(host_ports)}!")

    # Tell all nodes to join
    for node in host_ports[1:]:
        join_ring(node, host_ports[0])

    stabilize(host_ports)
