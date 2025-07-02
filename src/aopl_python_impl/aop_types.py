from __future__ import annotations
from typing import TYPE_CHECKING
from .aop_logger import log_pow

if TYPE_CHECKING:
    from .aop_value import AoPValue

class SymbolicPowerResult:
    """A container for a lazy, unevaluated power operation."""
    def __init__(self, base, exponent):
        self.base: 'AoPValue | SymbolicPowerResult' = base
        self.exponent: 'AoPValue | SymbolicPowerResult' = exponent

    def __repr__(self):
        return f"SymbolicPowerResult({self.base!r}^{self.exponent!r})"

    def resolve(self) -> 'AoPValue':
        """
        Eagerly evaluates the symbolic power into a final AoPValue.
        This is the trigger for the actual computation.
        """
        # Recursively resolve the base and exponent first.
        resolved_base = self.base.resolve() if isinstance(self.base, SymbolicPowerResult) else self.base
        resolved_exponent = self.exponent.resolve() if isinstance(self.exponent, SymbolicPowerResult) else self.exponent

        # Now that they are resolved to AoPValues, perform the power operation.
        # The __pow__ method in AoPValue is the eager, intelligent dispatcher.
        return resolved_base ** resolved_exponent
