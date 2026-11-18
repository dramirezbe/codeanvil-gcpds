#!/usr/bin/env python3
"""Read SDD module cards and emit deterministic Kahn levels (Slice 0 is infrastructure)."""
import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Module(NamedTuple):
    module_id: str
    subsystem: str
    layer: str
    depends_on: list[str]
    provides: list[str]
    hw_dependency: bool
    required_vl: str
    traced_reqs: list[str] = []


def items(value):
    value = re.sub(r"<!--.*?-->", "", value).strip().strip("[]`")
    return [] if value.lower() in {"", "none", "—", "-"} else [v.strip().strip("`'\"") for v in value.split(",")]


def read_modules(text):
    modules = {}
    for block in re.split(r"^#{3,6} ", text, flags=re.M):
        fields = dict((key.strip().strip("`"), value.strip()) for key, value in
                      re.findall(r"^\|\s*([a-z_]+)\s*\|([^|]*)\|", block, re.M))
        if "module_id" not in fields:
            continue
        required = {"module_id", "subsystem_id", "layer", "depends_on", "provides", "hw_dependency", "required_vl", "traced_reqs"}
        if required - fields.keys():
            raise ValueError(f"missing module fields: {sorted(required - fields.keys())}")
        module = Module(fields["module_id"].strip("`"), fields["subsystem_id"].strip("`"),
                        fields["layer"].strip("`"), items(fields["depends_on"]), items(fields["provides"]),
                        fields["hw_dependency"].lower() == "true", fields["required_vl"].strip("`"), items(fields["traced_reqs"]))
        key = f"{module.subsystem}/{module.module_id}"
        if key in modules or not module.traced_reqs:
            raise ValueError(f"duplicate module or empty traced_reqs: {key}")
        modules[key] = module
    if not modules:
        raise ValueError("no module cards found")
    return modules


def levels(modules):
    remaining = {}
    for key, module in modules.items():
        deps = set()
        for dep in module.depends_on:
            # Optional edge annotation carries a contract, identity remains the module.
            dep = dep.split(" (")[0]
            if dep in modules:
                target = dep
            else:
                candidates = [k for k, m in modules.items() if m.module_id == dep and m.subsystem == module.subsystem]
                if len(candidates) != 1:
                    raise ValueError(f"unknown dependency {dep} in {key}")
                target = candidates[0]
            deps.add(target)
        remaining[key] = deps
    result = []
    while remaining:
        ready = sorted(key for key, deps in remaining.items() if not deps)
        if not ready:
            raise ValueError("dependency cycle: " + ", ".join(sorted(remaining)))
        result.append(ready)
        remaining = {k: deps - set(ready) for k, deps in remaining.items() if k not in ready}
    return result


def topological_sort(modules):
    try:
        return [key for level in levels(modules) for key in level], False
    except ValueError:
        return [], True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdd", nargs="?", type=Path)
    parser.add_argument("--verify", type=Path, help="Read SDD module cards (alias for positional SDD)")
    parser.add_argument("--sort-only", action="store_true")
    args = parser.parse_args(argv)
    path = args.sdd or args.verify
    if path is None:
        parser.error("an SDD file is required")
    try:
        modules = read_modules(path.read_text(encoding="utf-8"))
        slices = levels(modules)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.sort_only:
        print("\n".join(key for group in slices for key in group))
    else:
        print("| Slice | Module | Depends on | Required VL | Plan | State |")
        print("|-------|--------|------------|-------------|------|-------|")
        for index, group in enumerate(slices, 1):
            for key in group:
                m = modules[key]
                print(f"| {index} | {key} | {', '.join(m.depends_on) or 'none'} | {m.required_vl} | .codeanvil/plans/{key}/PLAN.md | planned |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
