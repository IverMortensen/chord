#!/bin/sh

HOSTS="$(shuf /share/compute-nodes.txt)"
EXCLUDE="$(tr '\n' ' ' </share/exclude-nodes.txt)"

for H in $EXCLUDE; do
    HOSTS=$(echo $HOSTS | sed -e "s/${H}//")
done

# Find all nodes with 1min load < 0.4
for H in $HOSTS; do
    ssh -o ConnectTimeout=1 -o ConnectionAttempts=1 -x $H \
        "cat /proc/loadavg /proc/sys/kernel/hostname | tr '\n'  ' ' | awk '\$1+0 < 0.4 {printf \"%s %s\n\", \$1, \$6}'" 2>/dev/null &
done | sort -n | awk '{print $2}' | sed 's/.ifi.uit.no//'

wait
