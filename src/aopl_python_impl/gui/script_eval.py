# Isolated multi-line evaluation used by the canvas (no Qt).
from __future__ import annotations

from aopl_python_impl.aop_calculator import AoP_Calculator
from aopl_python_impl.definitions import AoPError


def run_isolated_script(calculator: AoP_Calculator, script_string: str, mode: str = "num") -> str:
    """
    Evaluate a multi-line script against a copy of calculator variables.
    Commits variables only if every line succeeds.
    """
    statements = [s.strip() for s in script_string.split("\n") if s.strip()]
    if not statements:
        return ""

    temp_calculator = AoP_Calculator(base=calculator.base, cache_file=calculator.cache_file)
    temp_calculator.cache = None
    temp_calculator.variables = calculator.variables.copy()

    final_result_str = ""
    eval_mode = "num" if mode == "auto" else mode
    for statement_text in statements:
        try:
            result_str, _ = temp_calculator.evaluate_expression(
                expression=statement_text,
                mode=eval_mode,
            )
            final_result_str = result_str
        except AoPError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"

    calculator.variables = temp_calculator.variables
    return final_result_str
