# Qt-free spreadsheet evaluation. Cells are AoP scripts; each result binds $A1, $B2, …
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Tuple
import re

from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.aop_formatter import format_as_decimal_string
from aopl_python_impl.aop_value import AoPValue
from aopl_python_impl.constants import LETTER_TO_EXPONENT_MAP
from aopl_python_impl.gui.graph_logic import pair_display_lines
from aopl_python_impl.gui.script_eval import run_isolated_script_pair

VARIABLE_RE = re.compile(r"\$([a-zA-Z_]\w*)")
ASSIGN_HEAD_RE = re.compile(r"^\s*(\$[a-zA-Z_]\w*)\s*=(?!=)")
ADDR_RE = re.compile(r"^([A-Za-z]+)(\d+)$")
RANGE_RE = re.compile(r"\$([A-Za-z]+\d+)\s*:\s*\$([A-Za-z]+\d+)")

HELP_TEXT = (
    "Cosmic Sheet uses the same AoP language as Cosmic Scratchpad.\n"
    "  Cell results bind as $A1, $B2, … — use those names in other cells.\n"
    "  $name = expr defines a named variable.\n"
    "  Adjacent letters add (ba = 110). Use * to multiply (a*b = c).\n"
    "  A leading = is optional spreadsheet sugar (=$A1+1).\n"
    "  $A1:$C1 sums that rectangle (empty cells count as 0).\n"
    "Commands:\n"
    "  /vars  /base  /setbase <n>  /constants  /letters  /help"
)


@dataclass
class CellSpec:
    expr: str = ""
    output_mode: str = "num"


@dataclass
class CellOut:
    expr: str
    output_mode: str
    primary: str = ""
    secondary: Optional[str] = None
    error: bool = False
    command: bool = False


@dataclass
class SheetResult:
    base: int
    cells: Dict[str, CellOut] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "base": self.base,
            "cells": {
                addr: {
                    "expr": cell.expr,
                    "output_mode": cell.output_mode,
                    "primary": cell.primary,
                    "secondary": cell.secondary,
                    "error": cell.error,
                    "command": cell.command,
                }
                for addr, cell in self.cells.items()
            },
            "variables": self.variables,
        }


def parse_addr(addr: str) -> Tuple[int, int]:
    match = ADDR_RE.match(addr.strip())
    if not match:
        raise ValueError(f"Invalid cell address: {addr!r}")
    col = 0
    for ch in match.group(1).upper():
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1, int(match.group(2)) - 1


def format_addr(col: int, row: int) -> str:
    if col < 0 or row < 0:
        raise ValueError("column and row must be non-negative")
    n = col + 1
    letters = ""
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return f"{letters}{row + 1}"


def normalize_addr(addr: str) -> str:
    col, row = parse_addr(addr)
    return format_addr(col, row)


def _is_cell_var_name(name: str) -> bool:
    inner = name[1:] if name.startswith("$") else name
    try:
        parse_addr(inner)
        return True
    except ValueError:
        return False


def strip_leading_equals(expr: str) -> str:
    stripped = expr.lstrip()
    if stripped.startswith("=") and not stripped.startswith("=="):
        return stripped[1:].lstrip()
    return expr


def canonicalize_cell_vars(expr: str) -> str:
    """Rewrite $a1-style names to canonical $A1 so cell refs are case-insensitive."""

    def repl(match: re.Match) -> str:
        inner = match.group(1)
        try:
            return f"${normalize_addr(inner)}"
        except ValueError:
            return match.group(0)

    return VARIABLE_RE.sub(repl, expr)


def expand_cell_ranges(expr: str, max_cells: int = 1560) -> str:
    """Rewrite $A1:$C2 as ($A1 + $B1 + $C1 + $A2 + $B2 + $C2). Display source is unchanged."""

    def repl(match: re.Match) -> str:
        try:
            c0, r0 = parse_addr(match.group(1))
            c1, r1 = parse_addr(match.group(2))
        except ValueError:
            return match.group(0)
        ca, cb = min(c0, c1), max(c0, c1)
        ra, rb = min(r0, r1), max(r0, r1)
        count = (cb - ca + 1) * (rb - ra + 1)
        if count < 1 or count > max_cells:
            return match.group(0)
        parts = [
            f"${format_addr(col, row)}"
            for row in range(ra, rb + 1)
            for col in range(ca, cb + 1)
        ]
        return "(" + " + ".join(parts) + ")"

    return RANGE_RE.sub(repl, expr)


def _script_for_cell(addr: str, expr: str) -> str:
    lines = [line.strip() for line in expr.split("\n") if line.strip()]
    if not lines:
        return ""
    cell_var = f"${addr}"
    last = lines[-1]
    match = ASSIGN_HEAD_RE.match(last)
    if match and match.group(1) == cell_var:
        return "\n".join(lines)
    lines[-1] = f"{cell_var} = {last}"
    return "\n".join(lines)


