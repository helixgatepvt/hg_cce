# HelixGate Snapshot Generator
# Deterministic Registry Snapshot Engine
# Governance-Hardened & Drift-Locked Production Version (Non-Circular Hash)

import json
import hashlib
import os
import sys

BASE_PATH = "03_canonical_registry"

# Files that define canonical registry state (DO NOT include manifest)
CANONICAL_FILES = {
    "registry": f"{BASE_PATH}/global_registry.json",
    "acu_index": f"{BASE_PATH}/acu_index.json",
    "dependency_graph": f"{BASE_PATH}/dependency_graph.json",
}

MANIFEST_PATH = f"{BASE_PATH}/version_manifest.json"
SNAPSHOT_PATH = "snapshots/current_snapshot.json"


def load_json(path):
    if not os.path.exists(path):
        print(f"Missing required file: {path}")
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


def load_canonical_data():
    return {
        "registry": load_json(CANONICAL_FILES["registry"]),
        "acu_index": load_json(CANONICAL_FILES["acu_index"]),
        "dependency_graph": load_json(CANONICAL_FILES["dependency_graph"]),
    }


def compute_registry_hash(data):
    # Explicit deterministic order — must match compile_validator
    combined = (
        canonical_json(data["registry"]) +
        canonical_json(data["acu_index"]) +
        canonical_json(data["dependency_graph"])
    )
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def main():
    canonical_data = load_canonical_data()
    computed_hash = compute_registry_hash(canonical_data)

    manifest = load_json(MANIFEST_PATH)

    registry_version = manifest.get("registry_version")
    registry_hash = manifest.get("registry_hash")
    operating_mode = manifest.get("operating_mode")

    # Hard fail if manifest missing required values
    if not registry_hash or not registry_version:
        print("Manifest missing registry_version or registry_hash. Aborting.")
        sys.exit(1)

    # Enforce registry hash consistency (non-circular)
    if computed_hash != registry_hash:
        print("Registry hash does not match manifest registry_hash. Aborting.")
        print("Computed:", computed_hash)
        print("Manifest:", registry_hash)
        sys.exit(1)

    snapshot = {
        "registry_hash": computed_hash,
        "operating_mode": operating_mode,
    }

    os.makedirs("snapshots", exist_ok=True)

    # Rolling snapshot
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4)

    # Version-bound archival snapshot (immutable)
    versioned_path = f"snapshots/registry_{registry_version}.json"

    if os.path.exists(versioned_path):
        print(f"Snapshot for version {registry_version} already exists. Immutable lock enforced.")
        sys.exit(1)

    archival_snapshot = {
        "registry_version": registry_version,
        "registry_hash": computed_hash
    }

    with open(versioned_path, "w", encoding="utf-8") as f:
        json.dump(archival_snapshot, f, indent=4)

    print("Snapshot generated successfully.")
    print("Registry SHA256:", computed_hash)


if __name__ == "__main__":
    main()
