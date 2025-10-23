# 3200-a3
Assignment 3 in INF-3200: Distributed hash table using Chord.

## How to run
The only step required is to run the **run.sh** script with a given number of chord nodes.
```bash
./run.sh <num_chord_nodes> [m]
```
- `num_chord_nodes`: Number of nodes to create in the Chord ring
- `m`: Optional parameter that determines the size of the identifier space (defaults to 8 if not specified)

The run script will:
1. Start up all nodes with unique IDs, no collitions (just make sure `m` is large enough so the chord ring can fit all the nodes).
2. Check that all the nodes are working, replacing any that don't.
3. Tell all the nodes to join the network of one boot node.
4. Wait for all the nodes to join the network, and to establish a complete chord ring,
where every node is present.

## API
These are the endpoints meant for client interaction.

### GET
**Get network information:**
# 3200-a3
Assignment 3 in INF-3200: Distributed hash table using Chord.

## How to run
The only step required is to run the **run.sh** script with a given number of chord nodes.
```bash
./run.sh <num_chord_nodes> [m]
```
- `num_chord_nodes`: Number of nodes to create in the Chord ring
- `m`: Optional parameter that determines the size of the identifier space (defaults to 8 if not specified)

The run script will:
1. Start up all nodes with unique IDs
2. Check that all the nodes are working, replacing any that don't
3. Tells all the nodes to join the network of one boot node.
4. Waits for all the nodes to join the network, and to establish a complete chord ring,
where every node is present

## API
These are the enpoints meant for external interaction.

### GET
**Get node's successor:**
```
GET http://<node_ip_port>/successor
```
The node will check if it can reach it's successor, and if it can it will respond with the successors address.
This is useful for walking along the entire chord ring to see all the nodes, and to make sure the ring is whole.

**Get node information:**
```
GET http://<node_ip_port>/node-info
```
Lists node identifier, successor address, and neighbour addresses.

**Get network information:**
```
GET http://<node_ip_port>/network
```
Lists all nodes that the connected node knows about.

**Retrieve stored value:**
```
GET http://<node_ip_port>/storage/<key>
```
Retrieves the value associated with the given key.

---

### PUT
**Store a value:**
```
PUT http://<node_ip_port>/storage/<key>
Body: <value>
```
Stores the value (from request body) with the given key.

---

### POST
**Post join:**
```
POST http://<node_ip_port>/join?nprime=<other_node>
```
Tell a node to join the other node's chord network.

**Post leave:**
```
POST http://<node_ip_port>/leave
```
Tell a node to leave it's current network.
The node will create a new network with only itself.

---
