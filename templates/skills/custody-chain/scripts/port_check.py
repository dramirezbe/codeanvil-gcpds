#!/usr/bin/env python3
"""Port Implementation Injections: verify runtime interfaces (ports) have bound,
concrete, conforming implementations.

  port_check.py --root . --bindings ports.json            # static (AST, no code executed)
  port_check.py --root . --bindings ports.json --import   # also imports + inspects at runtime

ports.json:
  {"ports":[{"id":"PORT-001","interface":"app.ports:ClockPort",
             "binding":"app.adapters:SystemClock","required":true,"scope":"runtime"}]}

Exit codes: 0 PASS, 1 FAIL, 2 usage/IO error.
"""
import argparse, ast, importlib, inspect, json, sys
from pathlib import Path
from _common import report


def _module_file(root: Path, dotted: str):
    base = root / dotted.replace(".", "/")
    for c in (base.with_suffix(".py"), base / "__init__.py"):
        if c.is_file():
            return c
    return None


def _split(ref):
    mod, sep, cls = (ref or "").partition(":")
    return (mod, cls) if sep and mod and cls else (None, None)


def _static_class(root, ref):
    mod, cls = _split(ref)
    if not mod:
        return None, "malformed reference (expected 'pkg.mod:Class')"
    path = _module_file(root, mod)
    if not path:
        return None, f"module file not found for {mod}"
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            methods, abstract = set(), set()
            for n in node.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(n.name)
                    if any("abstractmethod" in ast.unparse(d) for d in n.decorator_list):
                        abstract.add(n.name)
            bases = [ast.unparse(b).split(".")[-1] for b in node.bases]
            return {"name": cls, "methods": methods, "abstract": abstract, "bases": bases}, None
    return None, f"class {cls} not found in {path.relative_to(root)}"


def check_static(root, p):
    iface, e1 = _static_class(root, p.get("interface"))
    impl, e2 = _static_class(root, p.get("binding")) if p.get("binding") else (None, None)
    if e1:
        return "INVALID", f"interface: {e1}"
    if not p.get("binding"):
        return "UNBOUND", "no binding declared"
    if e2:
        return "UNBOUND", f"binding: {e2}"
    if impl["abstract"]:
        return "INVALID", f"binding has abstract methods: {sorted(impl['abstract'])}"
    needed = {m for m in iface["methods"] if not m.startswith("_")}
    missing = needed - impl["methods"]
    if not missing:
        return "BOUND", "all interface methods defined on binding"
    if iface["name"] in impl["bases"]:
        return "BOUND", "inherits interface; methods resolved by inheritance"
    if impl["bases"]:
        return "UNVERIFIED", f"missing {sorted(missing)} locally; bases {impl['bases']} not resolved statically"
    return "INVALID", f"binding lacks methods: {sorted(missing)}"


def _load(ref):
    mod, cls = _split(ref)
    return getattr(importlib.import_module(mod), cls)


def check_import(p):
    try:
        iface = _load(p["interface"])
        if not p.get("binding"):
            return "UNBOUND", "no binding declared"
        impl = _load(p["binding"])
    except Exception as e:  # noqa: BLE001 - report any import failure
        return "UNBOUND", f"import failed: {type(e).__name__}: {e}"
    if not inspect.isclass(impl):
        return "INVALID", "binding is not a class"
    if inspect.isabstract(impl):
        return "INVALID", f"binding is abstract: {sorted(impl.__abstractmethods__)}"
    bad = []
    for name, fn in inspect.getmembers(iface, inspect.isfunction):
        if name.startswith("_"):
            continue
        got = getattr(impl, name, None)
        if not callable(got):
            bad.append(f"{name}: missing"); continue
        try:
            a, b = inspect.signature(fn), inspect.signature(got)
            if len(a.parameters) != len(b.parameters):
                bad.append(f"{name}: arity {len(b.parameters)} != {len(a.parameters)}")
        except (TypeError, ValueError):
            pass
    return ("INVALID", "; ".join(bad)) if bad else ("BOUND", "runtime conformance ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--root", default="."); ap.add_argument("--bindings", required=True)
    ap.add_argument("--import", dest="do_import", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    try:
        ports = json.loads(Path(a.bindings).read_text())["ports"]
    except (OSError, KeyError, json.JSONDecodeError) as e:
        print(f"cannot read bindings: {e}", file=sys.stderr); sys.exit(2)
    if a.do_import:
        sys.path.insert(0, str(root))
    f, results, ids, slots = [], [], set(), {}
    for p in ports:
        pid = p.get("id", "<no-id>")
        if pid in ids:
            f.append({"port": pid, "code": "DUPLICATE_PORT_ID", "severity": "critical"})
        ids.add(pid)
        st, why = check_import(p) if a.do_import else check_static(root, p)
        required = p.get("required", True)
        results.append({"port": pid, "interface": p.get("interface"), "binding": p.get("binding"),
                        "status": st, "detail": why, "required": required})
        slot = (p.get("interface"), p.get("scope", "runtime"))
        if p.get("binding"):
            slots.setdefault(slot, []).append(pid)
        if st in ("UNBOUND", "INVALID") and required:
            f.append({"port": pid, "code": f"PORT_{st}", "severity": "critical", "detail": why})
        elif st != "BOUND":
            f.append({"port": pid, "code": f"PORT_{st}", "severity": "warning", "detail": why})
    for (iface, scope), who in slots.items():
        if len(who) > 1:
            f.append({"code": "AMBIGUOUS_BINDING", "severity": "critical",
                      "detail": f"{iface} ({scope}) bound by multiple ports: {who}"})
    failed = any(x["severity"] == "critical" for x in f)
    print(json.dumps(report("FAIL" if failed else "PASS", f, mode="import" if a.do_import else "static",
                            ports=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
