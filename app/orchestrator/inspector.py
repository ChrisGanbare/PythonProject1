from __future__ import annotations

import collections.abc
import importlib
import inspect
import json
import re
import typing
from enum import Enum
from pathlib import Path
from typing import Any


def _get_callable_from_path(callable_path: str) -> typing.Callable[..., Any]:
    """Dynamically import a module and retrieve a callable object by its dotted path."""
    if ":" in callable_path:
        module_path, callable_name = callable_path.split(":", 1)
    else:
        parts = callable_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid callable path: {callable_path}")
        module_path, callable_name = parts

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_path}': {e}") from e

    if not hasattr(module, callable_name):
        raise AttributeError(f"Module '{module_path}' has no attribute '{callable_name}'")

    obj = getattr(module, callable_name)
    if not callable(obj):
        raise TypeError(f"Object '{callable_name}' in '{module_path}' is not callable")

    return obj


def _parse_docstring(docstring: str | None) -> dict[str, str]:
    """Parse a docstring to extract parameter descriptions.

    Supports Google-style and reST-style docstrings.
    Returns a dictionary mapping parameter names to descriptions.
    """
    if not docstring:
        return {}

    params = {}
    
    # Simple regex for ":param name: description" (reST style)
    rest_pattern = re.compile(r":param\s+(\w+):\s*(.+)")
    for match in rest_pattern.finditer(docstring):
        params[match.group(1)] = match.group(2).strip()

    # Simple regex for "Args:\n  name (type): description" (Google style)
    # This is a simplification; full parsing is complex.
    lines = docstring.splitlines()
    in_args = False
    for line in lines:
        stripped = line.strip()
        if stripped == "Args:":
            in_args = True
            continue
        if stripped == "Returns:" or stripped == "Raises:":
            in_args = False
            continue
        
        if in_args and ":" in stripped:
            # simple "name: description" or "name (type): description"
            parts = stripped.split(":", 1)
            name_part = parts[0].strip()
            desc = parts[1].strip()
            
            # Remove type info if present e.g. "param (int)"
            if "(" in name_part:
                name_part = name_part.split("(", 1)[0].strip()
            
            params[name_part] = desc

    return params


def inspect_callable(callable_path: str) -> dict[str, Any]:
    """Inspect a callable and return its metadata including parameters."""
    func = _get_callable_from_path(callable_path)
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    param_docs = _parse_docstring(doc)

    parameters = []
    
    type_hints = typing.get_type_hints(func)

    for name, param in sig.parameters.items():
        # resolution of type annotation
        type_annotation = type_hints.get(name, param.annotation)
        
        type_str = "any"
        if type_annotation is not inspect.Parameter.empty:
            if hasattr(type_annotation, "__name__"):
                type_str = type_annotation.__name__
            else:
                type_str = str(type_annotation).replace("typing.", "")

        # Default value handling
        default_val = None
        required = True
        if param.default is not inspect.Parameter.empty:
            default_val = param.default
            required = False
            # creating serializable defaults if possible
            if isinstance(default_val, (Path, Enum)):
                default_val = str(default_val)
        
        # Description
        description = param_docs.get(name, "")

        parameters.append({
            "name": name,
            "type": type_str,
            "default": default_val,
            "required": required,
            "description": description
        })
        
    return {
        "name": func.__name__,
        "description": (doc.split("\n\n")[0] if doc else "").strip(),
        "parameters": parameters,
        "callable_path": callable_path
    }

