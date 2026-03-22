# -*- coding: utf-8 -*-
"""
Vue template static check (short-term mitigation without build step)

Checks:
  1. [ERR] _xxx() calls in template expressions — Vue 3 treats _ prefix
           as internal helper namespace, causing white screen at runtime.
  2. [WARN] Methods/computed referenced in template but not found in JS
           (best-effort scan; add false positives to IGNORE_METHODS).
  3. [ERR] Empty expression string in v-if / v-show / @click / v-bind.

Usage:
  python tools/check_vue_template.py
  python tools/check_vue_template.py --warn-as-error
Exit codes:
  0 = pass  1 = ERR found  2 = WARN only
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

# Force UTF-8 output so Chinese characters print correctly on Windows GBK console
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except AttributeError:
    pass  # Already wrapped (e.g. under pytest capture)

# ── Config ──────────────────────────────────────────────────────────────────

HTML_FILE = Path(__file__).parent.parent / "static" / "index.html"
JS_FILE   = Path(__file__).parent.parent / "static" / "js" / "dashboard-app.js"

KNOWN_VUE_INTERNALS = {
    "_createVNode", "_openBlock", "_createElementBlock", "_toDisplayString",
    "_renderList", "_withDirectives", "_resolveComponent",
}

IGNORE_METHODS: set[str] = {
    # Vue built-ins
    "$el", "$refs", "$emit", "$nextTick", "$watch", "$event",
    # Common v-for loop variables
    "index", "item", "key", "value", "idx", "row", "col",
    "param", "task", "session", "turn", "tag", "msg", "log", "step",
    "entry", "record", "field", "opt", "option", "group",
    "project", "file", "line", "node", "edge",
    # Project-specific v-for variables in index.html
    "proj", "scene", "phase", "art", "val", "ai", "groupKey",
    # Array/object built-in properties (fallback; already stripped by prop-access removal)
    "length", "push", "pop", "shift", "unshift", "splice",
    # Common attribute/property names
    "name", "type", "label", "title", "icon",
    # CSS class name keys used in :class binding objects
    "show", "active", "collapsed", "disabled", "hidden", "checked",
    # $event shorthand
    "event",
    # Global JS built-ins
    "bootstrap", "console", "parseInt", "parseFloat", "JSON",
    "Object", "Array", "String", "Number", "Boolean", "Math",
    "encodeURIComponent", "decodeURIComponent",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

_COLORS = {
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "green":  "\033[92m",
    "reset":  "\033[0m",
}


def _c(color: str, text: str) -> str:
    return _COLORS.get(color, "") + text + _COLORS["reset"]


def extract_template_expressions(html: str) -> list[tuple[int, str, str]]:
    """Return list of (line_no, directive_name, expression_text) from HTML."""
    results: list[tuple[int, str, str]] = []
    # Strip HTML comments before scanning so we don't match {{ }} inside comments
    html_no_comments = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group()), html, flags=re.DOTALL)
    lines = html_no_comments.splitlines()

    mustache_re = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
    directive_re = re.compile(
        r"""(?:v-if|v-else-if|v-show|v-bind(?::[^\s=>"']+)?|:[^\s=>"'/]+|@[^\s=>"'/]+|v-model(?:\.[a-z]+)*|v-for)\s*=\s*(?:"([^"]*?)"|'([^']*?)')""",
        re.IGNORECASE,
    )

    for lineno, line in enumerate(lines, start=1):
        for m in mustache_re.finditer(line):
            results.append((lineno, "{{ }}", m.group(1).strip()))
        for m in directive_re.finditer(line):
            expr = m.group(1) if m.group(1) is not None else (m.group(2) or "")
            directive = m.group(0).split("=")[0].strip()
            results.append((lineno, directive, expr.strip()))

    return results


