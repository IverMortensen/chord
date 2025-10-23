#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <num_chord_nodes> [m]"
    exit 1
fi

num_nodes=$1
m=${2:-8}
target="./src/"
active_nodes_file="active_nodes.txt"
stdout_dir="./stdout"
mkdir -p "$stdout_dir"

all_nodes=()
nodes=()
ports=()
endpoints=()
hashes=()
ids=()

# Function to find an available port and a unique ID
find_available_port_and_id() {
    local i=$1
    local node="${nodes[$i]}"

    while true; do
        local port=$(shuf -i 49152-65535 -n1)

        # Check if port is available
        if ssh "$USER@$node" "ss -tuln | grep -q ':${port} '"; then
            echo "Port $port is in use on $node, trying another port..."
            continue
        fi

        local endpoint="${node}:${port}"
        local hash=$(echo -n "$endpoint" | sha1sum | cut -d' ' -f1)
        local id=$(python3 -c "print(int('$hash', 16) % (2**$m))")

        # Check if this ID has been seen before
        if [[ -z "${seen_ids[$id]}" ]]; then
            seen_ids[$id]=1
            ports[$i]="$port"
            endpoints[$i]="$endpoint"
            hashes[$i]="$hash"
            ids[$i]="$id"
            break
        else
            echo "    ID collision detected ($id), regenerating port for ${node}..."
        fi
    done
}

# Function to start a process on a node
start_chord_node() {
    local i=$1
    local node="${nodes[$i]}"
    local node_endpoint="${endpoints[$i]}"
    local id="${ids[$i]}"

    printf "    %-15s %s\n" "$node_endpoint" "$id"

    local temp_dir="/tmp/chord-$$-$id"
    {
        ssh "$USER@$node" "mkdir -p $temp_dir" &&
            scp -r "$target" "$USER@$node:$temp_dir/" &&
            ssh "$USER@$node" "cd $temp_dir/src/ && python3 -u main.py $node_endpoint $m"
    } >"${stdout_dir}/${node}-${i}.log" 2>&1 &
}
echo "Finding nodes and assigning ports..."

# Get available nodes
readarray -t all_nodes < <(./nodes_by_load.sh)
num_available_nodes=${#all_nodes[@]}

if [ $num_available_nodes -eq 0 ]; then
    echo "    No nodes available."
    exit 1
fi

# Select random nodes
if [ $num_available_nodes -ge $num_nodes ]; then
    readarray -t nodes < <(printf '%s\n' "${all_nodes[@]}" | shuf -n "$num_nodes")
else
    # Extend nodes with repeats if not enough nodes
    readarray -t nodes < <(printf '%s\n' "${all_nodes[@]}" | shuf)
    missing_nodes=$((num_nodes - num_available_nodes))
    index=0
    while [ $missing_nodes -gt 0 ]; do
        nodes+=(${nodes[((index % num_available_nodes))]})
        ((missing_nodes--))
        ((index++))
    done
fi

# Store name of active nodes on disk for clean up script
printf "%s\n" "${nodes[@]}" | sort -u >>"$active_nodes_file"

# Find available port and ID for each chord node
declare -A seen_ids
for i in "${!nodes[@]}"; do
    find_available_port_and_id "$i"
done
echo "Done."
echo ""

# Start chord nodes
echo "Starting nodes..."
printf "    %-15s %s\n" "Address:" "ID:"
for i in "${!nodes[@]}"; do
    start_chord_node "$i"
done
echo "Done."
echo ""

echo "Waiting for nodes to start..."
sleep 6
echo "Done."
echo ""

# Check that nodes are running
echo "Checking if nodes are responsive..."
boot_node="${nodes[0]}:${ports[0]}"
for i in "${!nodes[@]}"; do
    while true; do
        node="${nodes[$i]}"
        port="${ports[$i]}"
        node_endpoint="${endpoints[$i]}"
        id="${ids[$i]}"

        # Check the status of the node
        if ! curl --max-time 5 "$node:$port/status" >/dev/null 2>&1; then
            echo "    Error: Failed to get status from $node:$port"
            echo "    Trying to restart node..."

            # If the node failed, try and start it again with a new port
            unset seen_ids[${ids[$i]}]
            find_available_port_and_id "$i"
            start_chord_node "$i"
            sleep 6
            continue
        fi
        break
    done
done
echo "Done."
echo ""

# Join all nodes, wait for ring to stabilize
echo "Joining nodes. Waiting for ring to stablilize..."
python3 ./tests/join.py "${num_nodes}" "${endpoints[@]}"
echo "Done."
echo ""

for i in "${!nodes[@]}"; do
    node="${nodes[$i]}"
    port="${ports[$i]}"
    printf "${node}:$((port)) "
done
echo ""
