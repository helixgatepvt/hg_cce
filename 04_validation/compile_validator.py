# HelixGate Compile Validator
# Phase 2 — Compile-Time Constitutional Enforcement Engine
# Phase 3 — Freeze Mode Structural Mutation Firewall
# Deterministic | No Auto-Correction | Structural Mode Locked

import json
import hashlib
import sys
import subprocess
from collections import deque

BASE_PATH = "."

FILES = {
    "registry": f"{BASE_PATH}/03_canonical_registry/global_registry.json",
    "acu_index": f"{BASE_PATH}/03_canonical_registry/acu_index.json",
    "dependency_graph": f"{BASE_PATH}/03_canonical_registry/dependency_graph.json",
    "manifest": f"{BASE_PATH}/03_canonical_registry/version_manifest.json"
}


# ---------------------------
# Utility
# ---------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_registry_hash(registry, acu_index, dependency_graph):
    combined = (
        canonical_json(registry) +
        canonical_json(acu_index) +
        canonical_json(dependency_graph)
    )
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ---------------------------
# Phase 3 — Freeze Enforcement
# ---------------------------

def enforce_freeze_mode(manifest):
    """
    If freeze_mode is true:
    - Any modification to canonical registry files is forbidden.
    - Any modification to manifest structural fields is forbidden.
    """

    if not manifest.get("freeze_mode", False):
        return

    protected_files = [
        "03_canonical_registry/global_registry.json",
        "03_canonical_registry/acu_index.json",
        "03_canonical_registry/dependency_graph.json",
        "03_canonical_registry/version_manifest.json",
    ]

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main"],
            capture_output=True,
            text=True,
            check=False
        )
        changed_files = result.stdout.strip().split("\n")
    except Exception:
        print(json.dumps({
            "status": "INVALID",
            "error": "Freeze mode: unable to inspect git diff."
        }))
        sys.exit(1)

    for file in protected_files:
        if file in changed_files:
            print(json.dumps({
                "status": "INVALID",
                "error": f"Freeze mode active: modification detected in {file}."
            }))
            sys.exit(1)


# ---------------------------
# Structural Validation
# ---------------------------

def validate_acu_completeness(registry, acu_index):
    registry_ids = {acu["acu_id"] for acu in registry["ac_units"]}
    index_ids = set(acu_index.keys())

    if registry_ids != index_ids:
        return False, "ACU ID mismatch between registry and index."

    if len(registry_ids) != registry.get("total_acu_count"):
        return False, "ACU count mismatch in registry metadata."

    return True, None


def validate_dag(dependency_graph):
    nodes = set(dependency_graph["nodes"])
    edges = dependency_graph["edges"]

    for edge in edges:
        if edge["from"] not in nodes or edge["to"] not in nodes:
            return False, "Dependency graph contains undefined nodes."

    in_degree = {node: 0 for node in nodes}
    adj = {node: [] for node in nodes}

    for edge in edges:
        adj[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    queue = deque([node for node in nodes if in_degree[node] == 0])
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(nodes):
        return False, "Dependency graph contains a cycle."

    return True, None


def validate_operating_mode(manifest, registry):
    if manifest["operating_mode"] != "STRUCTURAL_ONLY":
        return False, "Operating mode mismatch in manifest."
    if registry["operating_mode"] != "STRUCTURAL_ONLY":
        return False, "Operating mode mismatch in registry."
    return True, None


# ---------------------------
# Main
# ---------------------------

def main():
    try:
        registry = load_json(FILES["registry"])
        acu_index = load_json(FILES["acu_index"])
        dependency_graph = load_json(FILES["dependency_graph"])
        manifest = load_json(FILES["manifest"])
    except Exception as e:
        print(json.dumps({"status": "INVALID", "error": f"File load failure: {str(e)}"}))
        sys.exit(1)

    # Phase 3 Freeze Enforcement
    enforce_freeze_mode(manifest)

    valid, error = validate_acu_completeness(registry, acu_index)
    if not valid:
        print(json.dumps({"status": "INVALID", "error": error}))
        sys.exit(1)

    valid, error = validate_dag(dependency_graph)
    if not valid:
        print(json.dumps({"status": "INVALID", "error": error}))
        sys.exit(1)

    valid, error = validate_operating_mode(manifest, registry)
    if not valid:
        print(json.dumps({"status": "INVALID", "error": error}))
        sys.exit(1)

    computed_hash = compute_registry_hash(registry, acu_index, dependency_graph)

    if computed_hash != manifest["registry_hash"]:
        print(json.dumps({
            "status": "INVALID",
            "error": "Registry hash mismatch.",
            "computed_hash": computed_hash,
            "manifest_hash": manifest["registry_hash"]
        }))
        sys.exit(1)

    print(json.dumps({"status": "VALID"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
