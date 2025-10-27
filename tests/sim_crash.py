import sys

from utils import sim_crash, sim_recover, stabilize

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: [host:port ...]")
        sys.exit(1)
    host_ports = sys.argv[1:]
    num_nodes = len(host_ports) - 1
    crashed_nodes = []
    max = 0

    for i in range(1, num_nodes):
        print(f"Crashing {i} node(s)...")
        for j in range(i):
            node = host_ports.pop(0)
            sim_crash(node)
            crashed_nodes.append(node)

        print("Waiting for nodes to stabilize...")
        res = stabilize(host_ports, 120)
        if not res:
            print("")
            break
        max = i

        print(f"Recovering {i} node(s)...")
        for j in range(i):
            node = crashed_nodes.pop(0)
            sim_recover(node)
            host_ports.append(node)
        print("")

    print(f"Recovering {num_nodes} node(s)...")
    for node in crashed_nodes:
        sim_recover(node)
        host_ports.append(node)

    print("Waiting for nodes to stabilize...")
    if not stabilize(host_ports):
        print("Timelimit reached. Chord ring is still not stable.")

    print(f"\nNumber of crashed nodes chord ring handled: {max}")
