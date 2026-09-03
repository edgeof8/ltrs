# aopl_python_impl/__init__.py
#
# Public kernel surface. The GUIs import from submodules; library users can
# `from aopl_python_impl import Calculator, AoPValue, AoPError`.

from .aop_calculator import AoP_Calculator
from .aop_core import evaluate, evaluate_expression
from .aop_value import AoPValue
from .definitions import AoPError

Calculator = AoP_Calculator

__all__ = [
    "AoP_Calculator",
    "Calculator",
    "AoPValue",
    "AoPError",
    "evaluate",
    "evaluate_expression",
]