def extract_js_identifiers(js: str) -> set[str]:
    """Best-effort extraction of method/computed/data names from JS."""
    names: set[str] = set()
    patterns = [
        re.compile(r"^\s{6,}([\w$]+)\s*\(", re.MULTILINE),
        re.compile(r"^\s{6,}([\w$]+)\s*:", re.MULTILINE),
        re.compile(r"\basync\s+([\w$]+)\s*\(", re.MULTILINE),
    ]
    for pat in patterns:
        for m in pat.finditer(js):
            names.add(m.group(1))
    return names


def collect_called_names(expr: str) -> list[str]:
    """
    Collect root-level identifiers from a template expression.
    Strips string literals and property-access right-hand sides first.
    """
    expr_clean = re.sub(r"'[^']*'|\"[^\"]*\"", '""', expr)
    expr_clean = re.sub(r"\.\w+", "", expr_clean)

    ident_re = re.compile(r"\b([a-zA-Z_$][a-zA-Z0-9_$]*)\b")
    keywords = {
        "if", "else", "for", "in", "of", "return", "true", "false", "null",
        "undefined", "new", "typeof", "instanceof", "void", "delete",
        "let", "const", "var", "function", "class", "this", "super",
        "import", "export", "default", "from", "as", "async", "await",
        "try", "catch", "finally", "throw", "switch", "case", "break",
        "continue", "do", "while", "yield", "String", "Number", "Boolean",
    }
    return [
        m.group(1) for m in ident_re.finditer(expr_clean)
        if m.group(1) not in keywords
    ]


# ── Main check ───────────────────────────────────────────────────────────────

def run_checks(*, warn_as_error: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not HTML_FILE.exists():
        errors.append(f"HTML file not found: {HTML_FILE}")
    if not JS_FILE.exists():
        errors.append(f"JS file not found: {JS_FILE}")
    if errors:
        for e in errors:
            print(_c("red", f"[ERR] {e}"))
        return 1

    html = HTML_FILE.read_text(encoding="utf-8")
    js   = JS_FILE.read_text(encoding="utf-8")

    expressions = extract_template_expressions(html)
    js_names    = extract_js_identifiers(js)

    for lineno, source, expr in expressions:
        if not expr:
            errors.append(
                f"index.html:{lineno}  [{source}] directive has empty expression"
            )
            continue

        called = collect_called_names(expr)

        for name in called:
            # Rule 1: _ prefix
            if name.startswith("_") and name not in KNOWN_VUE_INTERNALS:
                errors.append(
                    f"index.html:{lineno}  [{source}]  \"{expr}\"\n"
                    f"         >>> `{name}` starts with _ -- Vue 3 treats it as an internal "
                    f"helper; component will white-screen. Rename the method."
                )

            # Rule 2: undefined in JS (best-effort)
            if (
                name not in js_names
                and name not in IGNORE_METHODS
                and not name[0].isupper()
                and len(name) > 2
            ):
                warnings.append(
                    f"index.html:{lineno}  [{source}]  \"{expr[:60]}\"\n"
                    f"         >>> `{name}` not found in dashboard-app.js "
                    f"(may be a false positive - add to IGNORE_METHODS if correct)"
                )

    # ── Output ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Vue template check  {HTML_FILE.name} <-> {JS_FILE.name}")
    print(f"{'='*60}")

    if not errors and not warnings:
        print(_c("green", "[OK] All checks passed."))
        print()
        return 0

    for msg in errors:
        print(_c("red", f"\n[ERR]  {msg}"))

    for msg in warnings:
        print(_c("yellow", f"\n[WARN] {msg}"))

    print(f"\n{'-'*60}")
    err_count  = len(errors)
    warn_count = len(warnings)
    summary = f"{err_count} error(s), {warn_count} warning(s)"
    if err_count:
        print(_c("red",    f"[NG] {summary}"))
    else:
        print(_c("yellow", f"[!!] {summary}"))
    print()

    if errors:
        return 1
    if warn_as_error and warn_count:
        return 1
    return 2 if warn_count else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-as-error", action="store_true",
        help="Treat WARN as failure (exit code 1)",
    )
    args = parser.parse_args()
    sys.exit(run_checks(warn_as_error=args.warn_as_error))


if __name__ == "__main__":
    main()