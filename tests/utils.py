import requests
import time


def leave_ring(node: str):
    response = requests.post(f"http://{node}/leave")
    print(f"    {node} LEAVE response: {response.status_code}")


def join_ring(new_node, existing_ring_node):
    response = requests.post(f"http://{new_node}/join?nprime={existing_ring_node}")
    if response.status_code != 200:
        print(f"    {new_node} JOIN response: {response.status_code}.")


def get_successor(node):
    successor = ""
    try:
        response = requests.get(f"http://{node}/successor")
        if response.status_code == 200:
            successor = response.text
    except:
        pass

    return successor


def sim_crash(node: str):
    response = requests.post(f"http://{node}/sim-crash")
    print(f"    {node} SIM-CRASH response: {response.status_code}")


def sim_recover(node: str):
    response = requests.post(f"http://{node}/sim-recover")
    print(f"    {node} SIM-RECOVER response: {response.status_code}")


def stabilize(host_ports, max_time=300, verbose=True):
    """
    Wait for all nodes to join and stabilize in the ring.
    """
    unique_nodes_in_ring = set()
    unique_nodes_in_ring.add(host_ports[0])
    current_node = host_ports[0]

    start_time = time.time()
    end_time = start_time + max_time

    while len(unique_nodes_in_ring) < len(host_ports) and time.time() < end_time:
        time.sleep(0.1)
        successor = get_successor(current_node)

        if successor:
            unique_nodes_in_ring.add(current_node)
            current_node = successor

        # If a node doesn't respond, start from the first node again
        else:
            current_node = host_ports[0]

    elapsed_time = time.time() - start_time
    success = len(unique_nodes_in_ring) == len(host_ports)

    if verbose:
        if success:
            print("    All nodes stabilized.")
        else:
            print("    Timeout. Some nodes can't be found.")
            print(f"    Nodes found: {len(unique_nodes_in_ring)} / {len(host_ports)}")
        print(f"    Time: {round(elapsed_time, 1)}s")

    return success
