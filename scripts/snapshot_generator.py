# HelixGate Snapshot Generator
# Deterministic Registry Snapshot Engine
# Aligned with Compile Validator Path Structure

import json
import hashlib
import os

BASE_PATH = "03_canonical_registry"

REGISTRY_FILES = {
    "registry": f"{BASE_PATH}/global_registry.json",
    "acu_index": f"{BASE_PATH}/acu_index.json",
    "dependency_graph": f"{BASE_PATH}/dependency_graph.json",
    "manifest": f"{BASE_PATH}/version_manifest.json"
}

SNAPSHOT_PATH = "snapshots/current_snapshot.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_registry_data():
    data = {}
    for key in sorted(REGISTRY_FILES.keys()):
        data[key] = load_json(REGISTRY_FILES[key])
    return data


def compute_snapshot_hash(data):
    combined = ""
    for key in sorted(data.keys()):
        combined += canonical_json(data[key])
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def main():
    data = load_registry_data()
    snapshot_hash = compute_snapshot_hash(data)

    manifest = data["manifest"]

    snapshot = {
        "snapshot_hash": snapshot_hash,
        "operating_mode": manifest.get("operating_mode"),
        "registry_hash": manifest.get("registry_hash")
    }

    os.makedirs("snapshots", exist_ok=True)

    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4)

    print("Snapshot generated.")
    print("SHA256:", snapshot_hash)


if __name__ == "__main__":
    main()
