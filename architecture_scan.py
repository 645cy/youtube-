"""TubeFactory OCP — Architecture Health Scanner."""
from __future__ import annotations

import ast
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
APPS_API = PROJECT_ROOT / "apps" / "api"
PACKAGES = PROJECT_ROOT / "packages"
TESTS = PROJECT_ROOT / "tests"


def collect_python_files(root: Path) -> list[Path]:
    return list(root.rglob("*.py"))


def parse_file(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return None


# ── 1. Circular Import Detection ──
def build_import_graph(files: list[Path]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    module_map: dict[str, Path] = {}

    for f in files:
        rel = f.relative_to(PROJECT_ROOT)
        mod = str(rel.with_suffix("")).replace(os.sep, ".")
        module_map[mod] = f

    for f in files:
        rel = f.relative_to(PROJECT_ROOT)
        mod = str(rel.with_suffix("")).replace(os.sep, ".")
        tree = parse_file(f)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    graph[mod].add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    graph[mod].add(alias.name)
    return dict(graph)


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited = set()
    stack = []

    def dfs(node: str) -> None:
        if node in stack:
            idx = stack.index(node)
            cycles.append(stack[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        stack.append(node)
        for neighbor in graph.get(node, set()):
            dfs(neighbor)
        stack.pop()

    for node in graph:
        dfs(node)
    # Deduplicate
    seen = set()
    uniq = []
    for c in cycles:
        key = tuple(sorted(set(c)))
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


# ── 2. God Functions / Complexity ──
def find_long_functions(files: list[Path], threshold: int = 50) -> list[dict[str, Any]]:
    results = []
    for f in files:
        tree = parse_file(f)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if lines > threshold:
                    results.append({
                        "file": str(f.relative_to(PROJECT_ROOT)),
                        "function": node.name,
                        "lines": lines,
                    })
    return sorted(results, key=lambda x: x["lines"], reverse=True)


# ── 3. Missing Type Annotations ──
def find_missing_types(files: list[Path]) -> list[dict[str, Any]]:
    results = []
    for f in files:
        tree = parse_file(f)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                missing = []
                if node.returns is None and node.name != "__init__":
                    missing.append("return")
                for arg in node.args.args + node.args.kwonlyargs:
                    if arg.annotation is None and arg.arg not in ("self", "cls"):
                        missing.append(f"arg:{arg.arg}")
                if missing:
                    results.append({
                        "file": str(f.relative_to(PROJECT_ROOT)),
                        "function": node.name,
                        "missing": missing,
                    })
    return results


# ── 4. Bare Exception Detection ──
def find_bare_exceptions(files: list[Path]) -> list[dict[str, Any]]:
    results = []
    for f in files:
        tree = parse_file(f)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    results.append({
                        "file": str(f.relative_to(PROJECT_ROOT)),
                        "line": node.lineno,
                        "type": "bare except:",
                    })
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    # Check if body just has pass or bare log
                    body = ast.unparse(node.body[0]) if node.body else ""
                    if "pass" in body or body.strip() == "":
                        results.append({
                            "file": str(f.relative_to(PROJECT_ROOT)),
                            "line": node.lineno,
                            "type": f"except Exception: {body[:40]}",
                        })
    return results


# ── 5. Hardcoded Secrets Detection ──
def find_hardcoded_secrets(files: list[Path]) -> list[dict[str, Any]]:
    results = []
    keywords = ["password", "secret", "token", "api_key", "apikey", "private_key"]
    for f in files:
        if "test" in f.name.lower():
            continue
        text = f.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for kw in keywords:
                if kw in low and "=" in line:
                    lhs, rhs = line.split("=", 1)
                    if not any(secret_kw in lhs.lower() for secret_kw in keywords):
                        continue
                    # CRG: Only inspect assignments to secret-like names; message strings can mention API keys safely.
                    # Heuristic: skip env var reads and settings references
                    if "os.environ" in line or "settings." in line or "getenv" in line:
                        continue
                    if ": str | None = None" in line or "developerKey=" in line or "page_token:" in line:
                        continue
                    # CRG: Scanner should flag literal secrets, not placeholder guidance or API parameter names.
                    if "your_" in low or "example" in low:
                        continue
                    if not rhs.strip().startswith(("\"", "'")):
                        continue
                    val = rhs.strip().strip('"\'')
                    if val and not val.startswith(("$", "{", "<", "os")):
                        results.append({
                            "file": str(f.relative_to(PROJECT_ROOT)),
                            "line": i,
                            "snippet": line.strip()[:80],
                        })
                        break
    return results


# ── 6. Dead Code / Unused Definitions (simple heuristic) ──
def collect_reference_names(files: list[Path]) -> set[str]:
    refs: set[str] = set()
    for f in files:
        tree = parse_file(f)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                refs.add(node.id)
            elif isinstance(node, ast.Attribute):
                refs.add(node.attr)
    return refs


def find_potential_dead_code(files: list[Path]) -> list[dict[str, Any]]:
    """Find public functions with no project-wide name or attribute reference."""
    # CRG: Use project-wide references so public helpers used from other modules are not false positives.
    refs = collect_reference_names(files)
    results = []
    for f in files:
        tree = parse_file(f)
        if not tree:
            continue
        is_alembic_revision = "migrations" in f.parts and f.name.endswith(".py")
        # Only report if file has no obvious external reference pattern
        # Skip dunder and private
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("_"):
                    continue
                if is_alembic_revision and node.name in ("upgrade", "downgrade"):
                    continue
                if node.name not in refs and node.name not in ("main", "lifespan", "now_utc"):
                    results.append({
                        "file": str(f.relative_to(PROJECT_ROOT)),
                        "name": node.name,
                        "kind": "function",
                    })
    return results


# ── 7. Database Migration Check ──
def check_migrations() -> dict[str, Any]:
    mig_dir = PROJECT_ROOT / "packages" / "db" / "migrations"
    if not mig_dir.exists():
        return {"exists": False, "count": 0, "note": "No migrations directory found"}
    migs = list(mig_dir.glob("*.py"))
    return {"exists": True, "count": len(migs), "files": [m.name for m in migs[:5]]}


# ── 8. Test Coverage by Module ──
def check_test_coverage(api_files: list[Path], test_files: list[Path]) -> dict[str, Any]:
    # CRG: __init__.py is package plumbing, not a business module requiring dedicated tests.
    api_mods = {f.stem for f in api_files if f.stem != "__init__"}
    tested_mods = set()
    for tf in test_files:
        text = tf.read_text(encoding="utf-8")
        for mod in api_mods:
            if mod in text:
                tested_mods.add(mod)
    untested = sorted(api_mods - tested_mods)
    return {
        "total_api_modules": len(api_mods),
        "tested_modules": len(tested_mods),
        "untested_modules": untested,
    }


# ── Main Runner ──
def main() -> None:
    api_files = collect_python_files(APPS_API)
    pkg_files = collect_python_files(PACKAGES)
    test_files = collect_python_files(TESTS)
    all_src = api_files + pkg_files

    print("=" * 70)
    print("TubeFactory OCP — Architecture Health Scan Report")
    print("=" * 70)

    # 1. Cycles
    print("\n🔁 1. CIRCULAR IMPORTS")
    graph = build_import_graph(all_src)
    cycles = find_cycles(graph)
    if cycles:
        for c in cycles[:5]:
            print(f"   ⚠️  {' → '.join(c)}")
    else:
        print("   ✅ No circular imports detected")

    # 2. Long functions
    print("\n📏 2. LONG FUNCTIONS (>50 lines)")
    long_funcs = find_long_functions(all_src)
    print(f"   Found {len(long_funcs)} functions exceeding threshold")
    for f in long_funcs[:10]:
        print(f"   ⚠️  {f['file']}::{f['function']} — {f['lines']} lines")

    # 3. Missing types
    print("\n❓ 3. MISSING TYPE ANNOTATIONS")
    missing = find_missing_types(all_src)
    print(f"   Found {len(missing)} functions with missing annotations")
    for m in missing[:8]:
        print(f"   ⚠️  {m['file']}::{m['function']} — {', '.join(m['missing'][:3])}")

    # 4. Bare exceptions
    print("\n🚨 4. BARE / SILENT EXCEPTION HANDLERS")
    bare = find_bare_exceptions(all_src)
    print(f"   Found {len(bare)} handlers")
    for b in bare[:8]:
        print(f"   ⚠️  {b['file']}:{b['line']} — {b['type']}")

    # 5. Secrets
    print("\n🔑 5. POTENTIAL HARDCODED SECRETS")
    secrets = find_hardcoded_secrets(all_src)
    if secrets:
        for s in secrets[:5]:
            print(f"   🚨 {s['file']}:{s['line']} — {s['snippet']}")
    else:
        print("   ✅ None detected")

    # 6. Dead code
    print("\n💀 6. POTENTIALLY UNUSED FUNCTIONS (project-wide)")
    dead = find_potential_dead_code(all_src)
    print(f"   Found {len(dead)} functions with zero project references")
    for d in dead[:8]:
        print(f"   ⚠️  {d['file']}::{d['name']}")

    # 7. Migrations
    print("\n🗃️ 7. DATABASE MIGRATIONS")
    mig = check_migrations()
    if mig["exists"]:
        print(f"   ✅ {mig['count']} migration files")
    else:
        print(f"   🚨 {mig['note']}")

    # 8. Test coverage
    print("\n🧪 8. TEST COVERAGE BY MODULE")
    cov = check_test_coverage(api_files, test_files)
    print(f"   API modules: {cov['total_api_modules']}")
    print(f"   Tested: {cov['tested_modules']}")
    print(f"   Untested: {len(cov['untested_modules'])}")
    if cov["untested_modules"]:
        for m in cov["untested_modules"][:10]:
            print(f"   ⚠️  {m}")

    print("\n" + "=" * 70)
    print("Scan complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
