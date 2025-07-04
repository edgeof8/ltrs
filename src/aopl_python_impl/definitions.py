# aopl_python_impl/definitions.py

from typing import NamedTuple, List, Dict, Pattern, Optional, Tuple, Union, TYPE_CHECKING
# This is a standard pattern to avoid circular import errors.
# The type checker sees the import, but it's not executed at runtime.
if TYPE_CHECKING:
    from .aop_value import AoPValue

class SymbolicPowerResult:
    def __init__(self, base: Union['AoPValue', 'SymbolicPowerResult'], exponent: Union['AoPValue', 'SymbolicPowerResult']):
        self.base = base
        self.exponent = exponent

    @property
    def ultimate_base_aop_value(self) -> 'AoPValue':
        """Recursively finds the root AoPValue base of the nested power structure."""
        current_base = self.base
        while isinstance(current_base, SymbolicPowerResult):
            current_base = current_base.base
        return current_base

    def __repr__(self):
        return f"SymbolicPowerResult({self.base!r}^{self.exponent!r})"
    def __add__(self, other):
        return NotImplemented
    def __radd__(self, other):
        return NotImplemented
    def __mul__(self, other):
        from .aop_value import AoPValue # Import here for runtime, avoids circular import at top level
        if isinstance(other, SymbolicPowerResult) and self.base == other.base:
            new_exponent = self.exponent + other.exponent
            return SymbolicPowerResult(self.base, new_exponent)
        if isinstance(other, AoPValue) and self.base == other:
            root_aop_base = self.ultimate_base_aop_value
            one = AoPValue.from_number(1, base=root_aop_base._rust_obj.base)
            new_exponent = self.exponent + one
            return SymbolicPowerResult(self.base, new_exponent)
        return NotImplemented
    def __rmul__(self, other):
        return self.__mul__(other)

class Token(NamedTuple):
    kind: str
    value: str
    start: int
    end: int

class AoPError(Exception): pass
