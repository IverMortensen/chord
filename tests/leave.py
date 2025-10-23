import sys

from utils import leave_ring, stabilize

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: <num_nodes_to_leave> [host:port ...]")
        sys.exit(1)
    num_nodes = int(sys.argv[1])
    host_ports = sys.argv[2:]

    if num_nodes > len(host_ports):
        print(f"Num nodes to leave {num_nodes} > nodes in ring {len(host_ports)}.")
        exit(1)

    for _ in range(num_nodes):
        node = host_ports.pop(0)
        leave_ring(node)

    stabilize(host_ports)

    print("Chordring after leave:")
    print(host_ports)
