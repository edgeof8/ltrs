# aopl_python_impl/aop_calculator.py

from typing import Optional, Dict, Any, Callable
from .definitions import ValueTuple, OutputFormatMode, PowerAssociativity
from .aop_parser import parse_and_evaluate
from .aop_formatter import format_output
from .aop_operations import simplify_value

class AoPCalculator:
    def __init__(self, base: int = 10, output_mode: OutputFormatMode = OutputFormatMode.AUTO,
                 precision: int = 10, power_assoc: PowerAssociativity = PowerAssociativity.RIGHT):
        if base < 2:
            raise ValueError("Base must be at least 2")
        if precision < 1:
            raise ValueError("Precision must be at least 1")
        self.base: int = base
        self.output_mode: OutputFormatMode = output_mode
        self.precision: int = precision
        self.power_assoc: PowerAssociativity = power_assoc
        self.letter_cache: Dict[str, ValueTuple] = {}

    def set_base(self, base: int) -> None:
        if base < 2:
            raise ValueError("Base must be at least 2")
        self.base = base
        self.letter_cache.clear()

    def set_output_mode(self, mode: OutputFormatMode) -> None:
        self.output_mode = mode

    def set_precision(self, precision: int) -> None:
        if precision < 1:
            raise ValueError("Precision must be at least 1")
        self.precision = precision

    def set_power_associativity(self, assoc: PowerAssociativity) -> None:
        self.power_assoc = assoc

    def get_letter_value(self, letter: str) -> ValueTuple:
        if letter not in self.letter_cache:
            from .aop_parser import letter_to_value
            self.letter_cache[letter] = letter_to_value(letter, self.base)
        return self.letter_cache[letter]

    def evaluate(self, expression: str) -> ValueTuple:
        return parse_and_evaluate(expression, self.base, self.power_assoc)

    def format_value(self, value: ValueTuple) -> str:
        def get_letter(n: int) -> str:
            if 1 <= n <= 26:
                return chr(ord('a') + n - 1)
            return str(n)

        def represent_exponent(exp_val: Any, base: int, letter_getter: Callable[[int], str]) -> str:
            from .aop_formatter import represent_exponent_as_aop_term
            return represent_exponent_as_aop_term(exp_val, base, letter_getter)

        def normalize(val: ValueTuple) -> ValueTuple:
            return simplify_value(val, self.base)

        return format_output(value, self.base, get_letter, represent_exponent, self.output_mode, normalize, self.precision)

    def evaluate_and_format(self, expression: str) -> str:
        result = self.evaluate(expression)
        return self.format_value(result)

    def clear_cache(self) -> None:
        self.letter_cache.clear()
