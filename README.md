# Chord
Distributed hash table implementation using the Chord protocol.

## How to run
Run the **run.sh** script with the desired number of Chord nodes:
```bash
./run.sh <num_chord_nodes> [m]
```

**Parameters:**
- `num_chord_nodes`: Number of nodes to create in the Chord ring
- `m`: (Optional) Bit length of the identifier space. Determines ring size as 2^m (default: 8)

**What the script does:**
1. Starts all nodes with unique IDs
2. Verifies all nodes are running, replacing any that fail
3. Instructs all nodes to join the network via a bootstrap node
4. Waits for ring stabilization until all nodes are connected

## API

### GET Endpoints

**Get node's successor:**
```
GET http://<node_ip:port>/successor
```
Returns the address of the node's successor if reachable. Useful for walking the ring and verifying ring completeness.

**Get node information:**
```
GET http://<node_ip:port>/node-info
```
Returns node identifier, successor address, and finger table entries.

**Get network information:**
```
GET http://<node_ip:port>/network
```
Returns all nodes known to this node.

**Retrieve stored value:**
```
GET http://<node_ip:port>/storage/<key>
```
Retrieves the value associated with the given key.

### PUT Endpoints

**Store a value:**
```
PUT http://<node_ip:port>/storage/<key>
Body: <value>
```
Stores the value (from request body) under the given key.

### POST Endpoints

**Join network:**
```
POST http://<node_ip:port>/join?nprime=<bootstrap_node>
```
Instructs the node to join the Chord network via the specified bootstrap node.

**Leave network:**
```
POST http://<node_ip:port>/leave
```
Instructs the node to leave its current network. The node will transfer its data to its successor and form a singleton network.

## Examples

**Starting a 10-node ring with m=6:**
```bash
./run.sh 10 6
```

**Storing and retrieving a value:**
```bash
# Store
curl -X PUT http://c7-15:50516/storage/mykey -d "myvalue"

# Retrieve
curl http://c7-15:50516/storage/mykey
```

**Walking the ring:**
```bash
curl http://c7-15:50516/successor
```
