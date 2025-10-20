# 3200-a3
Assignment 3 in INF-3200: Distributed hash table using Chord.

## How to run
The only step required is to run the **run.sh** script with a given number of chord nodes.
```bash
./run.sh <num_chord_nodes> [m]
```
- `num_chord_nodes`: Number of nodes to create in the Chord ring
- `m`: Optional parameter that determines the size of the identifier space (defaults to 6 if not specified)

The run script will:
1. Start up all nodes with unique IDs
2. Set up successor relationships for all nodes
3. Configure finger tables for each node sequentially

## API
These endpoints are meant for client interactions.

### GET Endpoints
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

### PUT Endpoints
**Store a value:**
```
PUT http://<node_ip_port>/storage/<key>
Body: <value>
```
Stores the value (from request body) with the given key.
