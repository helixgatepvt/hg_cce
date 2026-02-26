# HelixGate Snapshot Generator
# Deterministic Registry Snapshot Engine
# Governance-Hardened & Drift-Locked Production Version
# Non-Circular Hash Model
# Explicit Hash Order (Must Match compile_validator)

import json
import hashlib
import os
import sys

BASE_PATH = "03_canonical_registry"

# Canonical registry state files (EXCLUDES manifest by design)
REGISTRY_PATH = f"{BASE_PATH}/global_registry.json"
ACU_INDEX_PATH = f"{BASE_PATH}/acu_index.json"
DEPENDENCY_GRAPH_PATH = f"{BASE_PATH}/dependency_graph.json"

MANIFEST_PATH = f"{BASE_PATH}/version_manifest.json"
SNAPSHOT_PATH = "snapshots/current_snapshot.json"


# ---------------------------
# Utility Functions
# ---------------------------

def load_json(path):
    if not os.path.exists(path):
        print(f"Missing required file: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def canonical_json(obj):
    """
    Deterministic JSON serialization.
    Must match compile_validator exactly.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )


# ---------------------------
# Canonical Hash Computation
# ---------------------------

def compute_registry_hash(registry, acu_index, dependency_graph):
    """
    Explicit deterministic ordering:
    registry → acu_index → dependency_graph

    DO NOT change ordering.
    Must remain identical to compile_validator.
    """

    combined = (
        canonical_json(registry) +
        canonical_json(acu_index) +
        canonical_json(dependency_graph)
    )

    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ---------------------------
# Main Execution
# ---------------------------

def main():
    # Load canonical registry state
    registry = load_json(REGISTRY_PATH)
    acu_index = load_json(ACU_INDEX_PATH)
    dependency_graph = load_json(DEPENDENCY_GRAPH_PATH)

    computed_hash = compute_registry_hash(
        registry,
        acu_index,
        dependency_graph
    )

    manifest = load_json(MANIFEST_PATH)

    registry_version = manifest.get("registry_version")
    manifest_hash = manifest.get("registry_hash")
    operating_mode = manifest.get("operating_mode")

    # Mandatory manifest validation
    if not registry_version or not manifest_hash:
        print("Manifest missing registry_version or registry_hash. Aborting.")
        sys.exit(1)

    # Enforce hash consistency (non-circular model)
    if computed_hash != manifest_hash:
        print("Registry hash does not match manifest registry_hash. Aborting.")
        print("Computed:", computed_hash)
        print("Manifest:", manifest_hash)
        sys.exit(1)

    # Prepare snapshot payload
    snapshot = {
        "registry_hash": computed_hash,
        "operating_mode": operating_mode,
    }

    os.makedirs("snapshots", exist_ok=True)

    # Rolling snapshot (overwrites safely)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4)

    # Version-bound archival snapshot (immutable by design)
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
