import sys

from utils import sim_crash, sim_recover, stabilize

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: <num_nodes_to_crash> [host:port ...]")
        sys.exit(1)
    num_nodes = int(sys.argv[1])
    host_ports = sys.argv[2:]

    if num_nodes > len(host_ports):
        print(f"Num nodes to crash {num_nodes} > nodes in ring {len(host_ports)}.")
        exit(1)

    print(f"Crashing {num_nodes} node(s)...")
    crashed_nodes = []
    for _ in range(num_nodes):
        node = host_ports.pop(0)
        sim_crash(node)
        crashed_nodes.append(node)

    print("Waiting for nodes to stabilize...")
    stabilize(host_ports)

    print(f"Recovering {num_nodes} node(s)...")
    for node in crashed_nodes:
        sim_recover(node)
        host_ports.append(node)

    print("Waiting for nodes to stabilize...")
    stabilize(host_ports)
