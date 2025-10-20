#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <num_chord_nodes> [m]"
    exit 1
fi

num_nodes=$1
m=${2:-6}
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
successor_endpoints=()
successor_ids=()

# Get available nodes
readarray -t all_nodes < <(/share/ifi/available-nodes.sh)
num_available_nodes=${#all_nodes[@]}

if [ $num_available_nodes -eq 0 ]; then
    echo "No nodes available."
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
printf "%s\n" "${nodes[@]}" | sort -u >> "$active_nodes_file"

# Create ids for each of the nodes by hashing node:port sha1
declare -A seen_ids
for i in "${!nodes[@]}"; do
    while true; do
        port=$(shuf -i 49152-65535 -n1)
        endpoint="${nodes[i]}:${port}"
        hash=$(echo -n "$endpoint" | sha1sum | cut -d' ' -f1)
        id=$(python3 -c "print(int('$hash', 16) % (2**$m))")

        # Check if this ID has been seen before
        if [[ -z "${seen_ids[$id]}" ]]; then
            seen_ids[$id]=1
            ports+=("$port")
            endpoints+=("$endpoint")
            hashes+=("$hash")
            ids+=("$id")
            break
        else
            echo "ID collision detected ($id), regenerating port for ${nodes[i]}..."
        fi
    done
done

# Get the successor ids of the nodes
mapfile -t successor_ids < <(python3 get_successor_id_order.py $m ${endpoints[@]})

# Use successor ids to find successor endpoints
for i in "${!successor_ids[@]}"; do
    successor_id="${successor_ids[$i]}"
    for j in "${!ids[@]}"; do
        if [ "${ids[$j]}" -eq "$successor_id" ]; then
            successor_endpoints+=("${endpoints[$j]}")
            break
        fi
    done
done

# Start processes
for i in "${!nodes[@]}"; do
    node="${nodes[$i]}"
    node_endpoint="${endpoints[$i]}"
    id="${ids[$i]}"
    successor_id="${successor_ids[$i]}"

    echo "Starting process on $node_endpoint $id with successor $successor_endpoint $successor_id"

    # Copy target to node (one for each proccess)
    # and start the proccess
    temp_dir="/tmp/chord-$$-$i"
    {
        ssh "$USER@$node" "mkdir -p $temp_dir" && \
        scp -r "$target" "$USER@$node:$temp_dir/" && \
        ssh "$USER@$node" "cd $temp_dir/src/ && pip3 install -r requirements.txt && python3 -u main.py $node_endpoint $m"
    } > "${stdout_dir}/${node}-${i}.log" 2>&1 &
done

echo "Waiting for nodes to start..."
sleep 6

# Set up successors
for i in "${!nodes[@]}"; do
    node="${nodes[$i]}"
    port="${ports[$i]}"
    successor_endpoint="${successor_endpoints[$i]}"
    echo "Sending $node:$port successor $successor_endpoint"
    curl -X PUT -d "$successor_endpoint" "$node:$port/successor"
    echo "Completed node $node"
done

# Set up finger tables
for i in "${!nodes[@]}"; do
    node="${nodes[$i]}"
    port="${ports[$i]}"
    echo "Fixing fingers for node $node:$port..."
    curl -X PUT "$node:$((port))/fix_fingers"
    echo "Completed node $node"
done

echo ""
for i in "${!nodes[@]}"; do
    node="${nodes[$i]}"
    port="${ports[$i]}"
    printf "${node}:$((port)) "
done
echo ""
