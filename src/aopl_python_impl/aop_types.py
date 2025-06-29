# aopl_python_impl/aop_types.py

class SymbolicPowerResult:
    """A simple container for an unevaluated power operation."""
    def __init__(self, base, exponent):
        self.base = base       # This will be an AoPValue
        self.exponent = exponent # This will also be an AoPValue

    def __repr__(self):
        return f"SymbolicPowerResult({self.base!r}^{self.exponent!r})"
