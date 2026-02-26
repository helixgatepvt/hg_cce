
import json
import hashlib
import os

REGISTRY_FILES = [
    "global_registry.json",
    "acu_index.json",
    "dependency_graph.json",
    "version_manifest.json"
]

SNAPSHOT_PATH = "snapshots/current_snapshot.json"


def load_registry_data():
    combined = {}
    for file in REGISTRY_FILES:
        with open(file, "r") as f:
            combined[file] = json.load(f)
    return combined


def compute_hash(data):
    serialized = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(serialized).hexdigest()


def main():
    data = load_registry_data()
    snapshot_hash = compute_hash(data)

    snapshot = {
        "snapshot_hash": snapshot_hash,
        "files_included": REGISTRY_FILES,
        "model_version": data["version_manifest.json"]["model_version"]
    }

    os.makedirs("snapshots", exist_ok=True)

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=4)

    print("Snapshot generated.")
    print("SHA256:", snapshot_hash)


if __name__ == "__main__":
    main()
