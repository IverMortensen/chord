import sys
import hashlib

def main():
    m = int(sys.argv[1])
    endpoints = sys.argv[2:]

    # Calculate IDs
    ids = []
    for node in endpoints:
        hash = hashlib.sha1(node.encode()).hexdigest()
        id = int(hash, 16) % (2**m)
        ids.append(id)

    ids_sorted = sorted(set(ids))

    # Create mapping between ids and successor ids
    succsessor_ids = {}
    for i, id_val in enumerate(ids_sorted):
        next_id = ids_sorted[(i + 1) % len(ids_sorted)]
        succsessor_ids[id_val] = next_id

    # Return successor ids in order of ids (same order as nodes in bash script)
    for id_val in ids:
        print(succsessor_ids[id_val])

if __name__ == "__main__":
    main()
