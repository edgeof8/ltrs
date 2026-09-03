# Isolated multi-line evaluation used by the canvas (no Qt).
from __future__ import annotations

from typing import Optional, Tuple

from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.aop_formatter import format_as_aop, format_as_decimal_string
from aopl_python_impl.constants import EXPONENT_TO_LETTER_MAP
from aopl_python_impl.definitions import AoPError


def run_isolated_script(calculator: AoP_Calculator, script_string: str, mode: str = "num") -> str:
    """
    Evaluate a multi-line script against a copy of calculator variables.
    Commits variables only if every line succeeds.
    """
    num, aop = run_isolated_script_pair(calculator, script_string)
    if num.startswith("Error:"):
        return num
    if mode == "aop":
        return aop if aop is not None else num
    return num


def run_isolated_script_pair(
    calculator: AoP_Calculator, script_string: str
) -> Tuple[str, Optional[str]]:
    """Return (num, aop-or-None). On error, aop is None and num starts with Error:."""
    statements = [s.strip() for s in script_string.split("\n") if s.strip()]
    if not statements:
        return "", None

    temp_calculator = AoP_Calculator(base=calculator.base, cache_file=calculator.cache_file)
    temp_calculator.cache = None
    temp_calculator.variables = calculator.variables.copy()

    final_value = None
    for statement_text in statements:
        try:
            value, _ = temp_calculator.evaluate(statement_text)
            if value is not None:
                final_value = value
        except AoPError as e:
            return f"Error: {e}", None
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}", None

    calculator.variables = temp_calculator.variables
    if final_value is None:
        return "", None
    try:
        final_num = format_as_decimal_string(final_value)
        aop = format_as_aop(final_value, EXPONENT_TO_LETTER_MAP)
    except (AoPError, ValueError, OverflowError) as e:
        return f"Error: {e}", None
    if not aop or aop == final_num:
        return final_num, None
    return final_num, aop