def _named_assignments(expr: str) -> List[str]:
    names = []
    for line in expr.split("\n"):
        match = ASSIGN_HEAD_RE.match(line)
        if match:
            names.append(match.group(1))
    return names


def _equality_display(num: str, expr: str) -> Optional[str]:
    if "==" not in expr:
        return None
    if num == "1":
        return "True"
    if num == "0":
        return "False"
    return None


def evaluate_sheet(base: int, cells: Mapping[str, Mapping[str, str]]) -> SheetResult:
    """Evaluate a whole sheet. Empty cells may be omitted."""
    engine = SheetEngine(base=base)
    return engine.evaluate(cells)


class SheetEngine:
    def __init__(self, base: int = 10):
        self.calculator = AoP_Calculator(base=base)
        self.calculator.cache = None

    def evaluate(self, cells: Mapping[str, Mapping[str, str]]) -> SheetResult:
        specs: Dict[str, CellSpec] = {}
        for raw_addr, payload in cells.items():
            try:
                addr = normalize_addr(raw_addr)
            except ValueError:
                continue
            expr = canonicalize_cell_vars(
                strip_leading_equals((payload.get("expr") or "").strip())
            )
            mode = (payload.get("output_mode") or "num").lower()
            if mode not in ("num", "aop"):
                mode = "num"
            if not expr:
                continue
            specs[addr] = CellSpec(expr=expr, output_mode=mode)

        for spec in specs.values():
            if spec.expr.startswith("/"):
                self._apply_setbase(spec.expr)

        result = SheetResult(base=self.calculator.base)
        if not specs:
            return result

        formula_addrs = [addr for addr, spec in specs.items() if not spec.expr.startswith("/")]
        command_addrs = [addr for addr, spec in specs.items() if spec.expr.startswith("/")]

        var_definer, duplicates, reserved_theft = self._collect_definers(specs, formula_addrs)
        deps = self._collect_deps(specs, formula_addrs, var_definer)
        order, cyclic = _topo_order(formula_addrs, deps)

        for addr in cyclic:
            spec = specs[addr]
            result.cells[addr] = CellOut(
                expr=spec.expr,
                output_mode=spec.output_mode,
                primary="Error: Variable dependency cycle.",
                error=True,
            )

        for addr in order:
            spec = specs[addr]
            if addr in reserved_theft:
                result.cells[addr] = CellOut(
                    expr=spec.expr,
                    output_mode=spec.output_mode,
                    primary=reserved_theft[addr],
                    error=True,
                )
                continue
            if addr in duplicates:
                result.cells[addr] = CellOut(
                    expr=spec.expr,
                    output_mode=spec.output_mode,
                    primary=duplicates[addr],
                    error=True,
                )
                continue
            result.cells[addr] = self._eval_formula(addr, spec)

        for addr in command_addrs:
            spec = specs[addr]
            result.cells[addr] = self._eval_command(spec)

        result.variables = self._format_variables()
        return result

    def _apply_setbase(self, expr: str) -> None:
        first = expr.split("\n", 1)[0].strip()
        parts = first.split()
        if len(parts) >= 2 and parts[0].lower() == "/setbase" and parts[1].lstrip("-").isdigit():
            new_base = int(parts[1])
            if new_base >= 2:
                self.calculator.base = new_base

    def _collect_definers(
        self, specs: Dict[str, CellSpec], formula_addrs: Iterable[str]
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        var_definer: Dict[str, str] = {}
        duplicates: Dict[str, str] = {}
        reserved_theft: Dict[str, str] = {}
        for addr in formula_addrs:
            var_definer[f"${addr}"] = addr
        for addr in formula_addrs:
            for name in _named_assignments(specs[addr].expr):
                if _is_cell_var_name(name) and name != f"${addr}":
                    reserved_theft[addr] = f"Error: {name} is reserved for cell {name[1:]}."
                    continue
                owner = var_definer.get(name)
                if owner is not None and owner != addr:
                    duplicates[addr] = f"Error: {name} already defined in {owner}."
                    continue
                var_definer[name] = addr
        return var_definer, duplicates, reserved_theft

    def _collect_deps(
        self,
        specs: Dict[str, CellSpec],
        formula_addrs: Iterable[str],
        var_definer: Mapping[str, str],
    ) -> Dict[str, List[str]]:
        deps: Dict[str, List[str]] = {addr: [] for addr in formula_addrs}
        for addr in formula_addrs:
            seen = set()
            for raw in VARIABLE_RE.findall(expand_cell_ranges(specs[addr].expr)):
                name = f"${raw}"
                source = var_definer.get(name)
                if source and source != addr and source not in seen:
                    seen.add(source)
                    deps[addr].append(source)
        return deps

    def _bind_missing_cell_refs(self, expr: str) -> List[str]:
        added: List[str] = []
        for raw in VARIABLE_RE.findall(expr):
            name = f"${raw}"
            if not _is_cell_var_name(name):
                continue
            if name in self.calculator.variables:
                continue
            self.calculator.variables[name] = AoPValue.from_number(0, self.calculator.base)
            added.append(name)
        return added

    def _eval_formula(self, addr: str, spec: CellSpec) -> CellOut:
        expanded = expand_cell_ranges(spec.expr)
        script = _script_for_cell(addr, expanded)
        fillers = self._bind_missing_cell_refs(script)
        try:
            num, aop = run_isolated_script_pair(self.calculator, script)
        finally:
            for name in fillers:
                if name != f"${addr}":
                    self.calculator.variables.pop(name, None)
        if num.startswith("Error:"):
            cell_var = f"${addr}"
            self.calculator.variables.pop(cell_var, None)
            return CellOut(
                expr=spec.expr,
                output_mode=spec.output_mode,
                primary=num,
                error=True,
            )
        equality = _equality_display(num, spec.expr)
        if equality is not None:
            return CellOut(
                expr=spec.expr,
                output_mode=spec.output_mode,
                primary=equality,
            )
        primary, secondary = pair_display_lines(num, aop, spec.output_mode)
        return CellOut(
            expr=spec.expr,
            output_mode=spec.output_mode,
            primary=primary,
            secondary=secondary,
        )

    def _eval_command(self, spec: CellSpec) -> CellOut:
        first = spec.expr.split("\n", 1)[0].strip()
        parts = first.split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:]
        handlers = {
            "/help": self._cmd_help,
            "/?": self._cmd_help,
            "/vars": self._cmd_vars,
            "/variables": self._cmd_vars,
            "/base": self._cmd_base,
            "/setbase": self._cmd_setbase,
            "/constants": self._cmd_constants,
            "/letters": self._cmd_letters,
            "/aopabet": self._cmd_letters,
            "/clearvars": self._cmd_clearvars,
            "/reset": self._cmd_reset,
        }
        handler = handlers.get(cmd)
        if handler is None:
            text = f"Error: Unknown command '{cmd}'."
            return CellOut(expr=spec.expr, output_mode=spec.output_mode, primary=text, error=True, command=True)
        text = handler(args)
        error = text.startswith("Error:")
        return CellOut(
            expr=spec.expr,
            output_mode=spec.output_mode,
            primary=text,
            error=error,
            command=True,
        )

    def _cmd_help(self, args: List[str]) -> str:
        return HELP_TEXT

    def _cmd_vars(self, args: List[str]) -> str:
        if not self.calculator.variables:
            return "Variables:\n  (none defined)"
        lines = ["Variables:"]
        for name, value in sorted(self.calculator.variables.items()):
            lines.append(f"  {name} = {format_as_decimal_string(value)}")
        return "\n".join(lines)

    def _cmd_base(self, args: List[str]) -> str:
        return f"Current base: {self.calculator.base}"

    def _cmd_setbase(self, args: List[str]) -> str:
        if not args or not args[0].lstrip("-").isdigit():
            return "Error: Usage /setbase <number>"
        new_base = int(args[0])
        if new_base < 2:
            return "Error: Base must be an integer >= 2."
        self.calculator.base = new_base
        return f"Base set to {new_base}."

    def _cmd_constants(self, args: List[str]) -> str:
        return (
            "The engine is an exact integer ring (Z[X]). Named real constants "
            "(#pi, #e, …) are not part of the language."
        )

    def _cmd_letters(self, args: List[str]) -> str:
        lines = ["AoP Letter Mapping (Current Base):"]
        for letter, exp in sorted(LETTER_TO_EXPONENT_MAP.items(), key=lambda item: item[1]):
            lines.append(f"  {letter}: base^{exp}")
        return "\n".join(lines)

    def _cmd_clearvars(self, args: List[str]) -> str:
        kept = {k: v for k, v in self.calculator.variables.items() if _is_cell_var_name(k)}
        self.calculator.variables = kept
        return "Named variables cleared. Cell bindings ($A1, …) kept."

    def _cmd_reset(self, args: List[str]) -> str:
        self.calculator.variables.clear()
        self.calculator.base = 10
        return "Calculator state reset (base 10, variables cleared)."

    def _format_variables(self) -> Dict[str, str]:
        out = {}
        for name, value in sorted(self.calculator.variables.items()):
            try:
                out[name] = format_as_decimal_string(value)
            except Exception:
                out[name] = str(value)
        return out


def _topo_order(addrs: Iterable[str], deps: Mapping[str, List[str]]) -> Tuple[List[str], List[str]]:
    nodes = list(addrs)
    incoming = {addr: 0 for addr in nodes}
    outgoing: Dict[str, List[str]] = {addr: [] for addr in nodes}
    for addr in nodes:
        for source in deps.get(addr, ()):
            if source not in outgoing:
                continue
            outgoing[source].append(addr)
            incoming[addr] += 1
    queue = deque(sorted(addr for addr, count in incoming.items() if count == 0))
    order: List[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(outgoing[node]):
            incoming[child] -= 1
            if incoming[child] == 0:
                queue.append(child)
    leftover = [addr for addr in nodes if addr not in order]
    return order, leftover
