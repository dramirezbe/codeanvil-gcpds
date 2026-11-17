#!/usr/bin/env python3
"""Deterministic topological sort and cycle detection for module slicing.

Takes a module dependency list (from SDD §1.4 cards) and produces:
1. Topological sort (compile order within a slice)
2. Cycle detection (DAG verification)
3. Slice boundaries (HAL-first, then DSP-then-Decision, etc.)
"""

import sys
from collections import defaultdict, deque
from typing import NamedTuple, Tuple, Set, List


class Module(NamedTuple):
    """A module from SDD §1.4."""
    module_id: str  # e.g., "acq", "estimator"
    subsystem: str  # e.g., "SUB-001"
    layer: str  # e.g., "HAL", "DSP", "Decision"
    depends_on: List[str]  # contract IDs this module consumes
    provides: List[str]  # contract IDs this module produces
    hw_dependency: bool  # true if hw_dependency: true
    required_vl: str  # "VL-0", "VL-1", or "VL-2"


def find_cycles(modules: dict[str, Module]) -> List[List[str]]:
    """Find all cycles in the module dependency graph."""
    graph = {m: set() for m in modules}
    for module_id, module in modules.items():
        for dep in module.depends_on:
            # Find which module produces this contract
            for other_id, other in modules.items():
                if dep in other.provides:
                    graph[module_id].add(other_id)
                    break

    visited = set()
    rec_stack = set()
    cycles = []

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                if dfs(neighbor, path):
                    return True
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
                return True

        path.pop()
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles


def topological_sort(modules: dict[str, Module]) -> Tuple[List[str], bool]:
    """
    Topological sort of modules by contract dependencies.
    Returns (sorted_list, has_cycle). If has_cycle, sorted_list is incomplete.
    """
    if find_cycles(modules):
        return [], True

    graph = defaultdict(set)
    in_degree = defaultdict(int)
    module_ids = set(modules.keys())

    # Build graph: edge from module A to module B if A.provides contains something B.depends_on
    for module_id, module in modules.items():
        in_degree[module_id] = 0

    for module_id, module in modules.items():
        for contract in module.depends_on:
            # Find producer
            for other_id, other in modules.items():
                if contract in other.provides and other_id != module_id:
                    graph[other_id].add(module_id)
                    in_degree[module_id] += 1
                    break

    queue = deque([m for m in module_ids if in_degree[m] == 0])
    sorted_list = []

    while queue:
        node = queue.popleft()
        sorted_list.append(node)

        for neighbor in sorted(graph[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return sorted_list, len(sorted_list) < len(module_ids)


def slice_by_layer(modules: dict[str, Module], sorted_order: List[str]) -> dict[str, List[str]]:
    """
    Group modules into slices by layer: HAL-first, then DSP-then-Decision, etc.
    Respects the sorted_order to maintain dependency order within slices.
    """
    layer_order = ["HAL", "DSP", "Decision", "Output", "Control", "other"]
    slices = {}
    seen = set()

    for layer in layer_order:
        slice_modules = []
        for module_id in sorted_order:
            if module_id not in seen and modules[module_id].layer == layer:
                # Only add if all dependencies are satisfied (in seen)
                deps_satisfied = True
                for contract in modules[module_id].depends_on:
                    producer_found = False
                    for other_id in seen:
                        if contract in modules[other_id].provides:
                            producer_found = True
                            break
                    if not producer_found and contract not in [
                        c for m in [modules[s] for s in seen] for c in m.provides
                    ]:
                        # TODO: handle cross-slice mocking
                        pass
                if deps_satisfied:
                    slice_modules.append(module_id)
                    seen.add(module_id)

        if slice_modules:
            slice_name = f"slice-{len(slices)+1:02d}-{layer.lower()}"
            slices[slice_name] = slice_modules

    return slices


def main(argv=None):
    """Entry point: `codeanvil python slice_backlog.py --verify BACKLOG.md` or similar."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Topological sort and slice planning for modules."
    )
    parser.add_argument(
        "--verify",
        metavar="BACKLOG.md",
        help="Verify BACKLOG.md for cycles and produce sorted order",
    )
    parser.add_argument(
        "--sort-only",
        action="store_true",
        help="Output only the sorted module list (one per line)",
    )

    args = parser.parse_args(argv)

    if args.verify:
        # TODO: Parse BACKLOG.md, extract modules, check cycles, produce PLAN.md slice boundaries
        print(f"Verification not yet implemented for {args.verify}")
        return 1
    else:
        print("Usage: python slice_backlog.py --verify BACKLOG.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
