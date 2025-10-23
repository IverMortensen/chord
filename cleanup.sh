#!/bin/bash
node_file="active_nodes.txt"
stdout_dir="stdout"
log_dir="$HOME/imo059-chord-logs"
temp_dir=$(mktemp -d)

if [ ! -f "$node_file" ]; then
    echo "No active nodes file found: $node_file"
    exit 1
fi

echo "killing processes..."

# Start all kill commands in parallel
index=0
while read -r node; do
    if [ -n "$node" ]; then
        {
            if ssh -n "$USER"@"$node" "pkill python" 2>/dev/null; then
                echo "Killing chord node on $node... SUCCESS"
            else
                echo "Killing chord node on $node... No process found or failed"
            fi
        } >"$temp_dir/output_$index" &
        ((index++))
    fi
done <"$node_file"

# Wait for them to finish
wait

# Print the results
for ((i = 0; i < index; i++)); do
    if [ -f "$temp_dir/output_$i" ]; then
        cat "$temp_dir/output_$i"
    fi
done

# Cleanup
rm -rf "$temp_dir"
rm -f "$node_file"
rm -r "$stdout_dir"
rm -r "$log_dir"
echo "Done."
