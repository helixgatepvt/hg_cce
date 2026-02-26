# HelixGate Snapshot Generator
# Deterministic Registry Snapshot Engine
# Governance-Hardened & Drift-Locked Production Version

import json
import hashlib
import os
import sys

BASE_PATH = "03_canonical_registry"

REGISTRY_FILES = {
    "registry": f"{BASE_PATH}/global_registry.json",
    "acu_index": f"{BASE_PATH}/acu_index.json",
    "dependency_graph": f"{BASE_PATH}/dependency_graph.json",
    "manifest": f"{BASE_PATH}/version_manifest.json"
}

SNAPSHOT_PATH = "snapshots/current_snapshot.json"


def load_json(path):
    if not os.path.exists(path):
        print(f"Missing required registry file: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def canonical_json(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )


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

    registry_version = manifest.get("registry_version")
    registry_hash = manifest.get("registry_hash")
    operating_mode = manifest.get("operating_mode")

    # Hard fail if manifest missing required values
    if not registry_hash or not registry_version:
        print("Manifest missing registry_version or registry_hash. Aborting.")
        sys.exit(1)

    # Enforce registry hash consistency
    if snapshot_hash != registry_hash:
        print("Snapshot hash does not match manifest registry_hash. Aborting.")
        sys.exit(1)

    snapshot = {
        "snapshot_hash": snapshot_hash,
        "operating_mode": operating_mode,
        "registry_hash": registry_hash
    }

    os.makedirs("snapshots", exist_ok=True)

    # Current rolling snapshot (non-immutable)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4)

    # Version-bound archival snapshot (immutable)
    versioned_path = f"snapshots/registry_{registry_version}.json"

    if os.path.exists(versioned_path):
        print(f"Snapshot for version {registry_version} already exists. Immutable lock enforced.")
        sys.exit(1)

    archival_snapshot = {
        "registry_version": registry_version,
        "registry_hash": registry_hash,
        "snapshot_hash": snapshot_hash
    }

    with open(versioned_path, "w", encoding="utf-8") as f:
        json.dump(archival_snapshot, f, indent=4)

    print("Snapshot generated successfully.")
    print("SHA256:", snapshot_hash)


if __name__ == "__main__":
    main()
